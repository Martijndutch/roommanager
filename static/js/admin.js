// Configuration
const daysOfWeek = [
    {name: 'Zondag', value: 'sunday'},
    {name: 'Maandag', value: 'monday'},
    {name: 'Dinsdag', value: 'tuesday'},
    {name: 'Woensdag', value: 'wednesday'},
    {name: 'Donderdag', value: 'thursday'},
    {name: 'Vrijdag', value: 'friday'},
    {name: 'Zaterdag', value: 'saturday'}
];

let roomsData = [];
let dragState = null;

function showLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = 'flex';
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = 'none';
}

function updateLoadingStatus(message, progress = '') {
    const statusEl = document.getElementById('loadingStatus');
    const progressEl = document.getElementById('loadingProgress');
    if (statusEl) statusEl.textContent = message;
    if (progressEl) progressEl.textContent = progress;
}

async function loadRooms() {
    try {
        showLoadingOverlay();
        updateLoadingStatus('Ruimtes ophalen van server...');
        
        const response = await fetch('/arcrooms/api/rooms');
        const data = await response.json();
        roomsData = data.rooms || [];
        
        updateLoadingStatus(`${roomsData.length} ruimtes gevonden`, `✓ Stap 1/2`);
        await new Promise(resolve => setTimeout(resolve, 300)); // Short delay for UI feedback
        
        // Load working hours for each room
        updateLoadingStatus('Beschikbaarheid ophalen per ruimte...');
        
        // Load working hours for all rooms in PARALLEL
        const workingHoursPromises = roomsData.map((room, i) => {
            updateLoadingStatus(
                `Beschikbaarheid laden: ${room.displayName}`,
                `Ruimte ${i + 1}/${roomsData.length}`
            );
            return fetch(`/arcrooms/api/admin/working-hours/${encodeURIComponent(room.emailAddress)}`)
                .then(whResponse => whResponse.json())
                .then(workingHours => {
                    room.workingHours = workingHours;
                    room.canEdit = workingHours.canEdit !== false;
                    
                    // Initialize time blocks structure
                    room.timeBlocks = {};
                    daysOfWeek.forEach(day => {
                        const slots = workingHours?.timeSlots?.filter(ts => ts.daysOfWeek?.includes(day.value)) || [];
                        room.timeBlocks[day.value] = slots.map(slot => ({
                            start: timeToMinutes(slot.startTime),
                            end: timeToMinutes(slot.endTime)
                        }));
                    });
                    
                    updateLoadingStatus(
                        `Beschikbaarheid geladen: ${room.displayName}`,
                        `Ruimte ${i + 1}/${roomsData.length}`
                    );
                });
        });
        
        // Wait for all working hours to load
        await Promise.all(workingHoursPromises);
        
        updateLoadingStatus('Interface opbouwen...', `✓ Stap 2/2`);
        await new Promise(resolve => setTimeout(resolve, 200));
        
        renderRooms();
        hideLoadingOverlay();
    } catch (error) {
        hideLoadingOverlay();
        showStatus('Fout bij laden van ruimtes: ' + error.message, 'error');
    }
}

function timeToMinutes(timeStr) {
    const [h, m] = timeStr.split(':').map(Number);
    return h * 60 + m;
}

