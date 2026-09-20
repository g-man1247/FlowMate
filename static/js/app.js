/* ==========================================================================
   FLOWMATE - AI STUDY-FOCUS ASSISTANT SPA CONTROLLER
   ========================================================================== */

let currentTab = 'dashboard';
let telemetryInterval = null;

// Chart Instances
let heartRateChartInstance = null;
let activityChartInstance = null;
let weeklyHoursChartInstance = null;
let subjectPieChartInstance = null;

// Data Arrays for Real-Time Streaming Chart
const heartRateDataBuffer = [];
const heartRateTimeLabels = [];
const maxChartPoints = 20;

// Application Initialization
document.addEventListener('DOMContentLoaded', () => {
    initTabNavigation();
    initCharts();
    loadCurrentUserProfile();
    fetchSystemStatus();
    loadStudyPlan();
    loadNotifications();
    loadFacultyView();
    
    // Start continuous telemetry polling (every 2 seconds)
    telemetryInterval = setInterval(fetchTelemetry, 2000);
});

// Tab Navigation
function initTabNavigation() {
    const navButtons = document.querySelectorAll('.nav-item, .bottom-nav-item, .nav-link-trigger');
    navButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const targetTab = btn.getAttribute('data-tab');
            if (targetTab) switchTab(targetTab);
        });
    });

    const mobileToggle = document.getElementById('mobile-menu-toggle');
    const sidebar = document.getElementById('app-sidebar');
    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }
}

function switchTab(tabId) {
    currentTab = tabId;
    
    // Update Nav Buttons
    document.querySelectorAll('.nav-item, .bottom-nav-item').forEach(b => {
        b.classList.remove('active');
        if (b.getAttribute('data-tab') === tabId) b.classList.add('active');
    });

    // Update Tab Pages
    document.querySelectorAll('.tab-page').forEach(page => {
        page.classList.remove('active');
    });

    const targetPage = document.getElementById(`tab-${tabId}`);
    if (targetPage) {
        targetPage.classList.add('active');
    }

    // Tab Specific Actions
    if (tabId === 'history') loadSessionHistory();
    if (tabId === 'notifications') loadNotifications();
    if (tabId === 'faculty') loadFacultyView();
    if (tabId === 'progress') renderProgressCharts();
}

// REST API Service Functions

async function fetchSystemStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();
        updateUIWithStatus(data);
    } catch (err) {
        console.warn('API Status fetch error:', err);
    }
}

async function fetchTelemetry() {
    try {
        const res = await fetch('/api/sensor/read');
        const data = await res.json();
        
        // Update live charts
        updateHeartRateChart(data.bpm, data.timestamp);
        
        // Also update status
        fetchSystemStatus();
    } catch (err) {
        console.warn('Telemetry poll error:', err);
    }
}

