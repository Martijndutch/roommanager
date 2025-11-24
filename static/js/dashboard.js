// Timezone-safe helper functions with performance optimization
// Use Intl.DateTimeFormat for fast, reliable timezone conversion (100x faster than toLocaleString)
const timeFormatterAmsterdam = new Intl.DateTimeFormat('nl-NL', {
    timeZone: 'Europe/Amsterdam',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
});

const hourFormatterAmsterdam = new Intl.DateTimeFormat('nl-NL', {
    timeZone: 'Europe/Amsterdam',
    hour: 'numeric',
    hour12: false
});

const minuteFormatterAmsterdam = new Intl.DateTimeFormat('nl-NL', {
    timeZone: 'Europe/Amsterdam',
    minute: 'numeric',
    hour12: false
});

function getAmsterdamTime(isoString) {
    const date = new Date(isoString);
    const parts = timeFormatterAmsterdam.formatToParts(date);
    const hour = Number(parts.find(p => p.type === 'hour').value);
    const minute = Number(parts.find(p => p.type === 'minute').value);
    return { hour, minute };
}

function formatTimeAmsterdam(isoString) {
    return timeFormatterAmsterdam.format(new Date(isoString));
}

// Zoom control via URL parameter only (for kiosk mode)
function setZoom(mode) {
    if (mode === 'compact') {
        document.body.classList.add('compact-mode');
    } else {
        document.body.classList.remove('compact-mode');
    }
}

// Check URL parameter for zoom mode and room filter
const urlParams = new URLSearchParams(window.location.search);
const urlZoom = urlParams.get('zoom');
const filterRoomEmail = urlParams.get('room'); // Filter by room email address

if (urlZoom === 'compact' || urlZoom === '75') {
    setZoom('compact');
}

function updateClock() {
    const now = new Date();
    document.getElementById('clock').textContent = now.toLocaleTimeString('nl-NL', { 
hour: '2-digit', 
minute: '2-digit',
second: '2-digit'
    });
}

setInterval(updateClock, 1000);
updateClock();

let currentBookingData = null;
let allMeetingsData = [];
let allRoomsData = [];
let workingHoursData = {};

// Helper function to decode HTML entities
function decodeHtml(html) {
    const txt = document.createElement('textarea');
    txt.innerHTML = html;
    return txt.value;
}