function minutesToTime(minutes) {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function renderRooms() {
    const container = document.getElementById('roomsContainer');
    container.innerHTML = '';
    
    roomsData.forEach((room, roomIndex) => {
        const card = document.createElement('div');
        card.className = 'room-card';
        
        // Add read-only indicator if user can't edit
        if (!room.canEdit) {
            card.classList.add('read-only');
        }
        
        // Build delegates display
        let delegatesHtml = '<div class="room-delegates">';
        if (room.delegates && room.delegates.length > 0) {
            delegatesHtml += '<strong>Gemachtigden:</strong><div class="delegate-list">';
            room.delegates.forEach(d => {
                delegatesHtml += `📧 ${d.name} (${d.email}) - ${d.role}<br>`;
            });
            delegatesHtml += '</div>';
        } else {
            delegatesHtml += '<strong>Gemachtigden:</strong> <span class="no-permission">Geen gemachtigden ingesteld</span>';
        }
        delegatesHtml += '</div>';
        
        const readOnlyBadge = !room.canEdit ? '<span class="read-only-badge">🔒 Alleen lezen</span>' : '';
        
        card.innerHTML = `
            <h2>
                ${room.displayName}
                ${readOnlyBadge}
            </h2>
            ${delegatesHtml}
            <table class="schedule-table">
                <tbody id="schedule-body-${roomIndex}">
                </tbody>
            </table>
        `;
        
        // Add card to DOM first so we can query the tbody
        container.appendChild(card);
        
        // Now render day rows
        const tbody = document.getElementById(`schedule-body-${roomIndex}`);
        daysOfWeek.forEach((day, dayIndex) => {
            tbody.insertAdjacentHTML('beforeend', renderDayRow(room, day, roomIndex, dayIndex));
        });
    });
    
    // Add event listeners for drag and resize
    setupDragAndResize();
}

function renderDayRow(room, day, roomIndex, dayIndex) {
    const blocks = room.timeBlocks[day.value] || [];
    const disabled = !room.canEdit ? 'disabled' : '';
    
    const blocksHtml = blocks.map((block, blockIndex) => {
        const leftPercent = (block.start / (24 * 60)) * 100;
        const widthPercent = ((block.end - block.start) / (24 * 60)) * 100;
        const disabledClass = !room.canEdit ? 'disabled' : '';
        const deleteButton = room.canEdit 
            ? '<button class="btn-delete-block" onclick="deleteTimeBlock(' + roomIndex + ', ' + dayIndex + ', ' + blockIndex + ')" title="Verwijder">&times;</button>'
            : '';
        return `
            <div class="time-block-visual ${disabledClass}" 
                 data-room="${roomIndex}" 
                 data-day="${dayIndex}" 
                 data-block="${blockIndex}"
                 style="left: ${leftPercent}%; width: ${widthPercent}%;">
                ${room.canEdit ? '<div class="resize-handle left"></div>' : ''}
                ${minutesToTime(block.start)} - ${minutesToTime(block.end)}
                ${room.canEdit ? '<div class="resize-handle right"></div>' : ''}
                ${deleteButton}
            </div>
        `;
    }).join('');
    
    const addButton = room.canEdit 
        ? '<button class="btn-add-slot" onclick="addTimeBlock(' + roomIndex + ', ' + dayIndex + ')">+</button>'
        : '';
    
    return `
        <tr>
            <td class="day-label">
                ${day.name}
                ${addButton}
            </td>
            <td colspan="48">
                <div class="timeline-container" id="timeline-${roomIndex}-${dayIndex}">
                    ${blocksHtml}
                </div>
            </td>
        </tr>
    `;
}

function setupDragAndResize() {
    document.querySelectorAll('.time-block-visual').forEach(block => {
        // Skip if block is disabled (read-only room)
        if (block.classList.contains('disabled')) {
            return;
        }
        
        const leftHandle = block.querySelector('.resize-handle.left');
        const rightHandle = block.querySelector('.resize-handle.right');
        
        if (leftHandle) {
            leftHandle.addEventListener('mousedown', (e) => startResize(e, block, 'left'));
        }
        if (rightHandle) {
            rightHandle.addEventListener('mousedown', (e) => startResize(e, block, 'right'));
        }
        
        block.addEventListener('mousedown', (e) => {
            if (!e.target.classList.contains('resize-handle')) {
                startDrag(e, block);
            }
        });
    });
}

function startDrag(e, block) {
    e.preventDefault();
    e.stopPropagation();
    
    const roomIndex = parseInt(block.dataset.room);
    const dayIndex = parseInt(block.dataset.day);
    const blockIndex = parseInt(block.dataset.block);
    const timeline = block.parentElement;
    const rect = timeline.getBoundingClientRect();
    
    dragState = {
        type: 'drag',
        block,
        roomIndex,
        dayIndex,
        blockIndex,
        timeline,
        timelineWidth: rect.width,
        startX: e.clientX,
        initialLeft: parseFloat(block.style.left)
    };
    
    document.addEventListener('mousemove', handleDrag);
    document.addEventListener('mouseup', endDrag);
}

function startResize(e, block, handle) {
    e.preventDefault();
    e.stopPropagation();
    
    const roomIndex = parseInt(block.dataset.room);
    const dayIndex = parseInt(block.dataset.day);
    const blockIndex = parseInt(block.dataset.block);
    const timeline = block.parentElement;
    const rect = timeline.getBoundingClientRect();
    
    dragState = {
        type: 'resize',
        handle,
        block,
        roomIndex,
        dayIndex,
        blockIndex,
        timeline,
        timelineWidth: rect.width,
        startX: e.clientX,
        initialLeft: parseFloat(block.style.left),
        initialWidth: parseFloat(block.style.width)
    };
    
    document.addEventListener('mousemove', handleResize);
    document.addEventListener('mouseup', endResize);
}

function handleDrag(e) {
    if (!dragState || dragState.type !== 'drag') return;
    
    const deltaX = e.clientX - dragState.startX;
    const deltaPercent = (deltaX / dragState.timelineWidth) * 100;
    let newLeft = dragState.initialLeft + deltaPercent;
    
    // Constrain to 0-100%
    const width = parseFloat(dragState.block.style.width);
    newLeft = Math.max(0, Math.min(100 - width, newLeft));
    
    // Snap to 30-minute intervals
    const totalMinutes = (newLeft / 100) * 24 * 60;
    const snappedMinutes = Math.round(totalMinutes / 30) * 30;
    newLeft = (snappedMinutes / (24 * 60)) * 100;
    
    dragState.block.style.left = newLeft + '%';
    updateBlockData(dragState.roomIndex, dragState.dayIndex, dragState.blockIndex);
}

function handleResize(e) {
    if (!dragState || dragState.type !== 'resize') return;
    
    const deltaX = e.clientX - dragState.startX;
    const deltaPercent = (deltaX / dragState.timelineWidth) * 100;
    
    if (dragState.handle === 'left') {
        let newLeft = dragState.initialLeft + deltaPercent;
        let newWidth = dragState.initialWidth - deltaPercent;
        
        // Snap to 30-minute intervals
        const totalMinutes = (newLeft / 100) * 24 * 60;
        const snappedMinutes = Math.round(totalMinutes / 30) * 30;
        newLeft = (snappedMinutes / (24 * 60)) * 100;
        
        // Recalculate width based on snapped position
        const currentRight = dragState.initialLeft + dragState.initialWidth;
        newWidth = currentRight - newLeft;
        
        // Constrain
        newLeft = Math.max(0, newLeft);
        newWidth = Math.max(2, Math.min(100 - newLeft, newWidth));
        
        dragState.block.style.left = newLeft + '%';
        dragState.block.style.width = newWidth + '%';
    } else {
        let newWidth = dragState.initialWidth + deltaPercent;
        const currentLeft = parseFloat(dragState.block.style.left);
        
        // Snap to 30-minute intervals
        const endMinutes = ((currentLeft + newWidth) / 100) * 24 * 60;
        const snappedEndMinutes = Math.round(endMinutes / 30) * 30;
        const snappedEndPercent = (snappedEndMinutes / (24 * 60)) * 100;
        newWidth = snappedEndPercent - currentLeft;
        
        newWidth = Math.max(2, Math.min(100 - currentLeft, newWidth));
        dragState.block.style.width = newWidth + '%';
    }
    
    updateBlockData(dragState.roomIndex, dragState.dayIndex, dragState.blockIndex);
}

function endDrag() {
    document.removeEventListener('mousemove', handleDrag);
    document.removeEventListener('mouseup', endDrag);
    dragState = null;
}

function endResize() {
    document.removeEventListener('mousemove', handleResize);
    document.removeEventListener('mouseup', endResize);
    dragState = null;
}

function updateBlockData(roomIndex, dayIndex, blockIndex) {
    const block = document.querySelector(`[data-room="${roomIndex}"][data-day="${dayIndex}"][data-block="${blockIndex}"]`);
    const left = parseFloat(block.style.left);
    const width = parseFloat(block.style.width);
    
    // Snap to 30-minute intervals
    const startMinutes = Math.round((left / 100) * 24 * 60 / 30) * 30;
    const endMinutes = Math.round(((left + width) / 100) * 24 * 60 / 30) * 30;
    
    const day = daysOfWeek[dayIndex];
    const room = roomsData[roomIndex];
    room.timeBlocks[day.value][blockIndex] = {
        start: startMinutes,
        end: endMinutes
    };
    
    // Update label - avoid nested template literal
    const deleteBtn = '<button class="btn-delete-block" onclick="deleteTimeBlock(' + roomIndex + ', ' + dayIndex + ', ' + blockIndex + ')" title="Verwijder">&times;</button>';
    block.innerHTML = `
        <div class="resize-handle left"></div>
        ${minutesToTime(startMinutes)} - ${minutesToTime(endMinutes)}
        <div class="resize-handle right"></div>
        ${deleteBtn}
    `;
    
    // Re-attach event listeners to the new handles
    setupDragAndResize();
}

function deleteTimeBlock(roomIndex, dayIndex, blockIndex) {
    const room = roomsData[roomIndex];
    
    // Check if room is editable
    if (!room.canEdit) {
        showStatus('Deze ruimte is alleen-lezen. U heeft geen rechten om deze aan te passen.', 'error');
        return;
    }
    
    const day = daysOfWeek[dayIndex];
    const blocks = room.timeBlocks[day.value] || [];
    
    // Remove the block
    blocks.splice(blockIndex, 1);
    room.timeBlocks[day.value] = blocks;
    
    // Re-render this specific day row
    const tbody = document.getElementById(`schedule-body-${roomIndex}`);
    if (!tbody) {
        console.error('tbody not found for room', roomIndex);
        return;
    }
    const rows = tbody.querySelectorAll('tr');
    if (rows[dayIndex]) {
        rows[dayIndex].outerHTML = renderDayRow(room, day, roomIndex, dayIndex);
    }
    
    setupDragAndResize();
}

function addTimeBlock(roomIndex, dayIndex) {
    const room = roomsData[roomIndex];
    
    // Check if room is editable
    if (!room.canEdit) {
        showStatus('Deze ruimte is alleen-lezen. U heeft geen rechten om deze aan te passen.', 'error');
        return;
    }
    
    const day = daysOfWeek[dayIndex];
    const blocks = room.timeBlocks[day.value] || [];
    
    // Add new block (08:00 - 17:00 by default)
    blocks.push({ start: 8 * 60, end: 17 * 60 });
    room.timeBlocks[day.value] = blocks;
    
    // Re-render this specific day row
    const tbody = document.getElementById(`schedule-body-${roomIndex}`);
    if (!tbody) {
        console.error('tbody not found for room', roomIndex);
        return;
    }
    const rows = tbody.querySelectorAll('tr');
    if (rows[dayIndex]) {
        rows[dayIndex].outerHTML = renderDayRow(room, day, roomIndex, dayIndex);
    }
    
    setupDragAndResize();
}

async function saveAllWorkingHours() {
    const statusDiv = document.getElementById('statusMessage');
    statusDiv.className = 'status-message';
    statusDiv.textContent = 'Bezig met opslaan en blokkades verwijderen...';
    statusDiv.style.display = 'block';
    
    let savedCount = 0;
    let skippedCount = 0;
    
    try {
        for (let roomIndex = 0; roomIndex < roomsData.length; roomIndex++) {
            const room = roomsData[roomIndex];
            
            // Skip rooms user can't edit
            if (!room.canEdit) {
                skippedCount++;
                continue;
            }
            
            const timeSlots = [];
            
            daysOfWeek.forEach(day => {
                const blocks = room.timeBlocks[day.value] || [];
                blocks.forEach(block => {
                    timeSlots.push({
                        daysOfWeek: [day.value],
                        startTime: minutesToTime(block.start) + ':00',
                        endTime: minutesToTime(block.end) + ':00'
                    });
                });
            });
            
            const workingHours = {
                timeSlots: timeSlots,
                timeZone: {
                    name: 'W. Europe Standard Time'
                }
            };
            
            const response = await fetch(`/arcrooms/api/admin/working-hours/${encodeURIComponent(room.emailAddress)}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(workingHours)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`Fout bij ${room.displayName}: ${errorData.error || response.statusText}`);
            }
            savedCount++;
        }
        
        let message = `✓ ${savedCount} ruimte(s) succesvol opgeslagen`;
        if (skippedCount > 0) {
            message += ` (${skippedCount} alleen-lezen ruimte(s) overgeslagen)`;
        }
        message += ' en blokkades verwijderd uit Exchange!';
        showStatus(message, 'success');
    } catch (error) {
        showStatus('Fout bij opslaan: ' + error.message, 'error');
    }
}

function showStatus(message, type) {
    const statusDiv = document.getElementById('statusMessage');
    statusDiv.className = `status-message ${type}`;
    statusDiv.textContent = message;
    
    if (type === 'success') {
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 3000);
    }
}

// Initialize on page load
loadRooms();