function updateUIWithStatus(data) {
    if (!data) return;

    // Student & Goals
    if (data.student) {
        document.getElementById('dash-completed-time').innerText = 
            `${Math.floor(data.student.completed_minutes/60)}h ${data.student.completed_minutes%60}m`;
        document.getElementById('dash-focus-score').innerText = `${data.student.focus_score}%`;
    }

    // Session Timer & Subject
    if (data.session) {
        const elapsedSec = data.session.elapsed_seconds || 0;
        const formattedTimer = formatSeconds(elapsedSec);
        
        document.getElementById('dash-timer-display').innerText = formattedTimer;
        document.getElementById('session-clock-display').innerText = formattedTimer;
        
        document.getElementById('dash-subject-display').innerText = data.session.current_subject;
        document.getElementById('session-subject-tag').innerText = data.session.current_subject;
        
        document.getElementById('dash-task-display').innerText = data.session.current_task;
        document.getElementById('session-task-tag').innerText = data.session.current_task;
        
        const isSessionActive = data.session.active && data.session.state === 'ACTIVE';
        document.getElementById('dash-session-status-badge').innerText = isSessionActive ? 'ACTIVE SESSION' : (data.session.state || 'IDLE');
        document.getElementById('dash-session-status-badge').className = isSessionActive ? 'badge badge-primary' : 'badge badge-secondary';
    }

    // Sensor Status & Mode
    if (data.sensor) {
        document.getElementById('dash-sensor-mode').innerText = `${data.sensor.mode} MODE`;
        document.getElementById('header-sensor-text').innerText = `Sensor: ${data.sensor.mode} (${data.sensor.device_name})`;
        document.getElementById('chart-live-bpm').innerText = data.sensor.bpm.toFixed(1);
        document.getElementById('dash-live-bpm').innerText = `${data.sensor.bpm.toFixed(1)} BPM`;
        
        document.getElementById('matrix-bpm').innerText = `${data.sensor.bpm.toFixed(1)} BPM`;
        document.getElementById('matrix-device').innerText = `Source: ${data.sensor.device_name}`;
        
        document.getElementById('dash-hw-status').innerText = data.sensor.connected ? 'Hardware Connected' : 'Sensor Disconnected';
        document.getElementById('session-bpm-val').innerText = `${data.sensor.bpm.toFixed(1)} BPM`;
        document.getElementById('session-device-sub').innerText = data.sensor.device_name;
    }

    // Focus Analysis & Software Classification
    if (data.focus_analysis) {
        document.getElementById('session-focus-status').innerText = data.focus_analysis.status;
        document.getElementById('session-confidence-sub').innerText = `Software Confidence: ${data.focus_analysis.confidence_pct}%`;
        
        document.getElementById('dash-act-status').innerText = `Activity: ${data.focus_analysis.activity_level}`;
        document.getElementById('session-activity-state').innerText = `Detected (${data.focus_analysis.activity_level})`;
        
        document.getElementById('matrix-status').innerText = `Status: ${data.focus_analysis.status} (${data.focus_analysis.confidence_pct}% Confidence)`;
    }
}

