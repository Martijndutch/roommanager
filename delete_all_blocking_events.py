#!/usr/bin/env python3
"""
Script to delete all blocking events from all room calendars
Run this once to clean up existing "niet beschikbaar" events
"""

import requests
import os
from datetime import datetime, timedelta

# Load environment variables
TENANT = os.getenv('AZURE_TENANT_ID')
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')

TOKEN_URL = f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/token"
GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"

def get_token():
    """Get app token"""
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }
    r = requests.post(TOKEN_URL, data=data)
    r.raise_for_status()
    return r.json()["access_token"]

def get_all_rooms(token):
    """Get all rooms"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    rooms_url = f"{GRAPH_ENDPOINT}/places/microsoft.graph.room"
    response = requests.get(rooms_url, headers=headers)
    response.raise_for_status()
    return response.json().get("value", [])

def delete_blocking_events(room_email, token):
    """Delete all blocking events from a room"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Query for existing blocking events (2 year window)
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=365)
    end_date = start_date + timedelta(days=730)
    
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
                # Delete if it's a "niet beschikbaar" event
                if "niet beschikbaar" in subject:
                    event_id = event.get("id")
                    delete_url = f"{GRAPH_ENDPOINT}/users/{room_email}/calendar/events/{event_id}"
                    del_response = requests.delete(delete_url, headers=headers)
                    if del_response.status_code in [200, 204]:
                        deleted_count += 1
                        print(f"  ✓ Deleted: {event.get('subject')}")
        return deleted_count
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return 0

def main():
    print("=" * 60)
    print("Deleting all blocking events from room calendars")
    print("=" * 60)
    print()
    
    # Load environment from file
    try:
        with open('/etc/arcrooms/secrets.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    except Exception as e:
        print(f"Error loading secrets: {e}")
        print("Make sure to run this script with sudo or as a user with access to /etc/arcrooms/secrets.env")
        return
    
    token = get_token()
    print("✓ Got access token")
    print()
    
    rooms = get_all_rooms(token)
    print(f"Found {len(rooms)} rooms")
    print()
    
    total_deleted = 0
    for room in rooms:
        room_name = room.get("displayName")
        room_email = room.get("emailAddress")
        print(f"Processing: {room_name} ({room_email})")
        deleted = delete_blocking_events(room_email, token)
        total_deleted += deleted
        print(f"  → Deleted {deleted} events")
        print()
    
    print("=" * 60)
    print(f"COMPLETED: Deleted {total_deleted} total blocking events")
    print("=" * 60)

if __name__ == "__main__":
    main()