function openBookingModal(room, date) {
    if (!isLoggedIn) {
        // Store the intended action before redirecting
        sessionStorage.setItem('pendingBooking', JSON.stringify({ room, date: date.toISOString() }));
        // Redirect to login if not logged in
        window.location.href = '/arcrooms/login?redirect=booking';
        return;
    }
    
    // Decode HTML entities in room name (e.g., &amp; -> &)
    room = decodeHtml(room);
    
    currentBookingData = { room, date };
    
    // Populate room dropdown
    const roomSelect = document.getElementById('modalRoom');
    roomSelect.innerHTML = '<option value="">-- Selecteer ruimte --</option>';
    allRoomsData.forEach(r => {
        const option = document.createElement('option');
        option.value = r.displayName;
        option.textContent = r.displayName;
        if (r.displayName === room) {
            option.selected = true;
        }
        roomSelect.appendChild(option);
    });
    
    // Populate date dropdown with next 14 days
    const dateSelect = document.getElementById('modalDate');
    dateSelect.innerHTML = '<option value="">-- Selecteer datum --</option>';
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    for (let i = 0; i < 14; i++) {
        const d = new Date(today);
        d.setDate(today.getDate() + i);
        const option = document.createElement('option');
        // Use local date string (YYYY-MM-DD) instead of ISO to avoid timezone issues
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const dateStr = `${year}-${month}-${day}`;
        option.value = dateStr;
        option.textContent = d.toLocaleDateString('nl-NL', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
        // Compare with passed date
        const passedDateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
        if (dateStr === passedDateStr) {
            option.selected = true;
        }
        dateSelect.appendChild(option);
    }
    
    // Function to update time slots based on current room and date selection
    const updateTimeSlots = () => {
        const selectedRoom = roomSelect.value;
        const selectedDateStr = dateSelect.value;
        
        if (selectedRoom && selectedDateStr) {
            currentBookingData.room = selectedRoom;
            currentBookingData.date = new Date(selectedDateStr + 'T12:00:00');
            
            const roomMeetings = allMeetingsData.filter(m => 
                m.room === selectedRoom && 
                getDateKey(m.start) === selectedDateStr
            );
            populateTimeSlots(roomMeetings);
        }
    };
    
    // Add event listeners to update time slots when room or date changes
    roomSelect.onchange = updateTimeSlots;
    dateSelect.onchange = updateTimeSlots;
    
    // Initial population of time slots
    const dateKey = date.toISOString().split('T')[0];
    const roomMeetings = allMeetingsData.filter(m => 
        m.room === room && 
        getDateKey(m.start) === dateKey
    );
    
    // Generate available time slots
    populateTimeSlots(roomMeetings);
    
    document.getElementById('bookingModal').classList.add('show');
    document.getElementById('successMessage').style.display = 'none';
    document.getElementById('errorMessage').style.display = 'none';
}

// Auto-open modal if user just logged in with booking redirect or has pending booking
if (isLoggedIn && (loginRedirect || sessionStorage.getItem('pendingBooking'))) {
    const pending = sessionStorage.getItem('pendingBooking');
    if (pending) {
        try {
            const { room, date } = JSON.parse(pending);
            sessionStorage.removeItem('pendingBooking');
            // Wait for data to load first
            setTimeout(() => {
                openBookingModal(room, new Date(date));
            }, 1000);
        } catch (e) {
            console.error('Failed to restore pending booking:', e);
        }
    } else if (loginRedirect) {
        // User just logged in via QR code - open booking modal with first room and today's date
        setTimeout(async () => {
            // Wait for rooms to load
            while (allRoomsData.length === 0) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            // Open booking modal with first room and today
            if (allRoomsData.length > 0) {
                const firstRoom = allRoomsData[0].displayName;
                openBookingModal(firstRoom, new Date());
            }
        }, 500);
    }
    // Clear the redirect flag
    fetch('/arcrooms/api/clear-redirect', { method: 'POST' });
}

function populateTimeSlots(existingMeetings) {
    const startSelect = document.getElementById('startTime');
    const endSelect = document.getElementById('endTime');
    
    // Clear existing options
    startSelect.innerHTML = '<option value="">-- Selecteer starttijd --</option>';
    endSelect.innerHTML = '<option value="">-- Selecteer eindtijd --</option>';
    
    // Get working hours for the selected room
    const room = currentBookingData.room;
    const roomData = allRoomsData.find(r => r.displayName === room);
    const workingHours = roomData ? workingHoursData[roomData.emailAddress] : null;
    const date = currentBookingData.date;
    const dayOfWeek = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'][date.getDay()];
    
    // Generate time slots from 7:00 to 22:00 in 30 minute intervals
    const slots = [];
    for (let hour = 7; hour <= 22; hour++) {
        for (let minute of [0, 30]) {
            if (hour === 22 && minute === 30) break; // Stop at 22:00
            const time = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
            slots.push(time);
        }
    }
    
    // Check which slots are available
    const availableSlots = slots.filter(slot => {
        const slotTime = new Date(`2000-01-01T${slot}:00`);
        
        // Check working hours
        if (workingHours && workingHours.timeSlots && workingHours.timeSlots.length > 0) {
            const daySlots = workingHours.timeSlots.filter(ts => ts.daysOfWeek && ts.daysOfWeek.includes(dayOfWeek));
            
            if (daySlots.length === 0) {
                return false; // No working hours for this day
            }
            
            // Check if slot falls within any working hour block
            const inWorkingHours = daySlots.some(ts => {
                const [startH, startM] = ts.startTime.split(':').map(Number);
                const [endH, endM] = ts.endTime.split(':').map(Number);
                const startMinutes = startH * 60 + startM;
                const endMinutes = endH * 60 + endM;
                const slotMinutes = slotTime.getHours() * 60 + slotTime.getMinutes();
                return slotMinutes >= startMinutes && slotMinutes < endMinutes;
            });
            
            if (!inWorkingHours) {
                return false; // Outside working hours
            }
        }
        
        // Check if this slot overlaps with any existing meeting
        for (let meeting of existingMeetings) {
            // Backend sends UTC, extract Amsterdam time
            const { hour: meetingStartHours, minute: meetingStartMinutes } = getAmsterdamTime(meeting.start);
            const { hour: meetingEndHours, minute: meetingEndMinutes } = getAmsterdamTime(meeting.end);
            
            // Create time-only dates for comparison (same date, different times)
            const meetingStartTime = new Date(`2000-01-01T${meetingStartHours.toString().padStart(2, '0')}:${meetingStartMinutes.toString().padStart(2, '0')}:00`);
            const meetingEndTime = new Date(`2000-01-01T${meetingEndHours.toString().padStart(2, '0')}:${meetingEndMinutes.toString().padStart(2, '0')}:00`);
            
            // A slot is occupied if it starts within a meeting's time range
            // (slotTime >= meetingStartTime && slotTime < meetingEndTime)
            if (slotTime >= meetingStartTime && slotTime < meetingEndTime) {
                console.log(`Slot ${slot} blocked by meeting: ${meeting.subject} (${meetingStartHours}:${meetingStartMinutes.toString().padStart(2, '0')} - ${meetingEndHours}:${meetingEndMinutes.toString().padStart(2, '0')})`);
                return false; // Slot is occupied
            }
        }
        return true;
    });
    
    console.log('Available start time slots:', availableSlots);
    
    // Populate start time options
    availableSlots.forEach(slot => {
        const option = document.createElement('option');
        option.value = slot;
        option.textContent = slot;
        startSelect.appendChild(option);
    });
}

// Setup end time population once (prevent event listener leak)
function setupEndTimeHandler() {
    const startSelect = document.getElementById('startTime');
    const endSelect = document.getElementById('endTime');
    
    // Single event handler - no memory leaks
    startSelect.addEventListener('change', function updateEndTimes() {
        const startTime = this.value;
        if (!startTime) {
            endSelect.innerHTML = '<option value="">-- Selecteer eindtijd --</option>';
            return;
        }
        
        endSelect.innerHTML = '<option value="">-- Selecteer eindtijd --</option>';
        
        // Get working hours and existing meetings from current booking context
        if (!currentBookingData) return;
        
        const room = currentBookingData.room;
        const roomData = allRoomsData.find(r => r.displayName === room);
        const workingHours = roomData ? workingHoursData[roomData.emailAddress] : null;
        const date = currentBookingData.date;
        const dayOfWeek = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'][date.getDay()];
        
        // Get existing meetings for this room and date
        const dateKey = date.toISOString().split('T')[0];
        const existingMeetings = allMeetingsData.filter(m => 
            m.room === room && 
            getDateKey(m.start) === dateKey
        );
        
        // Generate time slots
        const slots = [];
        for (let hour = 7; hour <= 22; hour++) {
            for (let minute of [0, 30]) {
                if (hour === 22 && minute === 30) break;
                const time = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
                slots.push(time);
            }
        }
        
        const startIndex = slots.indexOf(startTime);
        const startTimeDate = new Date(`2000-01-01T${startTime}:00`);
        const startMinutes = startTimeDate.getHours() * 60 + startTimeDate.getMinutes();
        
        // Find which working hours block contains the start time
        let workingHoursEndMinutes = 22 * 60;
        if (workingHours && workingHours.timeSlots && workingHours.timeSlots.length > 0) {
            const daySlots = workingHours.timeSlots.filter(ts => ts.daysOfWeek && ts.daysOfWeek.includes(dayOfWeek));
            
            for (const ts of daySlots) {
                const [startH, startM] = ts.startTime.split(':').map(Number);
                const [endH, endM] = ts.endTime.split(':').map(Number);
                const blockStartMinutes = startH * 60 + startM;
                const blockEndMinutes = endH * 60 + endM;
                
                if (startMinutes >= blockStartMinutes && startMinutes < blockEndMinutes) {
                    workingHoursEndMinutes = blockEndMinutes;
                    break;
                }
            }
        }
        
        // Find available end times
        for (let i = startIndex + 1; i < slots.length; i++) {
            const endSlot = slots[i];
            const endTime = new Date(`2000-01-01T${endSlot}:00`);
            const endMinutes = endTime.getHours() * 60 + endTime.getMinutes();
            
            if (endMinutes > workingHoursEndMinutes) {
                break;
            }
            
            // Check if range is available
            let rangeAvailable = true;
            for (let meeting of existingMeetings) {
                const { hour: meetingStartHours, minute: meetingStartMinutes } = getAmsterdamTime(meeting.start);
                const { hour: meetingEndHours, minute: meetingEndMinutes } = getAmsterdamTime(meeting.end);
                
                const meetingStartTime = new Date(`2000-01-01T${meetingStartHours.toString().padStart(2, '0')}:${meetingStartMinutes.toString().padStart(2, '0')}:00`);
                const meetingEndTime = new Date(`2000-01-01T${meetingEndHours.toString().padStart(2, '0')}:${meetingEndMinutes.toString().padStart(2, '0')}:00`);
                
                if (!(endTime <= meetingStartTime || startTimeDate >= meetingEndTime)) {
                    rangeAvailable = false;
                    break;
                }
            }
            
            if (rangeAvailable) {
                const option = document.createElement('option');
                option.value = endSlot;
                option.textContent = endSlot;
                endSelect.appendChild(option);
            } else {
                break;
            }
        }
    });
}

// Initialize end time handler once
setupEndTimeHandler();

function closeModal() {
    document.getElementById('bookingModal').classList.remove('show');
    document.getElementById('bookingForm').reset();
}

document.getElementById('bookingForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Get the current selected room from dropdown to ensure it's not HTML-encoded
    const selectedRoom = document.getElementById('modalRoom').value;
    const selectedDate = document.getElementById('modalDate').value;
    
    const formData = {
        room: selectedRoom,
        date: selectedDate,
        startTime: document.getElementById('startTime').value,
        endTime: document.getElementById('endTime').value,
        subject: document.getElementById('subject').value,
        notes: document.getElementById('notes').value
    };

    try {
        const response = await fetch('/arcrooms/api/request-meeting', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (response.ok) {
            document.getElementById('successMessage').textContent = 'Vergadering succesvol geboekt!';
            document.getElementById('successMessage').style.display = 'block';
            document.getElementById('bookingForm').reset();
            setTimeout(() => {
                closeModal();
                loadMeetings(); // Refresh the meetings list
            }, 2000);
        } else {
            // Check if session expired (401)
            if (response.status === 401) {
                document.getElementById('errorMessage').textContent = result.error || 'Uw sessie is verlopen. U wordt doorgestuurd naar de inlogpagina...';
                document.getElementById('errorMessage').style.display = 'block';
                
                // Store pending booking and redirect to login after 2 seconds
                sessionStorage.setItem('pendingBooking', JSON.stringify(formData));
                setTimeout(() => {
                    window.location.href = '/arcrooms/login?redirect=book';
                }, 2000);
            } else {
                document.getElementById('errorMessage').textContent = 'Fout: ' + (result.error || 'Onbekende fout');
                document.getElementById('errorMessage').style.display = 'block';
            }
        }
    } catch (error) {
        document.getElementById('errorMessage').textContent = 'Fout bij boeken: ' + error.message;
        document.getElementById('errorMessage').style.display = 'block';
    }
});

function formatTime(dateStr) {
    return formatTimeAmsterdam(dateStr);
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('nl-NL', options);
}

function isToday(dateStr) {
    const date = new Date(dateStr);
    const today = new Date();
    return date.toDateString() === today.toDateString();
}

function getDateKey(dateStr) {
    const date = new Date(dateStr);
    return date.toISOString().split('T')[0];
}

async function loadRoomsData() {
    try {
        const response = await fetch('/arcrooms/api/rooms');
        const data = await response.json();
        let rooms = data.rooms || [];
        
        // Filter by room email if specified in URL
        if (filterRoomEmail) {
            rooms = rooms.filter(room => room.emailAddress.toLowerCase() === filterRoomEmail.toLowerCase());
            
            // Show filter indicator
            if (rooms.length > 0) {
                const filterDiv = document.getElementById('roomFilter');
                filterDiv.textContent = `🔍 Filter actief: ${rooms[0].displayName}`;
                filterDiv.style.display = 'block';
            }
        }
        
        allRoomsData = rooms;
        
        // Load working hours for all rooms in PARALLEL
        const workingHoursPromises = allRoomsData.map(async (room) => {
            try {
                const whResponse = await fetch(`/arcrooms/api/working-hours/${encodeURIComponent(room.emailAddress)}`);
                if (whResponse.ok) {
                    workingHoursData[room.emailAddress] = await whResponse.json();
                } else {
                    console.log(`No working hours for ${room.displayName}`);
                    workingHoursData[room.emailAddress] = null;
                }
            } catch (error) {
                console.log(`Error loading working hours for ${room.displayName}:`, error);
                workingHoursData[room.emailAddress] = null;
            }
        });
        
        // Wait for all working hours to load
        await Promise.all(workingHoursPromises);
    } catch (error) {
        console.error('Error loading rooms data:', error);
    }
}

async function loadMeetings() {
    try {
        const response = await fetch('/arcrooms/api/meetings');
        const data = await response.json();
        let meetings = data.meetings;
        
        // Filter meetings by room if specified in URL
        if (filterRoomEmail) {
            const filteredRoomNames = allRoomsData.map(r => r.displayName);
            meetings = meetings.filter(m => filteredRoomNames.includes(m.room));
        }
        
        // Store all meetings for use
        allMeetingsData = meetings;

        // Huidige datum
        document.getElementById('currentDate').textContent = formatDate(new Date());

        // Vergaderingen van vandaag
        const todayMeetings = meetings.filter(m => isToday(m.start));
        const todayContainer = document.getElementById('todayMeetings');
        
        if (todayMeetings.length === 0) {
            todayContainer.innerHTML = '<div class="no-meetings">Geen vergaderingen gepland voor vandaag</div>';
        } else {
            todayMeetings.sort((a, b) => new Date(a.start) - new Date(b.start));
            todayContainer.innerHTML = todayMeetings.map(meeting => {
                // Only show pending status if room is NOT the organizer (invited meetings only)
                const isPending = !meeting.isOrganizer && (meeting.roomResponse === 'none' || meeting.roomResponse === 'tentativelyAccepted');
                const statusText = isPending ? ' (wacht op goedkeuring)' : '';
                return `
                <div class="meeting" onclick="window.open('https://outlook.office365.com/calendar/item/${encodeURIComponent(meeting.id)}', 'outlook', 'width=1000,height=800,scrollbars=yes,resizable=yes')" style="cursor: pointer;">
                    <div class="meeting-time">${formatTime(meeting.start)} - ${formatTime(meeting.end)}</div>
                    <div class="meeting-title">${meeting.subject}</div>
                    <div class="meeting-location">📍 ${meeting.room}${statusText}</div>
                </div>
            `}).join('');
        }

        // Komende 5 dagen kalender
        const weekContainer = document.getElementById('weekCalendar');
        const dayGroups = {};
        
        // Initialiseer komende 5 dagen
        for (let i = 0; i < 5; i++) {
            const date = new Date();
            date.setDate(date.getDate() + i);
            const key = date.toISOString().split('T')[0];
            dayGroups[key] = {
                date: date,
                meetings: []
            };
        }

        // Groepeer vergaderingen per dag
        meetings.forEach(meeting => {
            const key = getDateKey(meeting.start);
            if (dayGroups[key]) {
                dayGroups[key].meetings.push(meeting);
            }
        });

        // Render kalender
        weekContainer.innerHTML = Object.values(dayGroups).map(day => {
            const dayMeetings = day.meetings.sort((a, b) => new Date(a.start) - new Date(b.start));
            return `
                <div class="day-card">
                    <div class="day-header">${day.date.toLocaleDateString('nl-NL', { weekday: 'long' })}</div>
                    <div class="day-date">${day.date.toLocaleDateString('nl-NL', { day: 'numeric', month: 'long' })}</div>
                    ${dayMeetings.length === 0 ? '<div style="text-align: center; color: #ccc; font-size: 0.9em; padding: 20px;">Geen vergaderingen</div>' : 
                        dayMeetings.map(m => {
                            // Only show pending status if room is NOT the organizer (invited meetings only)
                            const isPending = !m.isOrganizer && (m.roomResponse === 'none' || m.roomResponse === 'tentativelyAccepted');
                            const statusText = isPending ? ' (wacht op goedkeuring)' : '';
                            return `
                            <div class="mini-meeting" onclick="window.open('https://outlook.office365.com/calendar/item/${encodeURIComponent(m.id)}', 'outlook', 'width=1000,height=800,scrollbars=yes,resizable=yes')" style="cursor: pointer;">
                                <div class="mini-meeting-time">${formatTime(m.start)} - ${formatTime(m.end)}</div>
                                <div class="mini-meeting-title">${m.subject}</div>
                                <div class="mini-meeting-room">${m.room}${statusText}</div>
                            </div>
                        `}).join('')
                    }
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error('Fout bij laden vergaderingen:', error);
        document.getElementById('todayMeetings').innerHTML = '<div class="no-meetings">Fout bij laden van vergaderingen</div>';
    }
}

function renderAvailabilityGrid(meetings) {
    const availabilityContainer = document.getElementById('availabilityGrid');
    
    // Get all defined rooms from ROOM_BOOKING_RULES or from meetings
    const allRooms = new Set();
    
    // Add rooms from meetings
    meetings.forEach(m => allRooms.add(m.room));
    
    // Add predefined rooms from allRoomsData
    allRoomsData.forEach(room => {
        allRooms.add(room.displayName);
    });
    
    // Now render with all rooms
    const rooms = Array.from(allRooms).sort();
    renderGrid(rooms, meetings);
}

function renderGrid(rooms, meetings) {
    const availabilityContainer = document.getElementById('availabilityGrid');
    
    // Create 7 days
    const days = [];
    for (let i = 0; i < 7; i++) {
        const date = new Date();
        date.setDate(date.getDate() + i);
        days.push(date);
    }
    
    // Calculate availability for each room per day
    const availability = {};
    rooms.forEach(room => {
        availability[room] = {};
        days.forEach(day => {
            const dayKey = day.toISOString().split('T')[0];
            const dayMeetings = meetings.filter(m => 
                m.room === room && 
                getDateKey(m.start) === dayKey
            );
            
            // Calculate total meeting hours
            let totalHours = 0;
            dayMeetings.forEach(m => {
                const start = new Date(m.start);
                const end = new Date(m.end);
                totalHours += (end - start) / (1000 * 60 * 60);
            });
            
            // Classify: free (0h), partial (< 4h), busy (>= 4h)
            if (totalHours === 0) {
                availability[room][dayKey] = { status: 'free', count: 0 };
            } else if (totalHours < 4) {
                availability[room][dayKey] = { status: 'partial', count: dayMeetings.length };
            } else {
                availability[room][dayKey] = { status: 'busy', count: dayMeetings.length };
            }
        });
    });
    
    // Build grid HTML
    let html = '<div class="availability-grid">';
    
    // Header row
    html += '<div class="availability-header"></div>';
    days.forEach(day => {
        html += `<div class="availability-header">${day.toLocaleDateString('nl-NL', { weekday: 'short' })}<br>${day.getDate()}/${day.getMonth() + 1}</div>`;
    });
    
    // Room rows
    rooms.forEach(room => {
        html += `<div class="availability-room">${room}</div>`;
        days.forEach(day => {
            const dayKey = day.toISOString().split('T')[0];
            const avail = availability[room][dayKey];
            
            // Get meetings for this room/day categorized by time
            const dayMeetings = allMeetingsData.filter(m => 
                m.room === room && 
                getDateKey(m.start) === dayKey
            );
            
            const morning = dayMeetings.filter(m => {
                const { hour } = getAmsterdamTime(m.start);
                return hour >= 0 && hour < 12;
            }).length;
            
            const afternoon = dayMeetings.filter(m => {
                const { hour } = getAmsterdamTime(m.start);
                return hour >= 12 && hour < 18;
            }).length;
            
            const evening = dayMeetings.filter(m => {
                const { hour } = getAmsterdamTime(m.start);
                return hour >= 18;
            }).length;
            
            // Check working hours for this day and room
            const roomData = allRoomsData.find(r => r.displayName === room);
            const workingHours = roomData ? workingHoursData[roomData.emailAddress] : null;
            const dayOfWeek = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'][day.getDay()];
            
            // Function to check if a time period has working hours
            const hasWorkingHours = (startHour, endHour) => {
                if (!workingHours || !workingHours.timeSlots || workingHours.timeSlots.length === 0) {
                    return true; // No restrictions, assume available
                }
                
                const daySlots = workingHours.timeSlots.filter(ts => ts.daysOfWeek && ts.daysOfWeek.includes(dayOfWeek));
                if (daySlots.length === 0) {
                    return false; // No working hours for this day
                }
                
                // Check if any working hour block overlaps with this time period
                return daySlots.some(ts => {
                    const [whStartH, whStartM] = ts.startTime.split(':').map(Number);
                    const [whEndH, whEndM] = ts.endTime.split(':').map(Number);
                    const whStart = whStartH + whStartM / 60;
                    const whEnd = whEndH + whEndM / 60;
                    
                    // Check if working hours overlap with this time period
                    return whStart < endHour && whEnd > startHour;
                });
            };
            
            const morningOpen = hasWorkingHours(0, 12);
            const afternoonOpen = hasWorkingHours(12, 18);
            const eveningOpen = hasWorkingHours(18, 24);
            
            const getTimeClass = (count, isOpen) => {
                if (!isOpen) return 'closed';
                if (count === 0) return '';
                if (count === 1) return 'partial';
                return 'busy';
            };
            
            const getTimeDisplay = (count, isOpen) => {
                if (!isOpen) return 'X';
                return count || '✓';
            };
            
            const title = `${avail.count} vergadering(en) - Och: ${morning}, Mid: ${afternoon}, Av: ${evening} - Klik om te boeken`;
            
            // Use data attribute to avoid HTML encoding issues with room names containing special characters
            html += `<div class="availability-cell" 
                          title="${title}"
                          data-room="${room.replace(/"/g, '&quot;')}"
                          data-date="${day.toISOString()}"
                          onclick="openBookingModal(this.getAttribute('data-room'), new Date(this.getAttribute('data-date')))">
                <div class="availability-time-sections">
                    <div class="availability-time-section ${getTimeClass(morning, morningOpen)}">${getTimeDisplay(morning, morningOpen)}</div>
                    <div class="availability-time-section ${getTimeClass(afternoon, afternoonOpen)}">${getTimeDisplay(afternoon, afternoonOpen)}</div>
                    <div class="availability-time-section ${getTimeClass(evening, eveningOpen)}">${getTimeDisplay(evening, eveningOpen)}</div>
                </div>
            </div>`;
        });
    });
    
    html += '</div>';
    availabilityContainer.innerHTML = html;
}

// Laad direct en ververs elke 5 minuten
async function init() {
    // Load rooms and meetings in PARALLEL for faster initial load
    await Promise.all([
        loadRoomsData(),
        loadMeetings()
    ]);
    // Render availability grid after both rooms (with working hours) and meetings are loaded
    renderAvailabilityGrid(allMeetingsData);
    
    // Generate QR code for booking
    generateBookingQRCode();
}

function generateBookingQRCode() {
    const container = document.getElementById('qrCodeContainer');
    if (!container) return;
    
    // Get current URL and add /login with booking redirect
    const baseUrl = window.location.origin + window.location.pathname;
    const bookingUrl = baseUrl.replace('/arcrooms/', '/arcrooms/login?redirect=booking');
    
    // Use QR Server API to generate QR code
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=100x100&data=${encodeURIComponent(bookingUrl)}`;
    
    container.innerHTML = `
        <div style="display: inline-block; cursor: pointer;" onclick="handleQRCodeClick(event)">
            <img src="${qrUrl}" 
                 alt="QR Code voor vergadering boeken" 
                 style="width: 100px; height: 100px; border: 2px solid #e30613; border-radius: 5px; background: white; padding: 5px; transition: transform 0.2s;"
                 title="Klik of scan om vergadering te boeken"
                 onmouseover="this.style.transform='scale(1.05)'"
                 onmouseout="this.style.transform='scale(1)'">
        </div>
    `;
}

function handleQRCodeClick(event) {
    event.preventDefault();
    
    // If user is already logged in, open booking modal directly
    if (isLoggedIn && allRoomsData.length > 0) {
        const firstRoom = allRoomsData[0].displayName;
        openBookingModal(firstRoom, new Date());
    } else {
        // If not logged in, redirect to login with booking redirect
        window.location.href = '/arcrooms/login?redirect=booking';
    }
}

init();
setInterval(async () => {
    // Refresh rooms and meetings in parallel
    await Promise.all([
        loadRoomsData(),
        loadMeetings()
    ]);
    // Re-render availability grid after refresh
    renderAvailabilityGrid(allMeetingsData);
}, 5 * 60 * 1000);