// Helper formatting
function formatSeconds(sec) {
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = Math.floor(sec % 60);
    return `${h.toString().padStart(2,'0')}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
}

// Session Lifecycle Controls
async function startNewSession() {
    try {
        const subject = document.getElementById('session-subject-tag').innerText;
        const task = document.getElementById('session-task-tag').innerText;
        
        const res = await fetch('/api/session/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({subject, task})
        });
        const data = await res.json();
        if (data.success) {
            fetchSystemStatus();
            switchTab('session');
        }
    } catch (err) {
        alert('Failed to start session: ' + err.message);
    }
}

async function togglePauseSession() {
    try {
        const res = await fetch('/api/session/pause', {method: 'POST'});
        const data = await res.json();
        fetchSystemStatus();
    } catch (err) {
        console.error(err);
    }
}

async function endSession() {
    if (!confirm("Are you sure you want to end this study session? Session log will be saved.")) return;
    try {
        const res = await fetch('/api/session/stop', {method: 'POST'});
        const data = await res.json();
        if (data.success) {
            alert("Session complete! Summary saved to " + (data.saved_file || "history"));
            fetchSystemStatus();
            switchTab('dashboard');
        }
    } catch (err) {
        alert('Failed to end session: ' + err.message);
    }
}

// Sensor Mode & Condition Setting
async function setSensorMode(mode) {
    try {
        const res = await fetch('/api/sensor/mode', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({mode})
        });
        const data = await res.json();
        if (data.success) fetchSystemStatus();
    } catch (err) {
        console.error(err);
    }
}

async function setSimulatedCondition(condition) {
    try {
        const res = await fetch('/api/sensor/condition', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({condition})
        });
        const data = await res.json();
        if (data.success) {
            // Highlight active button
            document.querySelectorAll('.condition-btn-grid .btn').forEach(btn => {
                btn.classList.remove('active');
                if (btn.innerText.includes(condition.replace(/_/g, ' '))) btn.classList.add('active');
            });
            fetchSystemStatus();
        }
    } catch (err) {
        console.error(err);
    }
}

// Study Plan Management
async function loadStudyPlan() {
    try {
        const res = await fetch('/api/study-plan');
        const data = await res.json();
        renderTaskList(data.tasks || []);
    } catch (err) {
        console.error(err);
    }
}

function renderTaskList(tasks) {
    const container = document.getElementById('task-list-container');
    if (!container) return;
    
    if (tasks.length === 0) {
        container.innerHTML = '<div class="text-muted text-center py-3">No tasks added yet.</div>';
        return;
    }

    container.innerHTML = tasks.map(t => `
        <div class="task-item">
            <div class="task-item-left">
                <i class="fa-solid ${t.status === 'COMPLETED' ? 'fa-circle-check text-emerald' : (t.status === 'IN_PROGRESS' ? 'fa-spinner text-indigo fa-spin' : 'fa-circle text-dim')} task-status-icon"></i>
                <div class="task-details">
                    <h4>${t.title}</h4>
                    <div class="task-meta">${t.subject} • ${t.completed_minutes}/${t.duration_minutes} mins completed</div>
                </div>
            </div>
            <div class="task-actions">
                ${t.status !== 'COMPLETED' ? `
                    <button class="btn btn-sm btn-primary" onclick="updateTaskState(${t.id}, 'start')"><i class="fa-solid fa-play"></i> Start</button>
                    <button class="btn btn-sm btn-secondary" onclick="updateTaskState(${t.id}, 'complete')"><i class="fa-solid fa-check"></i> Complete</button>
                ` : `<span class="badge badge-success">Completed</span>`}
                <button class="btn btn-sm btn-ghost" onclick="askAICoachAboutTask('${t.subject}', '${t.title}')"><i class="fa-solid fa-robot"></i> Ask AI</button>
            </div>
        </div>
    `).join('');
}

async function updateTaskState(id, action) {
    try {
        const res = await fetch('/api/study-plan/task', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id, action})
        });
        const data = await res.json();
        if (data.success) {
            renderTaskList(data.tasks);
            fetchSystemStatus();
        }
    } catch (err) {
        console.error(err);
    }
}

function showNewTaskModal() {
    document.getElementById('add-task-modal').classList.add('active');
}

function closeAddTaskModal() {
    document.getElementById('add-task-modal').classList.remove('active');
}

async function submitNewTask() {
    const subject = document.getElementById('new-task-subject').value.trim();
    const title = document.getElementById('new-task-title').value.trim();
    const duration = parseInt(document.getElementById('new-task-duration').value) || 30;

    if (!subject || !title) {
        alert("Please provide both subject and task description.");
        return;
    }

    closeAddTaskModal();
    alert("New task saved to study plan!");
    loadStudyPlan();
}

// AI Study Coach Chat Interface
async function sendChatMessage() {
    const inputEl = document.getElementById('coach-user-input');
    const text = inputEl.value.trim();
    if (!text) return;

    inputEl.value = '';
    appendChatMessage('Arun', text, 'user-msg');

    try {
        // Show loading avatar
        const loadingId = appendChatMessage('FlowMate AI Coach', 'Thinking...', 'coach-msg');

        const res = await fetch('/api/coach', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({prompt: text})
        });
        const data = await res.json();
        
        // Remove loading and show response
        const loadingElem = document.getElementById(loadingId);
        if (loadingElem) loadingElem.remove();

        const reply = data.response || data.error || "No response received.";
        appendChatMessage('FlowMate AI Coach', reply, 'coach-msg');
    } catch (err) {
        appendChatMessage('FlowMate AI Coach', 'Connection error: ' + err.message, 'coach-msg');
    }
}

function sendQuickPrompt(promptText) {
    document.getElementById('coach-user-input').value = promptText;
    sendChatMessage();
}

function askAICoachAboutTask(subject, task) {
    switchTab('coach');
    sendQuickPrompt(`Give me key study strategies and practice tips for ${subject}: ${task}`);
}

async function requestMetricCoaching() {
    switchTab('coach');
    appendChatMessage('System', 'Requesting Ollama metric coaching feedback...', 'user-msg');
    try {
        const res = await fetch('/api/coach', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_note: "Dashboard metric check"})
        });
        const data = await res.json();
        appendChatMessage('FlowMate AI Coach', data.response || data.error, 'coach-msg');
    } catch (err) {
        appendChatMessage('FlowMate AI Coach', 'Error: ' + err.message, 'coach-msg');
    }
}

function appendChatMessage(author, text, msgClass) {
    const container = document.getElementById('chat-messages');
    if (!container) return;

    const msgId = 'msg-' + Date.now();
    const timeStr = new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});

    const msgHtml = `
        <div class="chat-msg ${msgClass}" id="${msgId}">
            <div class="msg-avatar"><i class="fa-solid ${msgClass.includes('coach') ? 'fa-robot' : 'fa-user'}"></i></div>
            <div class="msg-body">
                <div class="msg-header">
                    <span class="msg-author">${author}</span>
                    <span class="msg-time">${timeStr}</span>
                </div>
                <div class="msg-text">${text}</div>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', msgHtml);
    container.scrollTop = container.scrollHeight;
    return msgId;
}

