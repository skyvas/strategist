/**
 * Bistro 15 Client Logic & Real-Time State Controller
 * Compatible with GitHub Pages static hosting & Wasmer Edge API
 */

// Configuration & API Base URL
const DEFAULT_API_BASE = window.location.origin.includes('github.io')
  ? (localStorage.getItem('bistro15_api_url') || 'https://waitlist-api.wasmer.app')
  : window.location.origin;

let API_BASE = DEFAULT_API_BASE;
let activeTicket = null;
let hostPin = sessionStorage.getItem('bistro15_host_pin') || null;
let currentView = 'guest'; // 'guest' | 'host'
let sseConnection = null;
let graceTimerInterval = null;
let pollTimerInterval = null;

// Audio Chime Synthesizer (Web Audio API - Zero external audio file needed)
function playNotificationChime() {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    const ctx = new AudioContext();
    
    // Tone 1: High crisp bell (880 Hz - A5)
    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();
    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(880, ctx.currentTime);
    gain1.gain.setValueAtTime(0.3, ctx.currentTime);
    gain1.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.8);
    osc1.connect(gain1);
    gain1.connect(ctx.destination);
    osc1.start(ctx.currentTime);
    osc1.stop(ctx.currentTime + 0.8);

    // Tone 2: Warm melodic chime (1174.66 Hz - D6) after 150ms
    setTimeout(() => {
      const osc2 = ctx.createOscillator();
      const gain2 = ctx.createGain();
      osc2.type = 'triangle';
      osc2.frequency.setValueAtTime(1174.66, ctx.currentTime);
      gain2.gain.setValueAtTime(0.3, ctx.currentTime);
      gain2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.2);
      osc2.connect(gain2);
      gain2.connect(ctx.destination);
      osc2.start(ctx.currentTime);
      osc2.stop(ctx.currentTime + 1.2);
    }, 150);
  } catch (err) {
    console.warn("Web Audio API chime error:", err);
  }
}

function triggerVibration() {
  if (navigator.vibrate) {
    navigator.vibrate([300, 150, 300, 150, 600]);
  }
}

function testAudioChime() {
  playNotificationChime();
  triggerVibration();
  showToast("Audio chime & haptics tested!", "info");
}

// Toast System
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerText = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 4000);
}

// View Toggle
function toggleView() {
  const guestPanel = document.getElementById('guest-view');
  const hostPanel = document.getElementById('host-view');
  const toggleBtn = document.getElementById('view-toggle-btn');

  if (currentView === 'guest') {
    currentView = 'host';
    guestPanel.classList.remove('active');
    hostPanel.classList.add('active');
    toggleBtn.innerText = 'Guest View';
    initHostView();
  } else {
    currentView = 'guest';
    hostPanel.classList.remove('active');
    guestPanel.classList.add('active');
    toggleBtn.innerText = 'Host Station';
  }
}

// =============================================================================
// GUEST QUEUE & LIVE TRACKER
// =============================================================================

async function handleJoinQueue(event) {
  event.preventDefault();
  const form = document.getElementById('waitlist-form');
  const guestName = document.getElementById('guest-name').value.trim();
  const partySize = parseInt(document.getElementById('party-size').value, 10);
  const phoneNumber = document.getElementById('phone-number').value.trim();

  const submitBtn = document.getElementById('join-queue-btn');
  submitBtn.disabled = true;
  submitBtn.innerText = 'Securing Queue Position...';

  try {
    const res = await fetch(`${API_BASE}/api/queue`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        guest_name: guestName,
        party_size: partySize,
        phone_number: phoneNumber
      })
    });

    const data = await res.json();
    if (!res.ok || !data.success) {
      showToast(data.error || 'Failed to join queue', 'error');
      submitBtn.disabled = false;
      submitBtn.innerText = 'Get In Line Now';
      return;
    }

    // Save ticket to local session
    activeTicket = data.ticket;
    localStorage.setItem('bistro15_ticket', JSON.stringify(activeTicket));
    form.reset();
    showToast(`Welcome ${guestName}! You are in line.`, 'success');
    renderTracker();
  } catch (err) {
    showToast('Network error connecting to waitlist API.', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = 'Get In Line Now';
  }
}

