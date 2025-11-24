# sv ARC Room Booking & Display System

A real-time meeting room display and booking system designed for sv ARC, primarily intended for static screens/kiosks to show room availability and usage throughout the organization.

## 🎯 Purpose

This system displays real-time meeting room occupancy and availability, making it easy for staff to:
- See at a glance which rooms are occupied
- Check upcoming meetings for today and the week
- Quickly identify available time slots
- Book rooms directly from the dashboard (optional - Outlook remains preferred)

## 📺 Primary Use Case: Digital Displays

The system is **optimized for display on static screens** such as:
- Lobby/reception area displays
- Meeting room entrance tablets
- Office hallway information screens
- Kiosk stations

Features for static display mode:
- Auto-refresh every 5 minutes
- Clean, high-contrast design readable from distance
- Compact mode for smaller screens
- No interaction required - displays update automatically

## 🔗 Microsoft Office Integration

The system connects to **Microsoft 365 / Office Online** as the authoritative source for meeting data:

- Reads calendar events from Exchange Online via Microsoft Graph API
- Displays real-time room availability from Outlook calendars
- Shows meeting organizers, times, and subjects
- Respects privacy settings (private meetings show as "Bezet")

**Important:** This is a **read and display system** - Microsoft Outlook remains the primary booking method.

## 📋 Features

### For Display/Viewing
- **Real-time dashboard** showing today's meetings across all rooms
- **Weekly calendar view** with 5-day preview
- **Availability grid** showing room status for next 7 days
  - Color-coded: Available (green), Partially booked (orange), Fully booked (red), Closed (grey)
  - Time blocks: Morning (8-12), Afternoon (12-17), Evening (17-22)
- **Automatic refresh** every 5 minutes
- **Room filtering** via URL parameter for single-room displays

### For Interactive Use
- **Quick booking** via clicking available time slots
- **QR code** for mobile booking access
- **Microsoft authentication** for secure access
- **Room and date selection** with dynamic availability
- **Working hours management** for room administrators

### Technical Features
- Server-side session management
- Timezone-aware (Europe/Amsterdam)
- HTML entity handling for special characters
- Event deduplication and cancelled event filtering
- Meeting title caching for performance
- Parallel API calls for fast loading

## 🏢 Available Rooms

- Business Club
- Ruimte: Bestuur & Commissiekamer
- Kantine
- Commissiekamer
- Overleg veld 2

## 🖥️ Technology Stack

**Backend:**
- Python 3.x with Flask
- Microsoft Graph API for Office 365 integration
- Server-side session storage
- OAuth 2.0 authentication

**Frontend:**
- Vanilla JavaScript (no frameworks)
- Responsive CSS with compact mode
- Real-time updates without page reload
- Mobile-optimized booking flow

**Deployment:**
- Linux systemd service
- Nginx reverse proxy
- HTTPS with Let's Encrypt
- SharePoint iframe embedding support

## 📱 Booking Methods

### 1. **Microsoft Outlook** (Recommended)
- Use Outlook desktop, web, or mobile app
- Create meeting and add room as resource
- Full Outlook features: recurring meetings, attachments, invites
- Automatic approval workflow

### 2. **Dashboard Booking** (Quick Option)
- Click available time slot on dashboard
- Login with sv ARC Microsoft account
- Fill in meeting details
- Submit for instant booking

### 3. **QR Code** (Mobile Quick Access)
- Scan QR code on display
- Login on mobile device
- Quick booking form opens automatically

## 🔐 Authentication & Security

- **Microsoft OAuth 2.0** authentication
- Only authorized sv ARC members can book
- Secure session management with encryption
- CORS configured for SharePoint embedding
- HTTPS-only in production

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Microsoft 365 tenant with room mailboxes
- Azure AD app registration with Graph API permissions

### Installation

```bash
# Clone repository
git clone https://github.com/Martijndutch/roommanager.git
cd roommanager

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export REDIRECT_URI="https://yourdomain.com/arcrooms/auth/callback"
export FLASK_SECRET_KEY="your-secret-key"

# Run application
python app.py
```

### Configuration

Create room working hours in `room_working_hours.json`:

```json
{
  "room@svarc.nl": {
    "timeZone": {"name": "W. Europe Standard Time"},
    "timeSlots": [
      {
        "daysOfWeek": ["monday", "tuesday", "wednesday", "thursday", "friday"],
        "startTime": "08:00:00",
        "endTime": "17:00:00"
      }
    ]
  }
}
```

## 📊 Usage Examples

### Display Single Room on Screen
```
https://svarc.100pctwifi.nl/arcrooms/?room=businessclub@svarc.nl
```

### Embed in SharePoint
```html
<iframe src="https://svarc.100pctwifi.nl/arcrooms/" 
        width="100%" height="800px" frameborder="0">
</iframe>
```

### Access Admin Panel
```
https://svarc.100pctwifi.nl/arcrooms/admin
```
(Requires delegate permissions for rooms)

## 🎨 Display Modes

### Normal Mode (1920x1080)
- Full-sized interface for large displays
- Complete information visibility
- Standard font sizes and spacing

### Compact Mode
- Click "Compact" button bottom-right
- Optimized for tablets and smaller screens
- Reduced padding and font sizes
- More content in less space

## 📖 Documentation

- **User Manual:** See `GEBRUIKERSHANDLEIDING.md` (Dutch)
- **Technical Setup:** See inline code documentation
- **API Endpoints:** See `app.py` route definitions

## 🔧 Administration

Room administrators can:
- Set working hours per room
- Configure multiple time blocks per day
- View delegate permissions
- See who can manage each room

Access admin panel at `/arcrooms/admin` (requires authentication and delegate permissions)

## 🤝 Integration Notes

### Outlook Integration
- System reads from Outlook but does **not** write back
- Bookings made via dashboard create events in user's Outlook calendar
- Meeting requests follow standard Outlook approval workflow
- Private meetings are respected and show as "Bezet"

### Microsoft Graph API Permissions Required
- `Calendars.Read` - Read room calendars
- `Calendars.ReadWrite` - Create bookings (user context)
- `Place.Read.All` - List available rooms
- `User.Read` - Get user information

## 🐛 Troubleshooting

**Meetings not showing:**
- Check working hours are configured
- Verify room has correct permissions
- Check timezone settings (Europe/Amsterdam)

**Cannot book room:**
- Ensure logged in with @svarc.nl account
- Check room working hours
- Verify room isn't already booked

**Display not updating:**
- Page auto-refreshes every 5 minutes
- Force refresh: F5 or reload page
- Check internet connectivity

## 📝 License

Internal use for sv ARC only.

## 👤 Author

**Martijn Jongen**  
© 2025 Monsultancy

## 🔗 Links

- **Production:** https://svarc.100pctwifi.nl/arcrooms/
- **Repository:** https://github.com/Martijndutch/roommanager

---

**Note:** While the system allows booking via the dashboard, **Microsoft Outlook remains the recommended and primary method** for creating meetings, especially for recurring meetings, adding multiple attendees, or including additional details like agendas and attachments.