// Session History Parser & Modal
async function loadSessionHistory() {
    try {
        const res = await fetch('/api/sessions');
        const data = await res.json();
        const tbody = document.getElementById('history-table-body');
        if (!tbody) return;

        if (!data.sessions || data.sessions.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No saved session files found in <code>data/sessions/</code>.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.sessions.map(s => {
            const dateStr = s.timestamp_start ? new Date(s.timestamp_start * 1000).toLocaleString() : 'N/A';
            return `
                <tr>
                    <td><strong>${s.file_name}</strong></td>
                    <td>${dateStr}</td>
                    <td>${s.duration_formatted}</td>
                    <td><span class="text-emerald font-mono">${s.average_bpm} BPM</span></td>
                    <td>${s.total_readings} samples</td>
                    <td><button class="btn btn-sm btn-secondary" onclick="viewSessionDetail('${s.file_name}')"><i class="fa-solid fa-eye"></i> View</button></td>
                </tr>
            `;
        }).join('');
    } catch (err) {
        console.error(err);
    }
}

async function viewSessionDetail(fileName) {
    try {
        const res = await fetch(`/api/sessions/${fileName}`);
        const result = await res.json();
        if (!result.success) return alert("Could not read file");

        const d = result.data;
        const modalBody = document.getElementById('modal-session-body');
        document.getElementById('modal-session-title').innerText = `Session Log: ${fileName}`;

        modalBody.innerHTML = `
            <div class="disclaimer-chip space-bottom"><i class="fa-solid fa-shield"></i> ${d.disclaimer}</div>
            <div class="metrics-grid space-bottom">
                <div class="metric-card glass-card">
                    <span class="metric-label">DURATION</span>
                    <div class="metric-value" style="font-size: 1.4rem;">${d.duration_seconds} sec</div>
                </div>
                <div class="metric-card glass-card">
                    <span class="metric-label">AVERAGE BPM</span>
                    <div class="metric-value text-emerald" style="font-size: 1.4rem;">${d.average_bpm} BPM</div>
                </div>
                <div class="metric-card glass-card">
                    <span class="metric-label">TOTAL READINGS</span>
                    <div class="metric-value text-cyan" style="font-size: 1.4rem;">${d.total_readings}</div>
                </div>
            </div>
            <h4>Recent Telemetry Samples:</h4>
            <div class="table-responsive space-top">
                <table class="data-table">
                    <thead>
                        <tr><th>Timestamp</th><th>BPM</th><th>Condition</th><th>Device</th></tr>
                    </thead>
                    <tbody>
                        ${(d.readings || []).slice(-10).map(r => `
                            <tr>
                                <td>${new Date(r.timestamp * 1000).toLocaleTimeString()}</td>
                                <td class="font-mono text-emerald">${r.bpm} BPM</td>
                                <td>${r.condition_label}</td>
                                <td>${r.device_name}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        document.getElementById('session-modal').classList.add('active');
    } catch (err) {
        alert("Error loading detail: " + err.message);
    }
}

function closeSessionModal() {
    document.getElementById('session-modal').classList.remove('active');
}

// Notifications Center
async function loadNotifications() {
    try {
        const res = await fetch('/api/notifications');
        const data = await res.json();
        const container = document.getElementById('notifications-list-container');
        if (!container) return;

        const notifs = data.notifications || [];
        const unreadCount = notifs.filter(n => !n.read).length;
        document.getElementById('notif-count-badge').innerText = unreadCount;

        container.innerHTML = notifs.map(n => `
            <div class="notif-item ${n.read ? '' : 'unread'}">
                <div class="notif-icon-col">
                    <i class="fa-solid ${n.category.includes('AI') ? 'fa-robot' : (n.category.includes('Hardware') ? 'fa-microchip' : 'fa-bell')}"></i>
                </div>
                <div class="notif-content-col">
                    <div class="notif-title-row">
                        <span>${n.title} <span class="badge badge-primary">${n.category}</span></span>
                        <span class="notif-time">${new Date(n.timestamp * 1000).toLocaleTimeString()}</span>
                    </div>
                    <div class="notif-msg">${n.message}</div>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error(err);
    }
}

async function markAllNotificationsRead() {
    try {
        await fetch('/api/notifications/read', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id: 'all'})
        });
        loadNotifications();
    } catch (err) {
        console.error(err);
    }
}

// Faculty / Mentor View
async function loadFacultyView() {
    try {
        const res = await fetch('/api/faculty/students');
        const data = await res.json();
        const tbody = document.getElementById('faculty-students-table');
        if (!tbody) return;

        tbody.innerHTML = (data.students || []).map(s => `
            <tr>
                <td><strong>${s.name}</strong></td>
                <td><span class="badge ${s.status === 'STUDYING' ? 'badge-success' : 'badge-warning'}">${s.status}</span></td>
                <td>${s.subject}</td>
                <td>${s.session_minutes} mins</td>
                <td>${s.activity_level}</td>
                <td>${s.today_progress}</td>
                <td>${s.alerts.length > 0 ? s.alerts.map(a => `<span class="badge badge-warning">${a}</span>`).join(' ') : '<span class="text-muted">None</span>'}</td>
            </tr>
        `).join('');
    } catch (err) {
        console.error(err);
    }
}

// Chart.js Real-time Telemetry
function initCharts() {
    // 1. Heart Rate Line Stream Chart
    const hrCtx = document.getElementById('heartRateChart');
    if (hrCtx) {
        heartRateChartInstance = new Chart(hrCtx, {
            type: 'line',
            data: {
                labels: heartRateTimeLabels,
                datasets: [{
                    label: 'Heart Rate (BPM)',
                    data: heartRateDataBuffer,
                    borderColor: '#ec4899',
                    backgroundColor: 'rgba(236, 72, 153, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.35,
                    pointRadius: 4,
                    pointBackgroundColor: '#ec4899'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } },
                    y: { min: 50, max: 120, grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    // 2. Activity & Focus Signals Chart
    const actCtx = document.getElementById('activityChart');
    if (actCtx) {
        activityChartInstance = new Chart(actCtx, {
            type: 'bar',
            data: {
                labels: ['10m ago', '8m ago', '6m ago', '4m ago', '2m ago', 'Now'],
                datasets: [{
                    label: 'Software Focus Index',
                    data: [78, 82, 85, 80, 84, 88],
                    backgroundColor: '#6366f1',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
                    y: { min: 0, max: 100, grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }
}

function updateHeartRateChart(bpm, timestamp) {
    if (!heartRateChartInstance) return;

    const timeLabel = new Date(timestamp * 1000).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit', second: '2-digit'});
    
    heartRateDataBuffer.push(bpm);
    heartRateTimeLabels.push(timeLabel);

    if (heartRateDataBuffer.length > maxChartPoints) {
        heartRateDataBuffer.shift();
        heartRateTimeLabels.shift();
    }

    heartRateChartInstance.update();
}

// User Authentication & Hardware Diagnostics

async function loadCurrentUserProfile() {
    try {
        const res = await fetch('/api/auth/me');
        const data = await res.json();
        if (data.success && data.user) {
            const user = data.user;
            document.getElementById('header-user-name').innerText = user.name;
            document.getElementById('header-user-roll').innerText = `Roll: ${user.roll_no}`;
            document.getElementById('header-user-avatar').innerText = user.name.charAt(0).toUpperCase();
        }
    } catch (err) {
        console.error(err);
    }
}

function showAuthModal() {
    document.getElementById('auth-modal').classList.add('active');
}

function closeAuthModal() {
    document.getElementById('auth-modal').classList.remove('active');
}

function switchAuthTab(tab) {
    if (tab === 'signin') {
        document.getElementById('auth-tab-signin').classList.add('active');
        document.getElementById('auth-tab-register').classList.remove('active');
        document.getElementById('form-signin').style.display = 'block';
        document.getElementById('form-register').style.display = 'none';
        document.getElementById('auth-modal-title').innerText = 'Student & Faculty Sign In';
    } else {
        document.getElementById('auth-tab-register').classList.add('active');
        document.getElementById('auth-tab-signin').classList.remove('active');
        document.getElementById('form-register').style.display = 'block';
        document.getElementById('form-signin').style.display = 'none';
        document.getElementById('auth-modal-title').innerText = 'Register New Student / Faculty';
    }
}

async function submitLogin() {
    const roll_no = document.getElementById('login-roll').value.trim();
    const password = document.getElementById('login-password').value.trim();

    if (!roll_no || !password) return alert("Please enter Roll Number and Password.");

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({roll_no, password})
        });
        const data = await res.json();
        if (data.success) {
            alert(`Welcome back, ${data.user.name}!`);
            closeAuthModal();
            loadCurrentUserProfile();
            fetchSystemStatus();
            loadStudyPlan();
        } else {
            alert(data.error || "Authentication failed.");
        }
    } catch (err) {
        alert("Login error: " + err.message);
    }
}

async function submitRegister() {
    const name = document.getElementById('reg-name').value.trim();
    const roll_no = document.getElementById('reg-roll').value.trim();
    const password = document.getElementById('reg-password').value.trim();
    const role = document.getElementById('reg-role').value;

    if (!name || !roll_no || !password) return alert("Please fill in Name, Roll Number, and Password.");

    try {
        const res = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, roll_no, password, role})
        });
        const data = await res.json();
        if (data.success) {
            alert(`User ${data.user.name} (${data.user.roll_no}) saved to Database successfully!`);
            closeAuthModal();
            loadCurrentUserProfile();
            fetchSystemStatus();
            loadStudyPlan();
        } else {
            alert(data.error || "Registration failed.");
        }
    } catch (err) {
        alert("Registration error: " + err.message);
    }
}

// Hardware Diagnostic Probe
async function runHardwareDiagnostic() {
    const modal = document.getElementById('hardware-diag-modal');
    const body = document.getElementById('hardware-diag-body');
    modal.classList.add('active');
    body.innerHTML = `<div class="text-center py-4"><i class="fa-solid fa-spinner fa-spin text-cyan" style="font-size: 2rem;"></i><div class="space-top">Executing real-time hardware signal quality probe...</div></div>`;

    try {
        const res = await fetch('/api/hardware/diagnostic');
        const data = await res.json();
        if (!data.success) return body.innerHTML = '<div class="text-danger">Diagnostic failed.</div>';

        const d = data.diagnostic;
        body.innerHTML = `
            <div class="metrics-grid space-bottom">
                <div class="metric-card glass-card">
                    <span class="metric-label">HARDWARE STATUS</span>
                    <div class="metric-value text-emerald" style="font-size: 1.2rem;">${d.health_status}</div>
                </div>
                <div class="metric-card glass-card">
                    <span class="metric-label">SIGNAL QUALITY</span>
                    <div class="metric-value text-cyan" style="font-size: 1.2rem;">${d.signal_quality_pct}%</div>
                </div>
                <div class="metric-card glass-card">
                    <span class="metric-label">LATENCY PING</span>
                    <div class="metric-value text-amber" style="font-size: 1.2rem;">${d.latency_ms} ms</div>
                </div>
            </div>
            <h4>Diagnostic Handshake Protocol Log:</h4>
            <div class="signal-matrix space-top">
                ${d.diagnostic_logs.map(log => `<div class="matrix-row"><div class="matrix-content"><strong>${log}</strong></div></div>`).join('')}
            </div>
            <div class="space-top text-center text-muted font-mono" style="font-size: 0.75rem;">
                Sensor: ${d.device_name} • Mode: ${d.sensor_mode} • Timestamp: ${new Date(d.timestamp * 1000).toLocaleTimeString()}
            </div>
        `;
    } catch (err) {
        body.innerHTML = `<div class="text-danger py-4">Error running diagnostic: ${err.message}</div>`;
    }
}

function closeHardwareDiagModal() {
    document.getElementById('hardware-diag-modal').classList.remove('active');
}