function handleLeaveQueue() {
  if (confirm("Are you sure you want to give up your spot in line?")) {
    localStorage.removeItem('bistro15_ticket');
    activeTicket = null;
    if (graceTimerInterval) clearInterval(graceTimerInterval);
    document.getElementById('tracker-card').classList.add('hidden');
    document.getElementById('ingress-card').classList.remove('hidden');
    showToast("You have left the waitlist.", "info");
  }
}

async function refreshActiveTicket() {
  if (!activeTicket || !activeTicket.ticket_uuid) return;
  try {
    const res = await fetch(`${API_BASE}/api/queue/${activeTicket.ticket_uuid}`);
    if (!res.ok) {
      if (res.status === 404) {
        localStorage.removeItem('bistro15_ticket');
        activeTicket = null;
        document.getElementById('tracker-card').classList.add('hidden');
        document.getElementById('ingress-card').classList.remove('hidden');
      }
      return;
    }
    const data = await res.json();
    if (data.success && data.ticket) {
      const prevStatus = activeTicket.status;
      activeTicket = data.ticket;
      localStorage.setItem('bistro15_ticket', JSON.stringify(activeTicket));
      updateTrackerUI(prevStatus);
    }
  } catch (err) {
    console.debug("Failed refreshing ticket status:", err);
  }
}

function renderTracker() {
  if (!activeTicket) return;
  document.getElementById('ingress-card').classList.add('hidden');
  document.getElementById('tracker-card').classList.remove('hidden');
  updateTrackerUI(null);
  refreshActiveTicket();
}

let lastAlertedStatus = null;
let lastAlertedReminder = false;

function updateTrackerUI(prevStatus) {
  if (!activeTicket) return;

  const bannerBadge = document.getElementById('tracker-status-badge');
  const ticketIdEl = document.getElementById('tracker-ticket-id');
  const greetingEl = document.getElementById('tracker-guest-greeting');
  const partyMetaEl = document.getElementById('tracker-party-meta');
  const posEl = document.getElementById('tracker-position');
  const waitEl = document.getElementById('tracker-est-wait');
  const heroAlert = document.getElementById('called-hero-alert');
  const tableCallout = document.getElementById('called-table-label');
  const activityTitle = document.getElementById('activity-title');
  const activityDesc = document.getElementById('activity-desc');
  const activityBadge = document.getElementById('activity-badge');

  ticketIdEl.innerText = `#${activeTicket.ticket_uuid.toUpperCase()}`;
  greetingEl.innerText = `Hello, ${activeTicket.guest_name}!`;
  partyMetaEl.innerText = `Party of ${activeTicket.party_size} • Phone: ${activeTicket.phone_number}`;

  bannerBadge.innerText = activeTicket.status;
  activityBadge.innerText = activeTicket.status;

  if (activeTicket.status === 'WAITING') {
    heroAlert.classList.add('hidden');
    bannerBadge.className = 'badge badge-connected';
    posEl.innerText = activeTicket.queue_position > 0 ? `#${activeTicket.queue_position}` : '1';
    waitEl.innerText = activeTicket.estimated_wait_minutes || '10-15';
    activityTitle.innerText = "Bistro 15 • In Queue";
    activityDesc.innerText = `Position #${activeTicket.queue_position || 1} (~${activeTicket.estimated_wait_minutes || 10}m wait)`;
  } else if (activeTicket.status === 'CALLED') {
    heroAlert.classList.remove('hidden');
    bannerBadge.className = 'badge badge-connected';
    tableCallout.innerText = `Table #${activeTicket.assigned_table_number || 'Ready'}`;
    posEl.innerText = 'NOW';
    waitEl.innerText = '0';
    activityTitle.innerText = `Table #${activeTicket.assigned_table_number || 'Ready'} is Ready!`;
    activityDesc.innerText = "Proceed to the Host Stand now";
    activityBadge.className = "pill-badge";
    activityBadge.style.background = "rgba(6, 182, 212, 0.3)";
    activityBadge.style.color = "#38bdf8";

    // Play chime & alert if transitioning to CALLED
    if (lastAlertedStatus !== 'CALLED') {
      playNotificationChime();
      triggerVibration();
      showToast(`Your Table #${activeTicket.assigned_table_number} is ready!`, 'success');
      lastAlertedStatus = 'CALLED';
    }

    // Start 10-Minute Grace Countdown
    startGraceCountdown(activeTicket.grace_seconds_remaining || 600);
  } else if (activeTicket.status === 'SEATED') {
    heroAlert.classList.add('hidden');
    bannerBadge.innerText = 'SEATED';
    greetingEl.innerText = `Enjoy your meal, ${activeTicket.guest_name}!`;
    posEl.innerText = '✓';
    waitEl.innerText = '0';
    activityTitle.innerText = "Seated at Bistro 15";
    activityDesc.innerText = `Table #${activeTicket.assigned_table_number}`;
  } else if (activeTicket.status === 'EXPIRED') {
    heroAlert.classList.add('hidden');
    bannerBadge.innerText = 'EXPIRED';
    greetingEl.innerText = `Reservation Expired`;
    posEl.innerText = '--';
    waitEl.innerText = '--';
  }
}

