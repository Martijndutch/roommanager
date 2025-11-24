import json
import requests
from flask import Flask, request, jsonify, render_template, redirect, session, url_for, make_response
from flask_cors import CORS
from flask_session import Session
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os
import re
from html import escape, unescape
from threading import Lock

app = Flask(__name__, static_url_path='/arcrooms/static')

# Configure CORS for SharePoint embedding
CORS(app, resources={
    r"/arcrooms/*": {
        "origins": [
            "https://svarc.sharepoint.com",
            "https://*.sharepoint.com",
            "https://svarc.100pctwifi.nl"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

@app.after_request
def add_security_headers(response):
    """Add security headers to allow iframe embedding in SharePoint"""
    # Allow embedding in SharePoint iframes
    response.headers['X-Frame-Options'] = 'ALLOW-FROM https://svarc.sharepoint.com'
    # For modern browsers, use Content-Security-Policy frame-ancestors
    response.headers['Content-Security-Policy'] = "frame-ancestors 'self' https://*.sharepoint.com https://svarc.100pctwifi.nl"
    # Allow credentials in cross-origin requests
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    # Disable caching for static files to prevent stale JavaScript
    if request.path.startswith('/arcrooms/static/'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# ---- Load secrets from environment variables ----
TENANT = os.getenv('AZURE_TENANT_ID')
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'https://svarc.100pctwifi.nl/arcrooms/auth/callback')
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

# Session configuration - server-side storage to prevent cookie size issues
app.config['SESSION_TYPE'] = 'filesystem'  # Store sessions in filesystem
app.config['SESSION_FILE_DIR'] = '/tmp/flask_sessions'  # Session storage directory
app.config['SESSION_PERMANENT'] = False  # Sessions expire on browser close
app.config['SESSION_USE_SIGNER'] = True  # Sign session cookies
app.config['SESSION_KEY_PREFIX'] = 'arcrooms:'  # Prefix for session keys
app.config['SESSION_COOKIE_SECURE'] = True  # Only send over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # Session expires after 2 hours

# Initialize Flask-Session
Session(app)

# Validate required environment variables
if not all([TENANT, CLIENT_ID, CLIENT_SECRET]):
    raise ValueError("Missing required environment variables: AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET")

TOKEN_URL = f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/token"
AUTH_URL = f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/authorize"
GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"

# Booking rules per room (auto-approve for certain conditions)
ROOM_BOOKING_RULES = {
    "Businessruimte": {"auto_approve": False, "requires_approval": True},
    "Commissiekamer": {"auto_approve": False, "requires_approval": True},
    "Kantine": {"auto_approve": True, "requires_approval": False, "max_duration_hours": 4}
}

# Working hours storage file
WORKING_HOURS_FILE = "room_working_hours.json"

# Meeting title cache: {cache_key: {"title": str, "timestamp": datetime}}
# Cache key format: f"{organizer_email}_{event_start}_{event_end}_{room_name}"
meeting_title_cache = {}
meeting_title_cache_lock = Lock()
CACHE_MAX_AGE_SECONDS = 15 * 60  # 15 minutes

def get_cached_meeting_title(organizer_email, event_start, event_end, room_name):
    """Retrieve meeting title from cache if available and not expired."""
    cache_key = f"{organizer_email}_{event_start}_{event_end}_{room_name}"
    
    with meeting_title_cache_lock:
        if cache_key in meeting_title_cache:
            cached = meeting_title_cache[cache_key]
            age = (datetime.now() - cached["timestamp"]).total_seconds()
            
            if age < CACHE_MAX_AGE_SECONDS:
                print(f"[CACHE HIT] Using cached title for {organizer_email} (age: {age:.1f}s)", flush=True)
                return cached["title"]
            else:
                # Expired, remove from cache
                print(f"[CACHE EXPIRED] Removing expired entry for {organizer_email} (age: {age:.1f}s)", flush=True)
                del meeting_title_cache[cache_key]
    
    return None

def cache_meeting_title(organizer_email, event_start, event_end, room_name, title):
    """Store meeting title in cache."""
    cache_key = f"{organizer_email}_{event_start}_{event_end}_{room_name}"
    
    with meeting_title_cache_lock:
        meeting_title_cache[cache_key] = {
            "title": title,
            "timestamp": datetime.now()
        }
        print(f"[CACHE STORE] Cached title for {organizer_email}", flush=True)

def cleanup_expired_cache():
    """Remove expired entries from cache. Called periodically."""
    with meeting_title_cache_lock:
        now = datetime.now()
        expired_keys = [
            key for key, value in meeting_title_cache.items()
            if (now - value["timestamp"]).total_seconds() >= CACHE_MAX_AGE_SECONDS
        ]
        
        for key in expired_keys:
            del meeting_title_cache[key]
        
        if expired_keys:
            print(f"[CACHE CLEANUP] Removed {len(expired_keys)} expired entries", flush=True)

# ---- Input Validation Functions ----

def validate_string(value, field_name, min_length=1, max_length=255, allow_empty=False):
    """Validate and sanitize string input"""
    if value is None:
        if allow_empty:
            return ""
        raise ValueError(f"{field_name} is required")
    
    # Convert to string and strip whitespace
    value = str(value).strip()
    
    if not allow_empty and not value:
        raise ValueError(f"{field_name} cannot be empty")
    
    if len(value) > max_length:
        raise ValueError(f"{field_name} is too long (max {max_length} characters)")
    
    if len(value) < min_length and not (allow_empty and len(value) == 0):
        raise ValueError(f"{field_name} is too short (min {min_length} characters)")
    
    # Escape HTML to prevent XSS
    return escape(value)

def validate_email(email):
    """Validate email format"""
    if not email:
        raise ValueError("Email is required")
    
    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError("Invalid email format")
    
    if len(email) > 254:  # RFC 5321
        raise ValueError("Email address too long")
    
    return email.lower()

def validate_date(date_str):
    """Validate ISO date format (YYYY-MM-DD)"""
    if not date_str:
        raise ValueError("Date is required")
    
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, date_str):
        raise ValueError("Invalid date format (use YYYY-MM-DD)")
    
    try:
        # Validate it's a real date
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Invalid date value")
    
    return date_str

def validate_time(time_str):
    """Validate time format (HH:MM)"""
    if not time_str:
        raise ValueError("Time is required")
    
    pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
    if not re.match(pattern, time_str):
        raise ValueError("Invalid time format (use HH:MM)")
    
    return time_str

def validate_working_hours(working_hours):
    """Validate working hours JSON structure"""
    if not isinstance(working_hours, dict):
        raise ValueError("Working hours must be a JSON object")
    
    # Check for required fields
    if 'timeSlots' not in working_hours:
        raise ValueError("Missing timeSlots field")
    
    if not isinstance(working_hours['timeSlots'], list):
        raise ValueError("timeSlots must be an array")
    
    # Validate each time slot
    valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    for idx, slot in enumerate(working_hours['timeSlots']):
        if not isinstance(slot, dict):
            raise ValueError(f"Time slot {idx} must be an object")
        
        # Validate daysOfWeek
        if 'daysOfWeek' not in slot or not isinstance(slot['daysOfWeek'], list):
            raise ValueError(f"Time slot {idx} missing valid daysOfWeek array")
        
        for day in slot['daysOfWeek']:
            if day not in valid_days:
                raise ValueError(f"Invalid day: {day}")
        
        # Validate times
        if 'startTime' not in slot or 'endTime' not in slot:
            raise ValueError(f"Time slot {idx} missing startTime or endTime")
        
        # Validate time format (HH:MM:SS or HH:MM)
        # Note: Allow 24:00:00 as valid end time (represents end of day)
        time_pattern_full = r'^(([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]|24:00:00)$'
        time_pattern_short = r'^(([0-1][0-9]|2[0-3]):[0-5][0-9]|24:00)$'
        
        # Normalize times to HH:MM:SS format if they're HH:MM
        if re.match(time_pattern_short, slot['startTime']) and not re.match(time_pattern_full, slot['startTime']):
            slot['startTime'] = slot['startTime'] + ':00'
        if re.match(time_pattern_short, slot['endTime']) and not re.match(time_pattern_full, slot['endTime']):
            slot['endTime'] = slot['endTime'] + ':00'
        
        if not re.match(time_pattern_full, slot['startTime']):
            raise ValueError(f"Invalid startTime format in slot {idx}: {slot['startTime']}")
        if not re.match(time_pattern_full, slot['endTime']):
            raise ValueError(f"Invalid endTime format in slot {idx}: {slot['endTime']}")
    
    return working_hours

def load_working_hours():
    """Load working hours from local file"""
    try:
        with open(WORKING_HOURS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_working_hours_to_file(room_email, working_hours):
    """Save working hours to local file"""
    all_hours = load_working_hours()
    all_hours[room_email] = working_hours
    with open(WORKING_HOURS_FILE, 'w') as f:
        json.dump(all_hours, f, indent=2)





# ---- Get MS Graph token using client credentials ----
def get_token():
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }
    r = requests.post(TOKEN_URL, data=data)
    if r.status_code != 200:
        print(f"Token error: {r.status_code}")
        print(f"Response: {r.text}")
    r.raise_for_status()
    return r.json()["access_token"]


def get_user_token():
    """Get valid user access token, refreshing if expired"""
    access_token = session.get('access_token')
    refresh_token = session.get('refresh_token')
    expires_at_str = session.get('token_expires_at')
    
    if not access_token:
        return None
    
    # Check if token is expired or will expire soon (within 5 minutes)
    if expires_at_str and refresh_token:
        try:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now() >= expires_at - timedelta(minutes=5):
                # Token expired or expiring soon, try to refresh
                try:
                    token_data = {
                        "client_id": CLIENT_ID,
                        "client_secret": CLIENT_SECRET,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token",
                        "scope": "openid profile email User.Read Calendars.ReadWrite offline_access"
                    }
                    
                    token_response = requests.post(TOKEN_URL, data=token_data, timeout=10)
                    if token_response.status_code == 200:
                        tokens = token_response.json()
                        new_access_token = tokens.get("access_token")
                        new_refresh_token = tokens.get("refresh_token", refresh_token)
                        expires_in = tokens.get("expires_in", 3600)
                        
                        # Update session with new tokens
                        new_expires_at = datetime.now() + timedelta(seconds=expires_in)
                        session['access_token'] = new_access_token
                        session['refresh_token'] = new_refresh_token
                        session['token_expires_at'] = new_expires_at.isoformat()
                        
                        return new_access_token
                    else:
                        print(f"Token refresh failed: {token_response.status_code}")
                        print(f"Response: {token_response.text}")
                        # Token refresh failed, return None so user needs to re-login
                        return None
                except Exception as e:
                    print(f"Error refreshing token: {str(e)}")
                    return None
        except Exception as e:
            print(f"Error checking token expiration: {str(e)}")
    
    # Return token even if we can't refresh (will work until it expires)
    return access_token


def get_room_delegates(room_email, token):
    """Get delegates for a room mailbox"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Get mailbox delegates
        url = f"{GRAPH_ENDPOINT}/users/{room_email}/mailboxSettings/delegateMeetingMessageDeliveryOptions"
        delegates_url = f"{GRAPH_ENDPOINT}/users/{room_email}/calendar/calendarPermissions"
        
        r = requests.get(delegates_url, headers=headers)
        if r.status_code == 200:
            permissions = r.json().get("value", [])
            # Filter for delegates with write access
            delegates = []
            for perm in permissions:
                if perm.get("role") in ["write", "owner", "delegate"]:
                    email_addr = perm.get("emailAddress", {})
                    if email_addr.get("address"):
                        delegates.append({
                            "email": email_addr.get("address"),
                            "name": email_addr.get("name", email_addr.get("address")),
                            "role": perm.get("role")
                        })
            return delegates
        return []
    except Exception as e:
        print(f"Error getting delegates for {room_email}: {e}")
        return []


def is_user_delegate(user_email, room_email, token):
    """Check if user is a delegate for the room"""
    delegates = get_room_delegates(room_email, token)
    user_email_lower = user_email.lower()
    return any(d["email"].lower() == user_email_lower for d in delegates)


def check_working_hours(room_email, date_str, start_time, end_time, token):
    """Check if booking time is within working hours for the room (supports multiple time blocks)"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{GRAPH_ENDPOINT}/users/{room_email}/mailboxSettings/workingHours"
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code != 200:
            # No working hours set, allow booking
            return {"allowed": True}
        
        working_hours = r.json()
        time_slots = working_hours.get("timeSlots", [])
        
        if not time_slots:
            # No time slots defined, allow booking
            return {"allowed": True}
        
        # Get day of week from date
        booking_date = datetime.strptime(date_str, "%Y-%m-%d")
        days_map = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_of_week = days_map[booking_date.weekday()]
        
        # Find all time slots for this day
        day_slots = [slot for slot in time_slots if day_of_week in slot.get("daysOfWeek", [])]
        
        if not day_slots:
            return {
                "allowed": False,
                "message": f"Deze ruimte is niet beschikbaar op {['maandag', 'dinsdag', 'woensdag', 'donderdag', 'vrijdag', 'zaterdag', 'zondag'][booking_date.weekday()]}."
            }
        
        # Parse booking times
        booking_start = datetime.strptime(start_time, "%H:%M").time()
        booking_end = datetime.strptime(end_time, "%H:%M").time()
        
        # Check if booking falls within ANY of the time slots
        for slot in day_slots:
            slot_start = datetime.strptime(slot["startTime"], "%H:%M:%S").time()
            slot_end = datetime.strptime(slot["endTime"], "%H:%M:%S").time()
            
            # Check if booking is completely within this slot
            if booking_start >= slot_start and booking_end <= slot_end:
                return {"allowed": True}
        
        # If we get here, booking doesn't fit in any slot
        # Build a friendly message with all available time blocks
        time_blocks = [f"{datetime.strptime(slot['startTime'], '%H:%M:%S').strftime('%H:%M')}-{datetime.strptime(slot['endTime'], '%H:%M:%S').strftime('%H:%M')}" 
                       for slot in day_slots]
        
        return {
            "allowed": False,
            "message": f"Boeking moet binnen werkuren zijn: {', '.join(time_blocks)}"
        }
        
    except Exception as e:
        # On error, allow booking (fail open)
        print(f"Working hours check error: {e}")
        return {"allowed": True}


# ---- Root endpoint ----
@app.get("/arcrooms/")
def index():
    user = session.get('user')
    return render_template('dashboard.html', user=user, session=session)


@app.get("/arcrooms/admin")
def admin_panel():
    user = session.get('user')
    if not user:
        return redirect('/arcrooms/login?redirect=/arcrooms/admin')
    return render_template('admin.html', user=user)


# ---- Login endpoint ----
@app.get("/arcrooms/login")
def login():
    redirect_param = request.args.get('redirect', '')
    state = f"{secrets.token_hex(16)}|{redirect_param}"
    auth_url = f"{AUTH_URL}?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&response_mode=query&scope=openid profile email User.Read Calendars.ReadWrite offline_access&state={state}"
    return redirect(auth_url)


# ---- OAuth callback ----
@app.get("/arcrooms/auth/callback")
def auth_callback():
    code = request.args.get('code')
    state = request.args.get('state', '')
    
    if not code:
        return "Error: No authorization code received", 400
    
    # Check if user is already logged in (code may have been redeemed already)
    if session.get('user') and session.get('access_token'):
        print("User already logged in, skipping token exchange")
        return redirect('/arcrooms/')
    
    # Extract redirect info from state
    redirect_to = ''
    if '|' in state:
        _, redirect_to = state.split('|', 1)
    
    # Exchange code for token
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    token_response = requests.post(TOKEN_URL, data=token_data)
    if token_response.status_code != 200:
        error_detail = token_response.json() if token_response.headers.get('content-type', '').startswith('application/json') else token_response.text
        print(f"Token exchange failed: {token_response.status_code}")
        print(f"Error detail: {error_detail}")
        # If user already logged in, just redirect
        if session.get('user'):
            return redirect('/arcrooms/')
        return f"Error getting token: {error_detail}. Please try logging in again.", 400
    
    tokens = token_response.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")  # May be None if already consented
    expires_in = tokens.get("expires_in", 3600)  # Default 1 hour
    
    # Calculate token expiration time
    expires_at = datetime.now() + timedelta(seconds=expires_in)
    
    # Get user info
    headers = {"Authorization": f"Bearer {access_token}"}
    user_response = requests.get(f"{GRAPH_ENDPOINT}/me", headers=headers)
    
    if user_response.status_code == 200:
        user_data = user_response.json()
        session.permanent = True  # Make session persistent
        session['user'] = {
            'name': user_data.get('displayName'),
            'email': user_data.get('mail') or user_data.get('userPrincipalName'),
            'id': user_data.get('id')
        }
        session['access_token'] = access_token
        if refresh_token:
            session['refresh_token'] = refresh_token
        session['token_expires_at'] = expires_at.isoformat()
        session['login_redirect'] = redirect_to
    
    return redirect('/arcrooms/')


# ---- Logout endpoint ----
@app.get("/arcrooms/logout")
def logout():
    session.clear()
    return redirect('/arcrooms/')


# ---- Clear login redirect flag ----
@app.post("/arcrooms/api/clear-redirect")
def clear_redirect():
    if 'login_redirect' in session:
        del session['login_redirect']
    return jsonify({"success": True})


# ---- API endpoint: get all meetings for dashboard ----
@app.get("/arcrooms/api/meetings")
def get_meetings():
    """
    Get all meetings with PARALLEL loading for better performance
    """
    try:
        token = get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Get all rooms
        rooms_url = f"{GRAPH_ENDPOINT}/places/microsoft.graph.room"
        rooms_r = requests.get(rooms_url, headers=headers, timeout=10)
        rooms_r.raise_for_status()
        
        all_rooms = {}
        for room in rooms_r.json().get("value", []):
            all_rooms[room["id"]] = room
        
        # Get schedules for next 10 days
        start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=10)
        
        def fetch_room_calendar(room_id, room):
            """Fetch calendar for a single room"""
            room_email = room.get("emailAddress")
            if not room_email:
                return []
            
            try:
                calendar_url = f"{GRAPH_ENDPOINT}/users/{room_email}/calendar/calendarView"
                params = {
                    "startDateTime": start.isoformat(),
                    "endDateTime": end.isoformat(),
                    "$select": "id,subject,start,end,showAs,body,organizer,location,isOrganizer,isCancelled,responseStatus,attendees,webLink",
                    "$top": 100
                }
                
                calendar_headers = headers.copy()
                # Request Europe/Amsterdam times - Graph returns local time without Z
                calendar_headers["Prefer"] = 'outlook.timezone="Europe/Amsterdam"'
                
                calendar_r = requests.get(calendar_url, headers=calendar_headers, params=params, timeout=10)
                
                if calendar_r.status_code != 200:
                    return []
                
                events = calendar_r.json().get("value", [])
                room_meetings = []
                
                for event in events:
                    # Skip cancelled events
                    if event.get("isCancelled", False):
                        continue
                    
                    subject = event.get("subject", "")
                    organizer = event.get("organizer", {}).get("emailAddress", {})
                    organizer_name = organizer.get("name", "")
                    organizer_email = organizer.get("address", "")
                    body_content = event.get("body", {}).get("content", "")
                    event_id = event.get("id")
                    is_organizer = event.get("isOrganizer", False)
                    
                    # If subject is hidden, try to get it from organizer's calendar
                    subject_is_hidden = (not subject or subject.strip() == "" or subject.strip() == organizer_name.strip())
                    if subject_is_hidden and not is_organizer and organizer_email:
                        event_start = event.get("start", {}).get("dateTime")
                        event_end = event.get("end", {}).get("dateTime")
                        room_display = room.get("displayName", "")
                        
                        # Check cache first
                        cached_subject = get_cached_meeting_title(organizer_email, event_start, event_end, room_display)
                        if cached_subject:
                            subject = cached_subject
                        else:
                            # Cache miss - fetch from API
                            try:
                                org_calendar_url = f"{GRAPH_ENDPOINT}/users/{organizer_email}/calendar/calendarView"
                                
                                try:
                                    event_dt_str = event_start.split('T')[0] if 'T' in event_start else event_start[:10]
                                    day_start = f"{event_dt_str}T00:00:00.0000000"
                                    day_end = f"{event_dt_str}T23:59:59.9999999"
                                except:
                                    day_start = event_start
                                    day_end = event_end
                                
                                org_params = {
                                    "startDateTime": day_start,
                                    "endDateTime": day_end,
                                    "$select": "id,subject,start,end,location,sensitivity",
                                    "$top": 100
                                }
                                org_headers = headers.copy()
                                org_headers["Prefer"] = 'outlook.timezone="Europe/Amsterdam"'
                                org_response = requests.get(org_calendar_url, headers=org_headers, params=org_params, timeout=5)
                                
                                if org_response.status_code == 200:
                                    org_events = org_response.json().get("value", [])
                                    
                                    for org_event in org_events:
                                        org_start = org_event.get("start", {}).get("dateTime")
                                        org_end = org_event.get("end", {}).get("dateTime")
                                        org_location = org_event.get("location", {})
                                        org_location_name = org_location.get("displayName", "") if isinstance(org_location, dict) else str(org_location)
                                        
                                        time_match = (org_start == event_start and org_end == event_end)
                                        location_match = room_display and room_display.lower() in org_location_name.lower()
                                        
                                        if time_match or location_match:
                                            org_subject = org_event.get("subject", "")
                                            org_sensitivity = org_event.get("sensitivity", "normal")
                                            
                                            if org_subject and org_subject.strip():
                                                if org_sensitivity == "private":
                                                    subject = f"Bezet ({organizer_name})" if organizer_name else "Bezet"
                                                else:
                                                    subject = f"{org_subject} ({organizer_name})" if (organizer_name and organizer_email != room_email) else org_subject
                                                
                                                # Cache the retrieved title
                                                cache_meeting_title(organizer_email, event_start, event_end, room_display, subject)
                                                break
                            except Exception as e:
                                print(f"Could not retrieve subject from organizer {organizer_email}: {str(e)}", flush=True)
                    
                    # Final fallback
                    if not subject or subject.strip() == "" or subject.strip() == organizer_name.strip():
                        subject = f"Bezet ({organizer_name})" if organizer_name else "Privé (onderwerp verborgen)"
                    
                    # Get room resource response status
                    # First check responseStatus (when viewing from room's own calendar)
                    room_response = "none"
                    response_status = event.get("responseStatus", {})
                    if response_status:
                        room_response = response_status.get("response", "none")
                    
                    # If not found in responseStatus, check attendees list
                    if room_response == "none":
                        attendees = event.get("attendees", [])
                        for attendee in attendees:
                            attendee_email = attendee.get("emailAddress", {}).get("address", "").lower()
                            if attendee_email == room_email.lower():
                                room_response = attendee.get("status", {}).get("response", "none")
                                break
                    
                    # Clean up datetime format (remove fractional seconds)
                    start_dt = event.get("start", {}).get("dateTime", "")
                    end_dt = event.get("end", {}).get("dateTime", "")
                    if start_dt:
                        start_dt = start_dt.split('.')[0]  # Remove fractional seconds
                    if end_dt:
                        end_dt = end_dt.split('.')[0]
                    
                    room_meetings.append({
                        "id": event_id,
                        "room": room.get("displayName"),
                        "roomEmail": room_email,
                        "subject": subject,
                        "start": start_dt,
                        "end": end_dt,
                        "status": event.get("showAs", "busy"),
                        "roomResponse": room_response,
                        "organizerEmail": organizer_email,
                        "organizerName": organizer.get("name", ""),
                        "body": body_content,
                        "isOrganizer": is_organizer
                    })
                
                return room_meetings
            except Exception as e:
                print(f"Error processing room {room_email}: {str(e)}", flush=True)
                return []
        
        # Fetch all room calendars in PARALLEL
        all_meetings = []
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            # Submit all tasks
            future_to_room = {
                executor.submit(fetch_room_calendar, room_id, room): (room_id, room)
                for room_id, room in all_rooms.items()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_room):
                room_id, room = future_to_room[future]
                try:
                    meetings = future.result()
                    all_meetings.extend(meetings)
                except Exception as e:
                    print(f"Error fetching calendar for room {room.get('emailAddress')}: {str(e)}", flush=True)
        
        # Cleanup expired cache entries
        cleanup_expired_cache()
        
        # Deduplicate meetings by ID (same event can appear multiple times)
        seen_ids = set()
        unique_meetings = []
        for meeting in all_meetings:
            meeting_id = meeting.get("id")
            if meeting_id and meeting_id not in seen_ids:
                seen_ids.add(meeting_id)
                unique_meetings.append(meeting)
            elif not meeting_id:
                # If no ID, keep it (shouldn't happen but be safe)
                unique_meetings.append(meeting)
        
        return jsonify({"meetings": unique_meetings, "count": len(unique_meetings)})
    except Exception as e:
        print(f"Error in get_meetings: {str(e)}", flush=True)
        return jsonify({"error": str(e), "meetings": []}), 500




# ---- Get room approver/owner ----
def get_room_approver(room_email, token):
    """Get the approver/owner of a room from Outlook"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Try to get calendar permissions/delegates
        delegates_url = f"{GRAPH_ENDPOINT}/users/{room_email}/calendar/calendarPermissions"
        delegates_r = requests.get(delegates_url, headers=headers, timeout=5)
        
        if delegates_r.status_code == 200:
            permissions = delegates_r.json().get("value", [])
            # Find someone with write/owner permissions
            for perm in permissions:
                role = perm.get("role", "")
                if role in ["write", "owner", "delegate"]:
                    email = perm.get("emailAddress", {}).get("address")
                    if email:
                        return email
        
        # Alternative: Try to get the room's owner from the mailbox settings
        mailbox_url = f"{GRAPH_ENDPOINT}/users/{room_email}"
        mailbox_r = requests.get(mailbox_url, headers=headers, timeout=5)
        
        if mailbox_r.status_code == 200:
            mailbox_data = mailbox_r.json()
            # Check for manager or other owner info
            manager_id = mailbox_data.get("manager", {}).get("id")
            if manager_id:
                manager_url = f"{GRAPH_ENDPOINT}/users/{manager_id}"
                manager_r = requests.get(manager_url, headers=headers, timeout=5)
                if manager_r.status_code == 200:
                    return manager_r.json().get("mail") or manager_r.json().get("userPrincipalName")
        
        # Fallback: return a general admin email
        return "admin@svarc.nl"
        
    except Exception as e:
        print(f"Error getting approver for {room_email}: {str(e)}")
        return "admin@svarc.nl"


# ---- API endpoint: request meeting ----
@app.post("/arcrooms/api/request-meeting")
def request_meeting():
    try:
        # Require login
        user = session.get('user')
        user_token = get_user_token()
        
        if not user or not user_token:
            # Clear expired session
            if user and not user_token:
                session.clear()
                return jsonify({"error": "Uw sessie is verlopen. Log opnieuw in om een vergadering te boeken."}), 401
            return jsonify({"error": "Inloggen verplicht. Gebruik 'Inloggen met sv ARC account' knop."}), 401
        
        data = request.json
        if not data:
            return jsonify({"error": "Geen data ontvangen"}), 400
        
        # Validate all inputs
        try:
            room = validate_string(data.get('room'), 'Ruimte', max_length=100)
            # Decode HTML entities (e.g., &amp; -> &)
            room = unescape(room)
            date = validate_date(data.get('date'))
            start_time = validate_time(data.get('startTime'))
            end_time = validate_time(data.get('endTime'))
            subject = validate_string(data.get('subject'), 'Onderwerp', min_length=3, max_length=255)
            notes = validate_string(data.get('notes', ''), 'Opmerking', max_length=1000, allow_empty=True)
        except ValueError as e:
            return jsonify({"error": f"Validatiefout: {str(e)}"}), 400
        
        # Validate time range
        try:
            start_dt = datetime.strptime(start_time, '%H:%M')
            end_dt = datetime.strptime(end_time, '%H:%M')
            if end_dt <= start_dt:
                return jsonify({"error": "Eindtijd moet na starttijd zijn"}), 400
        except ValueError:
            return jsonify({"error": "Ongeldige tijdnotatie"}), 400
        
        # Use logged-in user's info
        requester_name = user.get('name')
        requester_email = user.get('email')
        
        # Get app token for room lookup
        app_token = get_token()
        
        # Find the room email from the rooms API
        headers = {
            "Authorization": f"Bearer {app_token}",
            "Content-Type": "application/json"
        }
        
        rooms_url = f"{GRAPH_ENDPOINT}/places/microsoft.graph.room"
        rooms_r = requests.get(rooms_url, headers=headers, timeout=10)
        
        room_email = None
        if rooms_r.status_code == 200:
            rooms_list = rooms_r.json().get("value", [])
            for r in rooms_list:
                room_name = r.get("displayName", "")
                if room_name.lower() == room.lower():
                    room_email = r.get("emailAddress")
                    break
        
        if not room_email:
            return jsonify({"error": f"Ruimte '{room}' niet gevonden."}), 404
        
        # Check working hours
        working_hours_check = check_working_hours(room_email, date, start_time, end_time, app_token)
        if not working_hours_check["allowed"]:
            return jsonify({"error": working_hours_check["message"]}), 400
        
        # Create calendar event from user's calendar with room as attendee
        # This triggers the room's approval workflow if configured
        event_start = f"{date}T{start_time}:00"
        event_end = f"{date}T{end_time}:00"
        
        calendar_event = {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": f"""
                <p><strong>Ruimte:</strong> {room}</p>
                <p><strong>Aanvrager:</strong> {requester_name} ({requester_email})</p>
                {f'<p><strong>Opmerking:</strong> {notes}</p>' if notes else ''}
                """
            },
            "start": {
                "dateTime": event_start,
                "timeZone": "Europe/Amsterdam"
            },
            "end": {
                "dateTime": event_end,
                "timeZone": "Europe/Amsterdam"
            },
            "location": {
                "displayName": room
            },
            "attendees": [
                {
                    "emailAddress": {
                        "address": room_email,
                        "name": room
                    },
                    "type": "resource"
                }
            ],
            "showAs": "busy"
        }
        
        # Create event in user's calendar using user token (not app token!)
        # This sends a meeting request TO the room, triggering delegate approval
        create_headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }
        create_headers["Prefer"] = 'outlook.timezone="Europe/Amsterdam"'
        
        create_url = f"{GRAPH_ENDPOINT}/me/calendar/events"
        create_response = requests.post(create_url, json=calendar_event, headers=create_headers)
        
        if create_response.status_code not in [200, 201]:
            error_msg = create_response.json().get('error', {}).get('message', 'Onbekende fout')
            return jsonify({"error": f"Fout bij maken afspraak: {error_msg}"}), 500
        
        event_data = create_response.json()
        event_id = event_data.get("id")
        
        # Log the booking
        try:
            with open("meeting_requests.log", "a") as f:
                f.write(f"{datetime.now().isoformat()}|{room}|{date}|{start_time}-{end_time}|{subject}|{requester_name}|{requester_email}|{notes}|{event_id}\n")
        except Exception as log_error:
            print(f"Warning: Could not write to log file: {log_error}")
        
        return jsonify({
            "success": True,
            "message": f"Vergadering succesvol geboekt in {room}",
            "eventId": event_id,
            "room": room,
            "requesterName": requester_name,
            "requesterEmail": requester_email
        })
        
    except Exception as e:
        import traceback
        print(f"Error in request_meeting: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Fout: {str(e)}"}), 500
        
        if not room_email:
            print(f"Room '{room}' not found in available rooms")
            return jsonify({"error": f"Ruimte '{room}' niet gevonden. Probeer opnieuw."}), 404
        
        # Get approver email dynamically from Outlook (use app token)
        approver_email = get_room_approver(room_email, app_token)
        
        # Check booking rules for this room
        room_rules = ROOM_BOOKING_RULES.get(room, {"auto_approve": False, "requires_approval": True})
        auto_approve = room_rules.get("auto_approve", False)
        
        # If user is logged in with svarc.nl account, use their info
        if user and user.get('email', '').endswith('@svarc.nl'):
            # SVARC employees can auto-book certain rooms
            auto_approve = room_rules.get("auto_approve", False)
        
        # Calculate duration
        start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
        duration_hours = (end_dt - start_dt).total_seconds() / 3600
        
        # Check max duration rule
        max_duration = room_rules.get("max_duration_hours")
        if max_duration and duration_hours > max_duration:
            auto_approve = False
        
        # Create calendar event in the room's calendar
        event_start = f"{date}T{start_time}:00"
        event_end = f"{date}T{end_time}:00"
        
        event_status = "busy" if auto_approve else "tentative"
        subject_prefix = "" if auto_approve else "[AANVRAAG] "
        
        calendar_event = {
            "subject": f"{subject_prefix}{subject}",
            "body": {
                "contentType": "HTML",
                "content": f"""
                <p><strong>Status:</strong> {'Goedgekeurd' if auto_approve else 'Wacht op goedkeuring'}</p>
                <p><strong>Aanvrager:</strong> {requester_name} ({requester_email})</p>
                {f'<p><strong>Opmerking:</strong> {notes}</p>' if notes else ''}
                {'<p><em>Automatisch goedgekeurd op basis van boekingsregels</em></p>' if auto_approve else f'<p><em>Deze vergadering is voorlopig gereserveerd en wacht op goedkeuring van {approver_email}</em></p>'}
                """
            },
            "start": {
                "dateTime": event_start,
                "timeZone": "Europe/Amsterdam"
            },
            "end": {
                "dateTime": event_end,
                "timeZone": "Europe/Amsterdam"
            },
            "location": {
                "displayName": room
            },
            "attendees": [
                {
                    "emailAddress": {
                        "address": requester_email,
                        "name": requester_name
                    },
                    "type": "required"
                }
            ],
            "showAs": event_status,
            "responseRequested": not auto_approve,
            "isOnlineMeeting": False
        }
        
        # Create headers with appropriate token
        event_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Create the event - if user is logged in, create in their calendar and room calendar
        # Otherwise, just create in room calendar with app token
        if user_token:
            # Logged in user - create event in user's calendar which will also invite the room
            create_event_url = f"{GRAPH_ENDPOINT}/me/events"
            calendar_event["attendees"].append({
                "emailAddress": {
                    "address": room_email,
                    "name": room
                },
                "type": "resource"
            })
        else:
            # Not logged in - create event in room's calendar using app token
            create_event_url = f"{GRAPH_ENDPOINT}/users/{room_email}/calendar/events"
        
        event_response = requests.post(
            create_event_url, 
            json=calendar_event, 
            headers=event_headers, 
            timeout=10
        )
        
        if event_response.status_code not in [200, 201]:
            print(f"Error creating calendar event: {event_response.status_code} - {event_response.text}")
            return jsonify({"error": "Kon geen voorlopige reservering maken in de agenda"}), 500
        
        event_data = event_response.json()
        event_id = event_data.get("id")
        
        # Send notification email with copy to martijn@monsultancy.eu
        notification_status = "goedgekeurd en bevestigd" if auto_approve else "ontvangen en wacht op goedkeuring"
        
        # Format email body
        # Encode event_id and room for URL safety
        import urllib.parse
        approver_encoded = urllib.parse.quote(approver_email)
        approve_url = f"{REDIRECT_URI.rsplit('/auth/callback', 1)[0]}/api/approve-meeting/{event_id}?room={room_email}&requester={requester_email}&approver={approver_encoded}"
        reject_url = f"{REDIRECT_URI.rsplit('/auth/callback', 1)[0]}/api/reject-meeting/{event_id}?room={room_email}&requester={requester_email}&approver={approver_encoded}"
        cancel_url = f"{REDIRECT_URI.rsplit('/auth/callback', 1)[0]}/api/cancel-meeting/{event_id}?room={room_email}&requester={requester_email}"
        
        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #e30613;">Vergaderruimte Aanvraag - {notification_status.upper()}</h2>
            
            <p><strong>Ruimte:</strong> {room}</p>
            <p><strong>Datum:</strong> {date}</p>
            <p><strong>Tijd:</strong> {start_time} - {end_time}</p>
            <p><strong>Onderwerp:</strong> {subject}</p>
            
            <h3>Aanvrager:</h3>
            <p><strong>Naam:</strong> {requester_name}</p>
            <p><strong>Email:</strong> {requester_email}</p>
            
            {f'<p><strong>Opmerking:</strong> {notes}</p>' if notes else ''}
            
            <hr>
            {'<p style="background: #d4edda; padding: 15px; border-left: 4px solid #28a745;"><strong>✓ Automatisch goedgekeurd</strong><br>Deze reservering is direct bevestigd op basis van de boekingsregels.</p>' if auto_approve else f'''<p style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107;"><strong>⚠️ Wacht op goedkeuring</strong><br>De ruimte is voorlopig gereserveerd (tentative) in de agenda.</p>
            
            <div style="margin: 20px 0; text-align: center;">
                <a href="{approve_url}" style="display: inline-block; background: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 0 10px; font-weight: bold;">✓ Goedkeuren</a>
                <a href="{reject_url}" style="display: inline-block; background: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 0 10px; font-weight: bold;">✗ Afwijzen</a>
            </div>'''}
            
            <hr>
            <p style="font-size: 0.9em; color: #666;">
                <strong>Voor de aanvrager:</strong> Om deze aanvraag te annuleren, <a href="{cancel_url}" style="color: #e30613;">klik hier</a>.
            </p>
            
            <p style="color: #666; font-size: 0.9em;">
                Deze aanvraag is automatisch gegenereerd via het sv ARC vergaderruimte systeem.
            </p>
        </body>
        </html>
        """
        
        # Send email via Microsoft Graph API
        # Build recipient list
        recipients = [
            {
                "emailAddress": {
                    "address": approver_email
                }
            },
            {
                "emailAddress": {
                    "address": "martijn@monsultancy.eu"
                }
            }
        ]
        
        # Add requester to CC if not auto-approved
        cc_recipients = []
        if not auto_approve:
            cc_recipients.append({
                "emailAddress": {
                    "address": requester_email,
                    "name": requester_name
                }
            })
        
        email_message = {
            "message": {
                "subject": f"Vergaderruimte {room} - {notification_status}",
                "body": {
                    "contentType": "HTML",
                    "content": email_body
                },
                "toRecipients": recipients,
                "ccRecipients": cc_recipients,
                "importance": "high" if not auto_approve else "normal"
            },
            "saveToSentItems": True
        }
        
        # Use app token for sending emails
        email_headers = {
            "Authorization": f"Bearer {app_token}",
            "Content-Type": "application/json"
        }
        
        # Try to send email using the room's mailbox
        send_mail_url = f"{GRAPH_ENDPOINT}/users/{room_email}/sendMail"
        email_response = requests.post(
            send_mail_url,
            json=email_message,
            headers=email_headers,
            timeout=10
        )
        
        email_sent = email_response.status_code == 202
        if not email_sent:
            print(f"Warning: Could not send email via {room_email}: {email_response.status_code} - {email_response.text}")
            # Try alternative: send from application (requires Mail.Send permission on app)
            send_mail_url = f"{GRAPH_ENDPOINT}/me/sendMail"
            email_response = requests.post(
                send_mail_url,
                json=email_message,
                headers=email_headers,
                timeout=10
            )
            email_sent = email_response.status_code == 202
            if not email_sent:
                print(f"Warning: Could not send email from app either: {email_response.status_code}")
        
        print(f"Meeting request: {room} on {date} from {requester_name}")
        print(f"Event created with ID: {event_id} - Status: {event_status}")
        print(f"Auto-approved: {auto_approve}")
        print(f"Email sent: {email_sent} to {approver_email} and martijn@monsultancy.eu")
        
        # Store request in a simple log (in production, use a database)
        # Disabled for Azure to avoid file system quota issues
        # with open("meeting_requests.log", "a") as f:
        #     f.write(f"{datetime.now().isoformat()}|{room}|{date}|{start_time}-{end_time}|{subject}|{requester_name}|{requester_email}|{notes}|{event_id}|{auto_approve}|{email_sent}\n")
        
        return jsonify({
            "success": True,
            "message": f"Aanvraag {notification_status}. {'Email verzonden.' if email_sent else 'Let op: email kon niet worden verzonden.'}",
            "approver": approver_email,
            "eventId": event_id,
            "autoApproved": auto_approve,
            "emailSent": email_sent
        })
        
    except Exception as e:
        print(f"Error in request_meeting: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ---- API endpoint: list all rooms in the organization ----
@app.get("/arcrooms/api/rooms")
def list_rooms():
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Get all room lists
    url = f"{GRAPH_ENDPOINT}/places/microsoft.graph.roomlist"
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    
    room_lists = r.json().get("value", [])
    
    # Get all rooms from all room lists
    all_rooms = {}  # Use dict to deduplicate by ID
    for room_list in room_lists:
        room_list_email = room_list.get("emailAddress")
        if room_list_email:
            rooms_url = f"{GRAPH_ENDPOINT}/places/{room_list_email}/microsoft.graph.roomlist/rooms"
            rooms_r = requests.get(rooms_url, headers=headers)
            if rooms_r.status_code == 200:
                rooms = rooms_r.json().get("value", [])
                for room in rooms:
                    all_rooms[room["id"]] = room
    
    # Also get rooms directly (not in a room list)
    direct_rooms_url = f"{GRAPH_ENDPOINT}/places/microsoft.graph.room"
    direct_r = requests.get(direct_rooms_url, headers=headers)
    if direct_r.status_code == 200:
        direct_rooms = direct_r.json().get("value", [])
        for room in direct_rooms:
            all_rooms[room["id"]] = room
    
    # Convert back to list and sort by display name
    rooms_list = sorted(all_rooms.values(), key=lambda x: x.get("displayName", ""))
    
    # Add delegates information for each room
    for room in rooms_list:
        room["delegates"] = get_room_delegates(room.get("emailAddress"), token)
    
    return jsonify({"rooms": rooms_list, "count": len(rooms_list)})


@app.get("/arcrooms/api/working-hours/<room_email>")
def get_working_hours_public(room_email):
    """Get working hours for a specific room (public endpoint)"""
    try:
        all_hours = load_working_hours()
        room_hours = all_hours.get(room_email, {
            "timeZone": {"name": "W. Europe Standard Time"},
            "timeSlots": []
        })
        return jsonify(room_hours), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/arcrooms/api/admin/working-hours/<room_email>")
def get_working_hours(room_email):
    """Get working hours for a specific room from local storage with permission check"""
    try:
        user = session.get('user')
        if not user:
            return jsonify({"error": "Niet ingelogd"}), 401
        
        # Check if user is a delegate for this room
        token = get_token()
        user_email = user.get('preferred_username') or user.get('email') or user.get('userPrincipalName')
        has_access = is_user_delegate(user_email, room_email, token)
        
        all_hours = load_working_hours()
        room_hours = all_hours.get(room_email, {
            "timeZone": {"name": "W. Europe Standard Time"},
            "timeSlots": []
        })
        
        # Add access flag
        room_hours['canEdit'] = has_access
        
        return jsonify(room_hours), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/arcrooms/api/admin/working-hours/<room_email>")
def set_working_hours(room_email):
    """Set working hours for a specific room in local storage"""
    try:
        user = session.get('user')
        if not user:
            return jsonify({"error": "Niet ingelogd"}), 401
        
        # Check if user is a delegate for this room
        token = get_token()
        user_email = user.get('preferred_username') or user.get('email') or user.get('userPrincipalName')
        
        if not is_user_delegate(user_email, room_email, token):
            return jsonify({"error": "Geen toegang. U bent geen gemachtigde voor deze ruimte."}), 403
        
        # Validate input
        try:
            working_hours = validate_working_hours(request.json)
        except ValueError as e:
            print(f"Validation error for {room_email}: {str(e)}", flush=True)
            print(f"Received data: {request.json}", flush=True)
            return jsonify({"error": f"Validatiefout: {str(e)}"}), 400
        
        save_working_hours_to_file(room_email, working_hours)
        
        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"Exception in set_working_hours: {str(e)}", flush=True)
        return jsonify({"error": str(e)}), 500


def delete_blocking_events(room_email, token):
    """Delete all blocking events (niet beschikbaar) from room calendar"""
    from datetime import datetime, timedelta
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Query for existing blocking events (past and future)
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=365)
    end_date = start_date + timedelta(days=730)  # 2 years window
    
    list_url = f"{GRAPH_ENDPOINT}/users/{room_email}/calendar/events"
    params = {
        "$filter": f"start/dateTime ge '{start_date.isoformat()}' and start/dateTime le '{end_date.isoformat()}'",
        "$select": "id,subject,recurrence",
        "$top": 1000
    }
    
    deleted_count = 0
    try:
        response = requests.get(list_url, headers=headers, params=params)
        if response.status_code == 200:
            events = response.json().get("value", [])
            for event in events:
                subject = event.get("subject", "").lower()
                # Delete if it's a "niet beschikbaar" event (with or without 100pctwifi.nl prefix)
                if "niet beschikbaar" in subject:
                    event_id = event.get("id")
                    delete_url = f"{GRAPH_ENDPOINT}/users/{room_email}/calendar/events/{event_id}"
                    del_response = requests.delete(delete_url, headers=headers)
                    if del_response.status_code in [200, 204]:
                        deleted_count += 1
                        print(f"Deleted blocking event: {event.get('subject')} for {room_email}", flush=True)
            print(f"Deleted {deleted_count} blocking events for {room_email}", flush=True)
    except Exception as e:
        print(f"Warning: Failed to delete blocking events: {str(e)}", flush=True)
        raise


# ---- API endpoint: get room schedule ----
@app.get("/arcrooms/api/room")
def room_schedule():
    room_email = request.args.get("email")
    if not room_email:
        return jsonify({"error": "email parameter missing"}), 400
    
    # Validate email format
    try:
        room_email = validate_email(room_email)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Time window (nu → +24u)
    import datetime
    start = datetime.datetime.utcnow()
    end = start + datetime.timedelta(hours=24)

    token = get_token()

    body = {
        "schedules": [room_email],
        "startTime": {
            "dateTime": start.isoformat(),
            "timeZone": "UTC"
        },
        "endTime": {
            "dateTime": end.isoformat(),
            "timeZone": "UTC"
        },
        "availabilityViewInterval": 30
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"{GRAPH_ENDPOINT}/users/{room_email}/calendar/getSchedule"
    r = requests.post(url, json=body, headers=headers)
    r.raise_for_status()

    return jsonify(r.json())


@app.route("/arcrooms/api/approve-meeting/<event_id>", methods=["GET"])
def approve_meeting(event_id):
    """Approve a meeting request - changes from tentative to busy"""
    try:
        token = get_token()
        
        # Get event details first to find the room
        event_url = f"{GRAPH_ENDPOINT}/me/events/{event_id}"
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to get event from approver's perspective (using app token)
        # We need to find which room calendar has this event
        # For now, we'll try common rooms
        room_email = None
        event_data = None
        
        # Extract room from query parameter if provided
        room_email = request.args.get('room')
        requester = request.args.get('requester')
        approver = request.args.get('approver', 'Ruimtebeheerder')
        
        if not room_email:
            return "Room niet gespecificeerd. Gebruik de link uit de email.", 400
        
        # Get the event from room's calendar
        room_event_url = f"{GRAPH_ENDPOINT}/users/{room_email}/calendar/events/{event_id}"
        r = requests.get(room_event_url, headers=headers)
        
        if r.status_code != 200:
            return f"Vergadering niet gevonden in {room_email} agenda (Error {r.status_code})", 404
        
        event_data = r.json()
        
        # Update the event to showAs: busy (approved)
        update_data = {
            "showAs": "busy"
        }
        
        update_r = requests.patch(room_event_url, json=update_data, headers=headers)
        
        if update_r.status_code in [200, 202, 204]:
            # Send confirmation email to requester
            if requester:
                cancel_url = f"{REDIRECT_URI.rsplit('/auth/callback', 1)[0]}/api/cancel-meeting/{event_id}?room={room_email}&requester={requester}"
                start_time = event_data.get('start', {}).get('dateTime', 'N/A')
                end_time = event_data.get('end', {}).get('dateTime', 'N/A')
                
                approval_email = {
                    "message": {
                        "subject": f"✓ Vergaderruimte goedgekeurd - {room_email.split('@')[0]}",
                        "body": {
                            "contentType": "HTML",
                            "content": f"""
                            <html>
                            <body style="font-family: Arial, sans-serif;">
                                <h2 style="color: #e30613;">Vergaderruimte Aanvraag Goedgekeurd</h2>
                                <p style="background: #d4edda; padding: 15px; border-left: 4px solid #28a745;">
                                    <strong>✓ Uw aanvraag is goedgekeurd!</strong><br>
                                    De reservering is bevestigd.
                                </p>
                                
                                <h3>Details:</h3>
                                <p><strong>Ruimte:</strong> {room_email.split('@')[0]}</p>
                                <p><strong>Onderwerp:</strong> {event_data.get('subject', 'N/A')}</p>
                                <p><strong>Start:</strong> {start_time}</p>
                                <p><strong>Eind:</strong> {end_time}</p>
                                
                                <p><strong>Goedgekeurd door:</strong> {approver}</p>
                                
                                <hr>
                                <p style="text-align: center; margin: 20px 0;">
                                    <a href="{cancel_url}" style="display: inline-block; background: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Annuleer deze reservering</a>
                                </p>
                                
                                <p style="color: #666; font-size: 0.9em;">
                                    Deze bevestiging is automatisch gegenereerd via het sv ARC vergaderruimte systeem.
                                </p>
                            </body>
                            </html>
                            """
                        },
                        "toRecipients": [{"emailAddress": {"address": requester}}]
                    },
                    "saveToSentItems": True
                }
                
                try:
                    email_r = requests.post(
                        f"{GRAPH_ENDPOINT}/users/{room_email}/sendMail",
                        json=approval_email,
                        headers=headers
                    )
                    if email_r.status_code not in [200, 202]:
                        # Try fallback
                        requests.post(f"{GRAPH_ENDPOINT}/me/sendMail", json=approval_email, headers=headers)
                except:
                    pass
            
            return f"""
            <html>
            <head><style>
                body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; }}
                .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 8px; border: 2px solid #28a745; }}
                h2 {{ color: #e30613; }}
            </style></head>
            <body>
                <div class="success">
                    <h2>✓ Vergadering Goedgekeurd</h2>
                    <p><strong>Ruimte:</strong> {room_email.split('@')[0]}</p>
                    <p><strong>Onderwerp:</strong> {event_data.get('subject', 'N/A')}</p>
                    <p>De reservering is bevestigd en de aanvrager ({requester}) is op de hoogte gesteld.</p>
                    <p style="margin-top: 20px;"><a href="/">← Terug naar dashboard</a></p>
                </div>
            </body>
            </html>
            """
        else:
            return f"Fout bij goedkeuren: {update_r.status_code} - {update_r.text}", 500
            
    except Exception as e:
        return f"Fout: {str(e)}", 500


@app.route("/arcrooms/api/reject-meeting/<event_id>", methods=["GET"])
def reject_meeting(event_id):
    """Reject a meeting request - deletes the event"""
    try:
        token = get_token()
        room_email = request.args.get('room')
        requester = request.args.get('requester')
        approver = request.args.get('approver', 'Ruimtebeheerder')
        
        if not room_email:
            return "Room niet gespecificeerd", 400
        
        # Get event details before deleting
        headers = {"Authorization": f"Bearer {token}"}
        room_event_url = f"{GRAPH_ENDPOINT}/users/{room_email}/calendar/events/{event_id}"
        r = requests.get(room_event_url, headers=headers)
        
        if r.status_code != 200:
            return f"Vergadering niet gevonden (Error {r.status_code})", 404
        
        event_data = r.json()
        
        # Delete the event
        delete_r = requests.delete(room_event_url, headers=headers)
        
        if delete_r.status_code in [200, 202, 204]:
            # Send notification to requester about rejection
            if requester:
                start_time = event_data.get('start', {}).get('dateTime', 'N/A')
                end_time = event_data.get('end', {}).get('dateTime', 'N/A')
                
                rejection_email = {
                    "message": {
                        "subject": f"✗ Vergaderruimte afgewezen - {room_email.split('@')[0]}",
                        "body": {
                            "contentType": "HTML",
                            "content": f"""
                            <html>
                            <body style="font-family: Arial, sans-serif;">
                                <h2 style="color: #e30613;">Vergaderruimte Aanvraag Afgewezen</h2>
                                <p style="background: #f8d7da; padding: 15px; border-left: 4px solid #dc3545;">
                                    <strong>✗ Uw aanvraag is afgewezen</strong><br>
                                    De reservering is niet goedgekeurd.
                                </p>
                                
                                <h3>Details:</h3>
                                <p><strong>Ruimte:</strong> {room_email.split('@')[0]}</p>
                                <p><strong>Onderwerp:</strong> {event_data.get('subject', 'N/A')}</p>
                                <p><strong>Start:</strong> {start_time}</p>
                                <p><strong>Eind:</strong> {end_time}</p>
                                
                                <p><strong>Afgewezen door:</strong> {approver}</p>
                                
                                <p style="margin-top: 20px;">Neem contact op met de ruimtebeheerder voor meer informatie of probeer een andere tijd/ruimte te reserveren.</p>
                                
                                <p style="color: #666; font-size: 0.9em;">
                                    Deze melding is automatisch gegenereerd via het sv ARC vergaderruimte systeem.
                                </p>
                            </body>
                            </html>
                            """
                        },
                        "toRecipients": [{"emailAddress": {"address": requester}}]
                    },
                    "saveToSentItems": True
                }
                
                # Send notification email
                try:
                    email_r = requests.post(
                        f"{GRAPH_ENDPOINT}/users/{room_email}/sendMail",
                        json=rejection_email,
                        headers=headers
                    )
                    if email_r.status_code not in [200, 202]:
                        requests.post(f"{GRAPH_ENDPOINT}/me/sendMail", json=rejection_email, headers=headers)
                except:
                    pass  # Email sending is optional
            
            return f"""
            <html>
            <head><style>
                body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; }}
                .warning {{ background: #f8d7da; color: #721c24; padding: 20px; border-radius: 8px; border: 2px solid #dc3545; }}
                h2 {{ color: #e30613; }}
            </style></head>
            <body>
                <div class="warning">
                    <h2>✗ Vergadering Afgewezen</h2>
                    <p><strong>Ruimte:</strong> {room_email.split('@')[0]}</p>
                    <p><strong>Onderwerp:</strong> {event_data.get('subject', 'N/A')}</p>
                    <p>De reservering is verwijderd en de aanvrager ({requester}) is op de hoogte gesteld.</p>
                    <p style="margin-top: 20px;"><a href="/">← Terug naar dashboard</a></p>
                </div>
            </body>
            </html>
            """
        else:
            return f"Fout bij afwijzen: {delete_r.status_code} - {delete_r.text}", 500
            
    except Exception as e:
        return f"Fout: {str(e)}", 500


@app.route("/arcrooms/api/cancel-meeting/<event_id>", methods=["GET"])
def cancel_meeting(event_id):
    """Cancel a meeting request by requester - deletes the event"""
    try:
        token = get_token()
        room_email = request.args.get('room')
        requester = request.args.get('requester')
        
        if not room_email:
            return "Room niet gespecificeerd", 400
        
        # Get event details before deleting
        headers = {"Authorization": f"Bearer {token}"}
        room_event_url = f"{GRAPH_ENDPOINT}/users/{room_email}/calendar/events/{event_id}"
        r = requests.get(room_event_url, headers=headers)
        
        if r.status_code != 200:
            return f"Vergadering niet gevonden (Error {r.status_code})", 404
        
        event_data = r.json()
        
        # Delete the event
        delete_r = requests.delete(room_event_url, headers=headers)
        
        if delete_r.status_code in [200, 202, 204]:
            return f"""
            <html>
            <head><style>
                body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; }}
                .info {{ background: #d1ecf1; color: #0c5460; padding: 20px; border-radius: 8px; border: 2px solid #17a2b8; }}
                h2 {{ color: #e30613; }}
            </style></head>
            <body>
                <div class="info">
                    <h2>✓ Vergadering Geannuleerd</h2>
                    <p><strong>Ruimte:</strong> {room_email.split('@')[0]}</p>
                    <p><strong>Onderwerp:</strong> {event_data.get('subject', 'N/A')}</p>
                    <p>Uw reservering is succesvol geannuleerd.</p>
                    <p style="margin-top: 20px;"><a href="/">← Terug naar dashboard</a></p>
                </div>
            </body>
            </html>
            """
        else:
            return f"Fout bij annuleren: {delete_r.status_code} - {delete_r.text}", 500
            
    except Exception as e:
        return f"Fout: {str(e)}", 500


@app.get("/arcrooms/health")
def health():
    """Health check endpoint for monitoring and Azure App Service"""
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})







if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010)