function startGraceCountdown(initialSeconds) {
  if (graceTimerInterval) clearInterval(graceTimerInterval);
  let secondsRemaining = initialSeconds;

  function tick() {
    const digits = document.getElementById('grace-digits');
    const fill = document.getElementById('grace-bar-fill');
    const hint = document.getElementById('grace-hint');
    if (!digits || !fill) return;

    const mins = Math.floor(secondsRemaining / 60);
    const secs = secondsRemaining % 60;
    digits.innerText = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;

    const pct = Math.max(0, (secondsRemaining / 600) * 100);
    fill.style.width = `${pct}%`;

    // 7-minute mark trigger (3:00 remaining -> 180 seconds)
    if (secondsRemaining <= 180 && secondsRemaining > 0 && !lastAlertedReminder) {
      playNotificationChime();
      triggerVibration();
      showToast("Second Reminder: 3 minutes remaining before table release!", "warning");
      hint.innerText = "⚠️ Final 3 minutes remaining before table reassignment!";
      hint.style.color = "#f87171";
      lastAlertedReminder = true;
    }

    if (secondsRemaining <= 0) {
      clearInterval(graceTimerInterval);
      digits.innerText = "00:00";
      hint.innerText = "Table hold period expired.";
    }

    secondsRemaining--;
  }

  tick();
  graceTimerInterval = setInterval(tick, 1000);
}

// =============================================================================
// HOST STATION CONTROLLER
// =============================================================================

function initHostView() {
  if (hostPin) {
    document.getElementById('host-auth-box').classList.add('hidden');
    document.getElementById('host-dashboard').classList.remove('hidden');
    refreshHostData();
  } else {
    document.getElementById('host-auth-box').classList.remove('hidden');
    document.getElementById('host-dashboard').classList.add('hidden');
  }
}

async function authenticateHost() {
  const pinInput = document.getElementById('host-pin-input');
  const pin = pinInput.value.trim();
  if (!pin) {
    showToast("Please enter host PIN", "error");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/host/tables?pin=${pin}`);
    if (res.ok) {
      hostPin = pin;
      sessionStorage.setItem('bistro15_host_pin', hostPin);
      showToast("Host Station Unlocked", "success");
      initHostView();
    } else {
      showToast("Invalid Host PIN", "error");
    }
  } catch (err) {
    showToast("Network error verifying host PIN", "error");
  }
}

function logoutHost() {
  sessionStorage.removeItem('bistro15_host_pin');
  hostPin = null;
  initHostView();
}

async function refreshHostData() {
  if (!hostPin) return;
  try {
    const [tablesRes, queueRes] = await Promise.all([
      fetch(`${API_BASE}/api/host/tables?pin=${hostPin}`),
      fetch(`${API_BASE}/api/host/queue?pin=${hostPin}`)
    ]);

    if (!tablesRes.ok || !queueRes.ok) {
      if (tablesRes.status === 401) logoutHost();
      return;
    }

    const tablesData = await tablesRes.json();
    const queueData = await queueRes.json();

    renderHostTables(tablesData.tables || []);
    renderHostQueue(queueData.queue || [], tablesData.tables || []);
  } catch (err) {
    console.debug("Failed refreshing host data:", err);
  }
}

function renderHostTables(tables) {
  const grid = document.getElementById('tables-grid');
  grid.innerHTML = '';

  let availableCount = 0;
  let calledCount = 0;
  let occupiedCount = 0;
  let dirtyCount = 0;

  tables.forEach(tbl => {
    const status = tbl.status.toLowerCase();
    if (status === 'available') availableCount++;
    else if (status === 'called') calledCount++;
    else if (status === 'occupied') occupiedCount++;
    else if (status === 'dirty') dirtyCount++;

    const card = document.createElement('div');
    card.className = `table-card ${status}`;

    let actionBtn = '';
    let guestInfo = '';
    let timerInfo = '';

    if (status === 'available') {
      actionBtn = `<button class="btn btn-sm btn-outline btn-block" onclick="promptCallNext(${tbl.table_number})">Call Next Party</button>`;
    } else if (status === 'called') {
      guestInfo = `<div class="table-guest-info">👤 ${tbl.guest_name || 'Guest'} (${tbl.party_size || '?'}p)</div>`;
      timerInfo = `<div class="table-timer">⏳ ${Math.floor((tbl.grace_seconds_remaining || 0) / 60)}m left</div>`;
      actionBtn = `
        <button class="btn btn-sm btn-primary" onclick="seatTable(${tbl.table_number})">Seat</button>
        <button class="btn btn-sm btn-danger" onclick="bumpTable(${tbl.table_number})">Bump</button>
      `;
    } else if (status === 'occupied') {
      guestInfo = `<div class="table-guest-info">👤 ${tbl.guest_name || 'Dining'} (${tbl.party_size || '?'}p)</div>`;
      timerInfo = `<div class="table-timer">⏱️ Seated: ${tbl.elapsed_dining_minutes || 0}m</div>`;
      actionBtn = `<button class="btn btn-sm btn-outline btn-block" onclick="markDirty(${tbl.table_number})">Vacate / Clear</button>`;
    } else if (status === 'dirty') {
      timerInfo = `<div class="table-timer">🧹 Needs Bussing</div>`;
      actionBtn = `<button class="btn btn-sm btn-primary btn-block" style="background:#ca8a04" onclick="cleanTable(${tbl.table_number})">Mark Clean</button>`;
    }

    card.innerHTML = `
      <div class="table-header">
        <span class="table-number">T-${tbl.table_number}</span>
        <span class="table-cap">${tbl.capacity}-Top</span>
      </div>
      <div>
        <span class="table-status-pill">${tbl.status}</span>
        ${guestInfo}
        ${timerInfo}
      </div>
      <div class="table-actions">
        ${actionBtn}
      </div>
    `;

    grid.appendChild(card);
  });

  document.getElementById('count-available').innerText = availableCount;
  document.getElementById('count-called').innerText = calledCount;
  document.getElementById('count-occupied').innerText = occupiedCount;
  document.getElementById('count-dirty').innerText = dirtyCount;
}

function renderHostQueue(queue, tables) {
  const queueList = document.getElementById('host-queue-list');
  const badge = document.getElementById('queue-count-badge');
  badge.innerText = `${queue.length} Parties`;
  queueList.innerHTML = '';

  if (queue.length === 0) {
    queueList.innerHTML = '<div style="color:var(--text-dim); padding:20px; text-align:center;">No waiting parties in queue.</div>';
    return;
  }

  // Find available tables
  const availableTables = tables.filter(t => t.status === 'AVAILABLE');

  queue.forEach(item => {
    const div = document.createElement('div');
    div.className = 'queue-item';

    // Best matching table button
    let callBtn = '';
    if (item.status === 'WAITING' && availableTables.length > 0) {
      // Find table with capacity >= party_size
      const match = availableTables.find(t => t.capacity >= item.party_size) || availableTables[0];
      callBtn = `<button class="btn btn-sm btn-primary" onclick="callPartyToTable(${item.id}, ${match.table_number})">Call to T-${match.table_number}</button>`;
    } else if (item.status === 'CALLED') {
      callBtn = `<span class="badge badge-connected">Called (T-${item.assigned_table_number})</span>`;
    }

    div.innerHTML = `
      <div class="queue-item-left">
        <div class="queue-pos-badge">#${item.queue_position}</div>
        <div>
          <div class="queue-item-name">${item.guest_name}</div>
          <div class="queue-item-meta">${item.party_size} guests • ${item.phone_number}</div>
        </div>
      </div>
      <div class="queue-item-actions">
        ${callBtn}
      </div>
    `;
    queueList.appendChild(div);
  });
}

async function callPartyToTable(partyId, tableNumber) {
  try {
    const res = await fetch(`${API_BASE}/api/host/call`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Host-PIN': hostPin },
      body: JSON.stringify({ party_id: partyId, table_number: tableNumber })
    });
    const data = await res.json();
    if (res.ok) {
      showToast(`Party called to Table ${tableNumber}!`, 'success');
      refreshHostData();
    } else {
      showToast(data.error || 'Failed to call party', 'error');
    }
  } catch (err) {
    showToast('Network error calling party', 'error');
  }
}

async function promptCallNext(tableNumber) {
  // Fetch queue and pick first matching party
  try {
    const res = await fetch(`${API_BASE}/api/host/queue?pin=${hostPin}`);
    const data = await res.json();
    const waiting = (data.queue || []).filter(q => q.status === 'WAITING');
    if (waiting.length === 0) {
      showToast("No parties waiting in queue!", "info");
      return;
    }
    const party = waiting[0];
    callPartyToTable(party.id, tableNumber);
  } catch (err) {
    showToast("Error retrieving waiting queue", "error");
  }
}

async function seatTable(tableNumber) {
  try {
    const res = await fetch(`${API_BASE}/api/host/seat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Host-PIN': hostPin },
      body: JSON.stringify({ table_number: tableNumber })
    });
    if (res.ok) {
      showToast(`Table ${tableNumber} seated!`, 'success');
      refreshHostData();
    } else {
      const data = await res.json();
      showToast(data.error || 'Failed to seat table', 'error');
    }
  } catch (err) {
    showToast('Network error seating table', 'error');
  }
}

async function markDirty(tableNumber) {
  try {
    const res = await fetch(`${API_BASE}/api/host/dirty`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Host-PIN': hostPin },
      body: JSON.stringify({ table_number: tableNumber })
    });
    if (res.ok) {
      showToast(`Table ${tableNumber} cleared (marked dirty)`, 'info');
      refreshHostData();
    }
  } catch (err) {
    showToast('Network error clearing table', 'error');
  }
}

async function cleanTable(tableNumber) {
  try {
    const res = await fetch(`${API_BASE}/api/host/clean`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Host-PIN': hostPin },
      body: JSON.stringify({ table_number: tableNumber })
    });
    if (res.ok) {
      showToast(`Table ${tableNumber} clean and ready!`, 'success');
      refreshHostData();
    }
  } catch (err) {
    showToast('Network error cleaning table', 'error');
  }
}

async function bumpTable(tableNumber) {
  if (confirm(`Bump / cancel party at Table ${tableNumber} to free it for next party?`)) {
    try {
      const res = await fetch(`${API_BASE}/api/host/bump`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Host-PIN': hostPin },
        body: JSON.stringify({ table_number: tableNumber, force: true })
      });
      if (res.ok) {
        showToast(`Table ${tableNumber} released!`, 'info');
        refreshHostData();
      } else {
        const data = await res.json();
        showToast(data.error || 'Failed to bump table', 'error');
      }
    } catch (err) {
      showToast('Network error bumping table', 'error');
    }
  }
}

// =============================================================================
// REAL-TIME EVENT STREAM (SSE)
// =============================================================================

function connectEventStream() {
  if (typeof EventSource === 'undefined') return;

  try {
    sseConnection = new EventSource(`${API_BASE}/api/events`);

    sseConnection.onopen = () => {
      const badge = document.getElementById('connection-badge');
      if (badge) badge.style.display = 'inline-flex';
    };

    sseConnection.addEventListener('PARTY_CALLED', (e) => {
      refreshActiveTicket();
      if (currentView === 'host') refreshHostData();
    });

    sseConnection.addEventListener('QUEUE_UPDATED', (e) => {
      refreshActiveTicket();
      if (currentView === 'host') refreshHostData();
    });

    sseConnection.addEventListener('TABLES_UPDATED', (e) => {
      refreshActiveTicket();
      if (currentView === 'host') refreshHostData();
    });

    sseConnection.onerror = () => {
      console.debug("SSE disconnected. Falling back to background poll.");
    };
  } catch (err) {
    console.debug("SSE initialization error:", err);
  }
}

// Initial Boot
window.addEventListener('DOMContentLoaded', () => {
  // Check localStorage for active ticket
  const saved = localStorage.getItem('bistro15_ticket');
  if (saved) {
    try {
      activeTicket = JSON.parse(saved);
      renderTracker();
    } catch (e) {
      localStorage.removeItem('bistro15_ticket');
    }
  }

  // Check URL hash for direct host navigation
  if (window.location.hash === '#host') {
    toggleView();
  }

  connectEventStream();

  // Polling fallback every 3.5 seconds
  pollTimerInterval = setInterval(() => {
    if (activeTicket) refreshActiveTicket();
    if (currentView === 'host' && hostPin) refreshHostData();
  }, 3500);
});
