/* ==========================================================================
   FLOWMATE - PROFESSIONAL SPA CONTROLLER & API ADAPTER (VANILLA JS)
   ========================================================================== */

// --- 1. CENTRALIZED API & UTILITY HELPERS ---

const API = {
    async get(endpoint) {
        try {
            const res = await fetch(endpoint);
            if (!res.ok) {
                const errBody = await res.json().catch(() => ({}));
                throw new Error(errBody.error || `HTTP Error ${res.status}`);
            }
            return await res.json();
        } catch (err) {
            console.error(`[API GET ${endpoint}]`, err);
            throw err;
        }
    },

    async post(endpoint, body = {}) {
        try {
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok || data.success === false) {
                throw new Error(data.error || `HTTP Error ${res.status}`);
            }
            return data;
        } catch (err) {
            console.error(`[API POST ${endpoint}]`, err);
            throw err;
        }
    }
};

const Toast = {
    show(message, type = 'info', duration = 3500) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        let icon = 'fa-circle-info';
        if (type === 'success') icon = 'fa-circle-check';
        if (type === 'error') icon = 'fa-triangle-exclamation';
        if (type === 'warning') icon = 'fa-circle-exclamation';

        toast.innerHTML = `<i class="fa-solid ${icon}"></i><span>${escapeHTML(message)}</span>`;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
};

function escapeHTML(str) {
    if (typeof str !== 'string') return '';
    return str.replace(/[&<>'"]/g, tag => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
    }[tag] || tag));
}

function formatSeconds(sec) {
    sec = Math.max(0, Math.floor(sec || 0));
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = Math.floor(sec % 60);
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

// --- 2. GLOBAL APPLICATION STATE STORE ---

const AppState = {
    currentTab: 'dashboard',
    user: null,
    status: null,
    tasks: [],
    notifications: [],
    sensorMode: 'SIMULATION',
    simulatedCondition: 'DEEP_STUDY',
    telemetryInterval: null,
    theme: localStorage.getItem('flowmate_theme') || 'dark',

    // Chart.js Instances
    heartRateChart: null,
    activityChart: null,
    weeklyHoursChart: null,
    subjectPieChart: null,

    // Telemetry Stream Buffers
    hrBuffer: [],
    hrTimeLabels: [],
    maxChartPoints: 20
};

// --- 3. INITIALIZATION & EVEN LISTENERS ---

document.addEventListener('DOMContentLoaded', async () => {
    initTheme();
    initTabNavigation();
    initCharts();
    initModalEvents();

    // Initial Data Fetches
    await loadCurrentUserProfile();
    await fetchSystemStatus();
    await loadStudyPlan();
    await loadNotifications();
    await loadFacultyView();

    // Start Telemetry Stream Polling (every 2 seconds)
    AppState.telemetryInterval = setInterval(fetchTelemetry, 2000);
});

// Theme Management
function initTheme() {
    document.body.className = AppState.theme === 'light' ? 'theme-light' : 'theme-dark';
    updateThemeIcon();
}

function toggleTheme() {
    AppState.theme = AppState.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('flowmate_theme', AppState.theme);
    initTheme();
    Toast.show(`Switched to ${AppState.theme} theme`, 'info', 2000);
}

function updateThemeIcon() {
    const icon = document.getElementById('theme-icon');
    if (icon) {
        icon.className = AppState.theme === 'light' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
    }
}

// Navigation & Tab Switching
function initTabNavigation() {
    const navButtons = document.querySelectorAll('.nav-item, .bottom-nav-item, .nav-link-trigger');
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
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
    AppState.currentTab = tabId;

    // Update Navigation UI
    document.querySelectorAll('.nav-item, .bottom-nav-item').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-tab') === tabId) btn.classList.add('active');
    });

    // Close Mobile Sidebar if open
    const sidebar = document.getElementById('app-sidebar');
    if (sidebar) sidebar.classList.remove('active');

    // Switch Page View
    document.querySelectorAll('.tab-page').forEach(page => page.classList.remove('active'));
    const targetPage = document.getElementById(`tab-${tabId}`);
    if (targetPage) targetPage.classList.add('active');

    // Tab Specific Refreshes
    if (tabId === 'history') loadSessionHistory();
    if (tabId === 'notifications') loadNotifications();
    if (tabId === 'faculty') loadFacultyView();
    if (tabId === 'progress') renderProgressCharts();
    if (tabId === 'plan') loadStudyPlan();
}

// Modal Backdrop & Escape Key Listeners
function initModalEvents() {
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay.active').forEach(modal => modal.classList.remove('active'));
        }
    });
}

// --- 4. AUTHENTICATION & USER PROFILE ---

async function loadCurrentUserProfile() {
    try {
        const data = await API.get('/api/auth/me');
        if (data.success && data.user) {
            AppState.user = data.user;
            updateUserProfileUI(data.user);
        }
    } catch (err) {
        console.warn('Failed to fetch user profile:', err);
    }
}

function updateUserProfileUI(user) {
    if (!user) return;
    document.getElementById('header-user-name').innerText = user.name || 'Student';
    document.getElementById('header-user-roll').innerText = `Roll: ${user.roll_no || 'N/A'}`;
    document.getElementById('header-user-avatar').innerText = (user.name || 'A').charAt(0).toUpperCase();

    // Dynamic Time-of-Day Greeting
    const hour = new Date().getHours();
    let greeting = 'Good evening';
    if (hour < 12) greeting = 'Good morning';
    else if (hour < 17) greeting = 'Good afternoon';

    const greetingTitle = document.getElementById('dash-greeting-title');
    if (greetingTitle) {
        greetingTitle.innerText = `${greeting}, ${escapeHTML(user.name)} 👋`;
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
        document.getElementById('auth-modal-title').innerText = 'Register New Account';
    }
}

async function submitLogin() {
    const roll_no = document.getElementById('login-roll').value.trim();
    const password = document.getElementById('login-password').value.trim();

    if (!roll_no || !password) {
        Toast.show('Please enter both Roll Number and Password', 'warning');
        return;
    }

    try {
        const data = await API.post('/api/auth/login', { roll_no, password });
        if (data.success) {
            Toast.show(`Welcome back, ${data.user.name}!`, 'success');
            closeAuthModal();
            AppState.user = data.user;
            updateUserProfileUI(data.user);
            await fetchSystemStatus();
            await loadStudyPlan();
        }
    } catch (err) {
        Toast.show(err.message || 'Authentication failed', 'error');
    }
}

async function submitRegister() {
    const name = document.getElementById('reg-name').value.trim();
    const roll_no = document.getElementById('reg-roll').value.trim();
    const password = document.getElementById('reg-password').value.trim();
    const role = document.getElementById('reg-role').value;

    if (!name || !roll_no || !password) {
        Toast.show('Please complete all required fields', 'warning');
        return;
    }

    try {
        const data = await API.post('/api/auth/register', { name, roll_no, password, role });
        if (data.success) {
            Toast.show(`User ${data.user.name} registered successfully!`, 'success');
            closeAuthModal();
            AppState.user = data.user;
            updateUserProfileUI(data.user);
            await fetchSystemStatus();
            await loadStudyPlan();
        }
    } catch (err) {
        Toast.show(err.message || 'Registration failed', 'error');
    }
}

async function logoutUser() {
    try {
        await API.post('/api/auth/logout');
        Toast.show('Logged out successfully', 'info');
        closeAuthModal();
        await loadCurrentUserProfile();
        await fetchSystemStatus();
    } catch (err) {
        console.error(err);
    }
}

// --- 5. SYSTEM TELEMETRY & STATUS ENGINE ---

async function fetchSystemStatus() {
    try {
        const data = await API.get('/api/status');
        AppState.status = data;
        updateUIWithStatus(data);
    } catch (err) {
        console.warn('System status fetch failed:', err);
    }
}

async function fetchTelemetry() {
    try {
        const data = await API.get('/api/sensor/read');
        updateHeartRateChart(data.bpm, data.timestamp);
        
        // Background refresh status
        const statusData = await API.get('/api/status');
        AppState.status = statusData;
        updateUIWithStatus(statusData);
    } catch (err) {
        console.warn('Telemetry poll failed:', err);
    }
}

function updateUIWithStatus(data) {
    if (!data) return;

    // 1. Student Goal Progress
    if (data.student) {
        const compMin = data.student.completed_minutes || 0;
        const goalMin = data.student.goal_minutes || 180;
        const pct = Math.min(100, Math.round((compMin / goalMin) * 100));

        const hours = Math.floor(compMin / 60);
        const mins = compMin % 60;
        
        const compEl = document.getElementById('dash-completed-time');
        if (compEl) compEl.innerText = `${hours}h ${mins}m`;

        const subEl = document.getElementById('dash-completed-subtext');
        if (subEl) subEl.innerText = `${pct}% of daily target reached`;

        const barEl = document.getElementById('dash-goal-progress-bar');
        if (barEl) barEl.style.width = `${pct}%`;

        const focusScoreEl = document.getElementById('dash-focus-score');
        if (focusScoreEl) focusScoreEl.innerText = `${data.student.focus_score || 84}%`;

        const streakEl = document.getElementById('dash-streak-days');
        if (streakEl) streakEl.innerText = `${data.student.streak_days || 1} Days`;
    }

    // 2. Session Timer & Active Session Widget
    if (data.session) {
        const elapsedSec = data.session.elapsed_seconds || 0;
        const timeFormatted = formatSeconds(elapsedSec);

        const timerDisplay = document.getElementById('dash-timer-display');
        if (timerDisplay) timerDisplay.innerText = timeFormatted;

        const clockDisplay = document.getElementById('session-clock-display');
        if (clockDisplay) clockDisplay.innerText = timeFormatted;

        const dashSubject = document.getElementById('dash-subject-display');
        if (dashSubject) dashSubject.innerText = data.session.current_subject || 'Mathematics';

        const sessionSubjectTag = document.getElementById('session-subject-tag');
        if (sessionSubjectTag) sessionSubjectTag.innerText = data.session.current_subject || 'Mathematics';

        const dashTask = document.getElementById('dash-task-display');
        if (dashTask) dashTask.innerText = data.session.current_task || 'Calculus - Integration';

        const sessionTaskTag = document.getElementById('session-task-tag');
        if (sessionTaskTag) sessionTaskTag.innerText = data.session.current_task || 'Calculus - Integration';

        const isSessionActive = data.session.active && data.session.state === 'ACTIVE';
        const statusBadge = document.getElementById('dash-session-status-badge');
        if (statusBadge) {
            statusBadge.innerText = isSessionActive ? 'ACTIVE SESSION' : (data.session.state || 'IDLE');
            statusBadge.className = isSessionActive ? 'badge badge-primary' : 'badge badge-secondary';
        }
    }

    // 3. Sensor Status & Source Badges
    if (data.sensor) {
        const modeText = `${data.sensor.mode} MODE`;
        const modeBadge = document.getElementById('dash-sensor-mode');
        if (modeBadge) modeBadge.innerText = modeText;

        const headerText = document.getElementById('header-sensor-text');
        if (headerText) headerText.innerText = `${data.sensor.mode} (${data.sensor.device_name})`;

        const liveBpmText = `${data.sensor.bpm.toFixed(1)} BPM`;
        const dashBpmEl = document.getElementById('dash-live-bpm');
        if (dashBpmEl) dashBpmEl.innerText = liveBpmText;

        const chartLiveBpm = document.getElementById('chart-live-bpm');
        if (chartLiveBpm) chartLiveBpm.innerText = data.sensor.bpm.toFixed(1);

        const matrixBpm = document.getElementById('matrix-bpm');
        if (matrixBpm) matrixBpm.innerText = liveBpmText;

        const matrixDevice = document.getElementById('matrix-device');
        if (matrixDevice) matrixDevice.innerText = `Source: ${data.sensor.device_name}`;

        const hwStatusEl = document.getElementById('dash-hw-status');
        if (hwStatusEl) hwStatusEl.innerText = data.sensor.connected ? 'Hardware Connected' : 'Sensor Disconnected';

        const sessionBpmVal = document.getElementById('session-bpm-val');
        if (sessionBpmVal) sessionBpmVal.innerText = liveBpmText;

        const sessionDeviceSub = document.getElementById('session-device-sub');
        if (sessionDeviceSub) sessionDeviceSub.innerText = data.sensor.device_name;

        // Pulse dot animation trigger
        const pulseDot = document.getElementById('header-pulse-dot');
        if (pulseDot) {
            pulseDot.style.backgroundColor = data.sensor.connected ? 'var(--success)' : 'var(--danger)';
        }
    }

    // 4. Focus Analysis Signals
    if (data.focus_analysis) {
        const focusStatusEl = document.getElementById('session-focus-status');
        if (focusStatusEl) focusStatusEl.innerText = data.focus_analysis.status;

        const confidenceEl = document.getElementById('session-confidence-sub');
        if (confidenceEl) confidenceEl.innerText = `Software Confidence: ${data.focus_analysis.confidence_pct}%`;

        const actStatusEl = document.getElementById('dash-act-status');
        if (actStatusEl) actStatusEl.innerText = `Activity: ${data.focus_analysis.activity_level}`;

        const sessionActEl = document.getElementById('session-activity-state');
        if (sessionActEl) sessionActEl.innerText = `Detected (${data.focus_analysis.activity_level})`;

        const matrixStatus = document.getElementById('matrix-status');
        if (matrixStatus) matrixStatus.innerText = `Status: ${data.focus_analysis.status} (${data.focus_analysis.confidence_pct}% Confidence)`;
    }
}

// --- 6. FOCUS SESSION / POMODORO CONTROLS ---

async function startNewSession() {
    try {
        const subject = document.getElementById('session-subject-tag').innerText;
        const task = document.getElementById('session-task-tag').innerText;

        const data = await API.post('/api/session/start', { subject, task });
        if (data.success) {
            Toast.show('Focus session started! Telemetry tracking active.', 'success');
            await fetchSystemStatus();
            switchTab('session');
        }
    } catch (err) {
        Toast.show(`Failed to start session: ${err.message}`, 'error');
    }
}

async function togglePauseSession() {
    try {
        const data = await API.post('/api/session/pause');
        if (data.success) {
            const newState = data.session_state;
            Toast.show(`Session ${newState === 'PAUSED' ? 'Paused' : 'Resumed'}`, 'info');
            await fetchSystemStatus();
        }
    } catch (err) {
        Toast.show(`Error toggling pause: ${err.message}`, 'error');
    }
}

async function endSession() {
    try {
        const data = await API.post('/api/session/stop');
        if (data.success) {
            Toast.show(`Session completed & saved to history!`, 'success');
            await fetchSystemStatus();
            await loadStudyPlan();
            switchTab('dashboard');
        }
    } catch (err) {
        Toast.show(`Error ending session: ${err.message}`, 'error');
    }
}

function setPomodoroPreset(minutes) {
    AppState.pomodoroTargetMinutes = minutes;
    document.querySelectorAll('.pomodoro-presets-bar .btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.innerText.includes(`${minutes}m`)) btn.classList.add('active');
    });
    Toast.show(`Preset updated to ${minutes}-minute target`, 'info');
}

// --- 7. STUDY PLANNER & TASK MANAGEMENT (CRUD) ---

async function loadStudyPlan() {
    try {
        const data = await API.get('/api/study-plan');
        AppState.tasks = data.tasks || [];
        renderSubjectBreakdown(AppState.tasks);
        filterTasks();
        populateSubjectDropdown(AppState.tasks);
    } catch (err) {
        console.error('Failed to load study plan:', err);
    }
}

function populateSubjectDropdown(tasks) {
    const filterSelect = document.getElementById('task-subject-filter');
    if (!filterSelect) return;

    const subjects = Array.from(new Set(tasks.map(t => t.subject))).filter(Boolean);
    const currentVal = filterSelect.value;

    filterSelect.innerHTML = `<option value="ALL">All Subjects</option>` +
        subjects.map(s => `<option value="${escapeHTML(s)}">${escapeHTML(s)}</option>`).join('');
    
    filterSelect.value = currentVal;
}

function renderSubjectBreakdown(tasks) {
    const container = document.getElementById('subject-progress-cards');
    if (!container) return;

    if (!tasks || tasks.length === 0) {
        container.innerHTML = '';
        return;
    }

    // Group tasks by subject
    const subjectMap = {};
    tasks.forEach(t => {
        const sub = t.subject || 'General';
        if (!subjectMap[sub]) subjectMap[sub] = { completed: 0, total: 0 };
        subjectMap[sub].total += t.duration_minutes || 0;
        subjectMap[sub].completed += t.completed_minutes || 0;
    });

    const icons = {
        'Mathematics': 'fa-calculator text-primary',
        'Physics': 'fa-atom text-info',
        'Programming': 'fa-code text-success',
        'Chemistry': 'fa-flask text-warning'
    };

    container.innerHTML = Object.keys(subjectMap).map(sub => {
        const data = subjectMap[sub];
        const pct = data.total > 0 ? Math.min(100, Math.round((data.completed / data.total) * 100)) : 0;
        const iconClass = icons[sub] || 'fa-book text-primary';

        return `
            <div class="subject-card card">
                <div class="subject-card-header">
                    <span class="subject-name"><i class="fa-solid ${iconClass}"></i> ${escapeHTML(sub)}</span>
                    <span class="subject-pct">${pct}%</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: ${pct}%;"></div>
                </div>
                <div class="subject-subtext">${data.completed} of ${data.total} minutes completed</div>
            </div>
        `;
    }).join('');
}

function filterTasks() {
    const searchVal = (document.getElementById('task-search-input')?.value || '').toLowerCase().trim();
    const subjectVal = document.getElementById('task-subject-filter')?.value || 'ALL';
    const statusVal = document.getElementById('task-status-filter')?.value || 'ALL';

    const filtered = AppState.tasks.filter(t => {
        const matchesSearch = !searchVal || 
            t.title.toLowerCase().includes(searchVal) || 
            t.subject.toLowerCase().includes(searchVal);

        const matchesSubject = subjectVal === 'ALL' || t.subject === subjectVal;
        const matchesStatus = statusVal === 'ALL' || t.status === statusVal;

        return matchesSearch && matchesSubject && matchesStatus;
    });

    renderTaskList(filtered);
    renderDashboardTasksOverview(AppState.tasks);
}

function renderTaskList(tasks) {
    const container = document.getElementById('task-list-container');
    if (!container) return;

    if (!tasks || tasks.length === 0) {
        container.innerHTML = `
            <div class="text-muted text-center py-4">
                <i class="fa-solid fa-clipboard-list" style="font-size: 2rem; margin-bottom: 0.5rem;" class="text-dim"></i>
                <p>No study tasks found. Click "Add New Task" to create one.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = tasks.map(t => {
        const isComp = t.status === 'COMPLETED';
        const isProg = t.status === 'IN_PROGRESS';

        return `
            <div class="task-item">
                <div class="task-item-left">
                    <div class="task-checkbox ${isComp ? 'checked' : ''}" onclick="updateTaskState(${t.id}, '${isComp ? 'pause' : 'complete'}')" title="Toggle completion">
                        ${isComp ? '<i class="fa-solid fa-check" style="font-size: 0.75rem;"></i>' : ''}
                    </div>
                    <div class="task-details">
                        <h4 class="${isComp ? 'completed' : ''}">${escapeHTML(t.title)}</h4>
                        <div class="task-meta">
                            <span class="badge ${isComp ? 'badge-success' : (isProg ? 'badge-primary' : 'badge-secondary')}">${t.status}</span>
                            • ${escapeHTML(t.subject)} • ${t.completed_minutes || 0}/${t.duration_minutes || 30} mins
                        </div>
                    </div>
                </div>
                <div class="task-actions">
                    ${!isComp ? `
                        <button class="btn btn-sm btn-primary" onclick="setTaskAsActiveFocus('${escapeHTML(t.subject)}', '${escapeHTML(t.title)}')" title="Set as Active Focus">
                            <i class="fa-solid fa-play"></i> Focus
                        </button>
                    ` : ''}
                    <button class="btn btn-sm btn-outline" onclick="askAICoachAboutTask('${escapeHTML(t.subject)}', '${escapeHTML(t.title)}')" title="Ask AI Strategy">
                        <i class="fa-solid fa-robot"></i> AI Tips
                    </button>
                    <button class="btn btn-sm btn-ghost text-danger" onclick="updateTaskState(${t.id}, 'delete')" title="Delete Task">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function renderDashboardTasksOverview(tasks) {
    const container = document.getElementById('dash-today-tasks-container');
    if (!container) return;

    if (!tasks || tasks.length === 0) {
        container.innerHTML = `<div class="text-muted text-center py-3">No tasks created yet for today.</div>`;
        return;
    }

    const pending = tasks.slice(0, 4);
    container.innerHTML = pending.map(t => {
        const isComp = t.status === 'COMPLETED';
        return `
            <div class="task-item">
                <div class="task-item-left">
                    <div class="task-checkbox ${isComp ? 'checked' : ''}" onclick="updateTaskState(${t.id}, '${isComp ? 'pause' : 'complete'}')">
                        ${isComp ? '<i class="fa-solid fa-check" style="font-size: 0.75rem;"></i>' : ''}
                    </div>
                    <div class="task-details">
                        <h4 class="${isComp ? 'completed' : ''}">${escapeHTML(t.title)}</h4>
                        <div class="task-meta">${escapeHTML(t.subject)} • ${t.duration_minutes} mins</div>
                    </div>
                </div>
                <div class="task-actions">
                    <button class="btn btn-sm btn-outline" onclick="setTaskAsActiveFocus('${escapeHTML(t.subject)}', '${escapeHTML(t.title)}')">
                        <i class="fa-solid fa-play"></i> Focus
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function openAddTaskModal() {
    document.getElementById('task-form-id').value = '';
    document.getElementById('task-form-title').value = '';
    document.getElementById('task-form-subject').value = 'Mathematics';
    document.getElementById('task-form-duration').value = '45';
    document.getElementById('task-modal-title').innerText = 'Add New Study Task';
    document.getElementById('task-modal').classList.add('active');
}

function closeTaskModal() {
    document.getElementById('task-modal').classList.remove('active');
}

async function submitTaskForm() {
    const title = document.getElementById('task-form-title').value.trim();
    const subject = document.getElementById('task-form-subject').value.trim() || 'General';
    const duration = parseInt(document.getElementById('task-form-duration').value) || 30;

    if (!title) {
        Toast.show('Please enter a task title', 'warning');
        return;
    }

    try {
        const data = await API.post('/api/study-plan/task', {
            action: 'add',
            subject,
            title,
            duration
        });

        if (data.success) {
            Toast.show('Task added to study plan!', 'success');
            closeTaskModal();
            AppState.tasks = data.tasks;
            renderSubjectBreakdown(data.tasks);
            filterTasks();
            await fetchSystemStatus();
        }
    } catch (err) {
        Toast.show(`Failed to add task: ${err.message}`, 'error');
    }
}

async function updateTaskState(id, action) {
    try {
        const data = await API.post('/api/study-plan/task', { id, action });
        if (data.success) {
            Toast.show(`Task ${action === 'complete' ? 'completed' : (action === 'delete' ? 'deleted' : 'updated')}`, 'success');
            AppState.tasks = data.tasks;
            renderSubjectBreakdown(data.tasks);
            filterTasks();
            await fetchSystemStatus();
        }
    } catch (err) {
        Toast.show(`Task action failed: ${err.message}`, 'error');
    }
}

async function setTaskAsActiveFocus(subject, title) {
    try {
        const data = await API.post('/api/session/start', { subject, task: title });
        if (data.success) {
            Toast.show(`Selected "${title}" as active focus task!`, 'success');
            await fetchSystemStatus();
            switchTab('session');
        }
    } catch (err) {
        Toast.show(`Failed to set focus task: ${err.message}`, 'error');
    }
}

// --- 8. AI STUDY COACH & CHAT INTERFACE ---

async function sendChatMessage() {
    const inputEl = document.getElementById('coach-user-input');
    const text = inputEl.value.trim();
    if (!text) return;

    inputEl.value = '';
    const sendBtn = document.getElementById('chat-send-btn');
    if (sendBtn) sendBtn.disabled = true;

    // User Message Bubble
    appendChatMessage(AppState.user ? AppState.user.name : 'Student', text, 'user-msg');

    // Loading Message Bubble
    const loadingId = appendChatMessage('FlowMate AI Coach', 'Thinking...', 'coach-msg');

    try {
        const data = await API.post('/api/coach', { prompt: text });
        
        // Remove loading
        const loadingElem = document.getElementById(loadingId);
        if (loadingElem) loadingElem.remove();

        if (data.success) {
            appendChatMessage('FlowMate AI Coach', data.response, 'coach-msg');
        } else {
            appendChatMessage('FlowMate AI Coach', `⚠ ${data.error}`, 'coach-msg');
        }
    } catch (err) {
        const loadingElem = document.getElementById(loadingId);
        if (loadingElem) loadingElem.remove();

        appendChatMessage('FlowMate AI Coach', `AI service is currently unavailable. Please ensure Ollama is running locally ('ollama serve').`, 'coach-msg');
    } finally {
        if (sendBtn) sendBtn.disabled = false;
    }
}

function sendQuickPrompt(promptText) {
    document.getElementById('coach-user-input').value = promptText;
    sendChatMessage();
}

function askAICoachAboutTask(subject, title) {
    switchTab('coach');
    sendQuickPrompt(`Give me key study strategies and revision tips for ${subject}: ${title}`);
}

async function requestMetricCoaching() {
    switchTab('coach');
    appendChatMessage('System', 'Requesting Ollama metric coaching feedback...', 'user-msg');
    const loadingId = appendChatMessage('FlowMate AI Coach', 'Analyzing telemetry & study metrics...', 'coach-msg');

    try {
        const data = await API.post('/api/coach', { user_note: "Dashboard metric check" });
        const loadingElem = document.getElementById(loadingId);
        if (loadingElem) loadingElem.remove();

        if (data.success) {
            appendChatMessage('FlowMate AI Coach', data.response, 'coach-msg');
        } else {
            appendChatMessage('FlowMate AI Coach', `⚠ ${data.error}`, 'coach-msg');
        }
    } catch (err) {
        const loadingElem = document.getElementById(loadingId);
        if (loadingElem) loadingElem.remove();

        appendChatMessage('FlowMate AI Coach', 'AI service is currently unavailable. Please make sure Ollama is running.', 'coach-msg');
    }
}

function appendChatMessage(author, text, msgClass) {
    const container = document.getElementById('chat-messages');
    if (!container) return;

    const msgId = 'msg-' + Date.now();
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const msgHtml = `
        <div class="chat-msg ${msgClass}" id="${msgId}">
            <div class="msg-avatar"><i class="fa-solid ${msgClass.includes('coach') ? 'fa-robot' : 'fa-user'}"></i></div>
            <div class="msg-body">
                <div class="msg-header">
                    <span class="msg-author">${escapeHTML(author)}</span>
                    <span class="msg-time">${timeStr}</span>
                </div>
                <div class="msg-text">${escapeHTML(text)}</div>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', msgHtml);
    container.scrollTop = container.scrollHeight;
    return msgId;
}

// --- 9. TELEMETRY & SENSOR CONFIGURATION ---

async function setSensorMode(mode) {
    try {
        const data = await API.post('/api/sensor/mode', { mode });
        if (data.success) {
            Toast.show(`Sensor source set to ${mode}`, 'info');
            AppState.sensorMode = mode;
            
            // Highlight Mode Buttons in Settings & Monitor
            document.querySelectorAll('.mode-selector-group .btn').forEach(btn => {
                btn.classList.remove('active');
                if (btn.innerText.includes(mode)) btn.classList.add('active');
            });
            await fetchSystemStatus();
        }
    } catch (err) {
        Toast.show(`Failed to set sensor mode: ${err.message}`, 'error');
    }
}

async function setSimulatedCondition(condition) {
    try {
        const data = await API.post('/api/sensor/condition', { condition });
        if (data.success) {
            Toast.show(`Simulated condition profile set to ${condition.replace(/_/g, ' ')}`, 'info');
            AppState.simulatedCondition = condition;

            document.querySelectorAll('.condition-btn-grid .btn').forEach(btn => {
                btn.classList.remove('active');
                if (btn.innerText.includes(condition.replace(/_/g, ' '))) btn.classList.add('active');
            });
            await fetchSystemStatus();
        }
    } catch (err) {
        Toast.show(`Failed to set condition: ${err.message}`, 'error');
    }
}

async function runHardwareDiagnostic() {
    const modal = document.getElementById('hardware-diag-modal');
    const body = document.getElementById('hardware-diag-body');
    if (!modal || !body) return;

    modal.classList.add('active');
    body.innerHTML = `
        <div class="text-center py-4">
            <i class="fa-solid fa-spinner fa-spin text-primary" style="font-size: 2rem;"></i>
            <div class="space-top text-muted">Probing hardware sensor signal quality &amp; BLE latency...</div>
        </div>
    `;

    try {
        const data = await API.get('/api/hardware/diagnostic');
        if (data.success && data.diagnostic) {
            const d = data.diagnostic;
            body.innerHTML = `
                <div class="metrics-grid space-bottom">
                    <div class="metric-card">
                        <span class="metric-label">STATUS</span>
                        <div class="metric-value text-success" style="font-size: 1.1rem;">${escapeHTML(d.health_status)}</div>
                    </div>
                    <div class="metric-card">
                        <span class="metric-label">SIGNAL QUALITY</span>
                        <div class="metric-value text-info" style="font-size: 1.1rem;">${d.signal_quality_pct}%</div>
                    </div>
                    <div class="metric-card">
                        <span class="metric-label">PING LATENCY</span>
                        <div class="metric-value text-warning" style="font-size: 1.1rem;">${d.latency_ms} ms</div>
                    </div>
                </div>
                <h4>Diagnostic Log Trace:</h4>
                <div class="signal-matrix space-top">
                    ${(d.diagnostic_logs || []).map(log => `
                        <div class="matrix-row">
                            <div class="matrix-content"><strong>${escapeHTML(log)}</strong></div>
                        </div>
                    `).join('')}
                </div>
                <div class="space-top text-center text-muted font-mono" style="font-size: 0.75rem;">
                    Device: ${escapeHTML(d.device_name)} • Mode: ${escapeHTML(d.sensor_mode)} • Time: ${new Date(d.timestamp * 1000).toLocaleTimeString()}
                </div>
            `;
        }
    } catch (err) {
        body.innerHTML = `<div class="text-danger py-4">Diagnostic probe error: ${escapeHTML(err.message)}</div>`;
    }
}

function closeHardwareDiagModal() {
    document.getElementById('hardware-diag-modal').classList.remove('active');
}

// --- 10. PROGRESS ANALYTICS & CHART.JS ---

function initCharts() {
    // 1. Heart Rate Line Stream Chart
    const hrCtx = document.getElementById('heartRateChart');
    if (hrCtx) {
        AppState.heartRateChart = new Chart(hrCtx, {
            type: 'line',
            data: {
                labels: AppState.hrTimeLabels,
                datasets: [{
                    label: 'Heart Rate (BPM)',
                    data: AppState.hrBuffer,
                    borderColor: '#f43f5e',
                    backgroundColor: 'rgba(244, 63, 94, 0.1)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 3.5,
                    pointBackgroundColor: '#f43f5e'
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

    // 2. Software Focus Index Bar Chart
    const actCtx = document.getElementById('activityChart');
    if (actCtx) {
        AppState.activityChart = new Chart(actCtx, {
            type: 'bar',
            data: {
                labels: ['10m ago', '8m ago', '6m ago', '4m ago', '2m ago', 'Now'],
                datasets: [{
                    label: 'Focus Index',
                    data: [76, 82, 85, 80, 84, 88],
                    backgroundColor: '#6366f1',
                    borderRadius: 4
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
    if (!AppState.heartRateChart) return;

    const timeLabel = new Date(timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    AppState.hrBuffer.push(bpm);
    AppState.hrTimeLabels.push(timeLabel);

    if (AppState.hrBuffer.length > AppState.maxChartPoints) {
        AppState.hrBuffer.shift();
        AppState.hrTimeLabels.shift();
    }

    AppState.heartRateChart.update();
}

async function renderProgressCharts() {
    try {
        const data = await API.get('/api/progress');
        
        // Update Metrics Cards
        if (data.summary) {
            document.getElementById('prog-total-hours').innerText = `${data.summary.total_weekly_hours} hrs`;
            document.getElementById('prog-avg-focus').innerText = `${data.summary.avg_focus_score}%`;
            document.getElementById('prog-completed-tasks').innerText = data.summary.completed_tasks;
            document.getElementById('prog-streak-days').innerText = `${data.summary.streak_days} Days`;
        }

        // 1. Weekly Study Hours Chart
        const hoursCtx = document.getElementById('weeklyHoursChart');
        if (hoursCtx && data.weekly_study_hours) {
            if (AppState.weeklyHoursChart) AppState.weeklyHoursChart.destroy();
            
            AppState.weeklyHoursChart = new Chart(hoursCtx, {
                type: 'bar',
                data: {
                    labels: data.weekly_study_hours.map(d => d.day),
                    datasets: [{
                        label: 'Study Hours',
                        data: data.weekly_study_hours.map(d => d.hours),
                        backgroundColor: '#6366f1',
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
                        y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        }

        // 2. Subject Distribution Pie Chart
        const pieCtx = document.getElementById('subjectPieChart');
        if (pieCtx && data.subject_distribution) {
            if (AppState.subjectPieChart) AppState.subjectPieChart.destroy();

            AppState.subjectPieChart = new Chart(pieCtx, {
                type: 'doughnut',
                data: {
                    labels: data.subject_distribution.map(s => s.subject),
                    datasets: [{
                        data: data.subject_distribution.map(s => s.pct),
                        backgroundColor: ['#6366f1', '#06b6d4', '#10b981', '#f59e0b']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right', labels: { color: '#94a3b8' } }
                    }
                }
            });
        }
    } catch (err) {
        console.error('Failed to render progress charts:', err);
    }
}

// --- 11. SESSION HISTORY & NOTIFICATIONS ---

async function loadSessionHistory() {
    const tbody = document.getElementById('history-table-body');
    if (!tbody) return;

    try {
        const data = await API.get('/api/sessions');
        const sessions = data.sessions || [];

        if (sessions.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No saved study session logs found.</td></tr>`;
            return;
        }

        tbody.innerHTML = sessions.map(s => {
            const dateStr = s.timestamp_start ? new Date(s.timestamp_start * 1000).toLocaleString() : 'N/A';
            return `
                <tr>
                    <td><strong>${escapeHTML(s.file_name)}</strong></td>
                    <td>${dateStr}</td>
                    <td>${s.duration_formatted}</td>
                    <td><span class="font-mono text-success">${s.average_bpm} BPM</span></td>
                    <td>${s.total_readings} readings</td>
                    <td>
                        <button class="btn btn-sm btn-outline" onclick="viewSessionDetail('${escapeHTML(s.file_name)}')">
                            <i class="fa-solid fa-eye"></i> View Detail
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-danger">Failed to load session history.</td></tr>`;
    }
}

async function viewSessionDetail(fileName) {
    const modal = document.getElementById('session-modal');
    const body = document.getElementById('modal-session-body');
    if (!modal || !body) return;

    try {
        const data = await API.get(`/api/sessions/${fileName}`);
        if (!data.success) throw new Error('File unreadable');

        const d = data.data;
        document.getElementById('modal-session-title').innerText = `Session Log: ${fileName}`;

        body.innerHTML = `
            <div class="disclaimer-chip space-bottom"><i class="fa-solid fa-shield"></i> ${escapeHTML(d.disclaimer)}</div>
            <div class="metrics-grid space-bottom">
                <div class="metric-card">
                    <span class="metric-label">DURATION</span>
                    <div class="metric-value" style="font-size: 1.3rem;">${d.duration_seconds} sec</div>
                </div>
                <div class="metric-card">
                    <span class="metric-label">AVERAGE BPM</span>
                    <div class="metric-value text-success" style="font-size: 1.3rem;">${d.average_bpm} BPM</div>
                </div>
                <div class="metric-card">
                    <span class="metric-label">SAMPLES</span>
                    <div class="metric-value text-info" style="font-size: 1.3rem;">${d.total_readings}</div>
                </div>
            </div>
            <h4>Recent Sensor Telemetry Samples:</h4>
            <div class="table-responsive space-top">
                <table class="data-table">
                    <thead>
                        <tr><th>Timestamp</th><th>BPM</th><th>Condition</th><th>Device</th></tr>
                    </thead>
                    <tbody>
                        ${(d.readings || []).slice(-10).map(r => `
                            <tr>
                                <td>${new Date(r.timestamp * 1000).toLocaleTimeString()}</td>
                                <td class="font-mono text-success">${r.bpm} BPM</td>
                                <td>${escapeHTML(r.condition_label)}</td>
                                <td>${escapeHTML(r.device_name)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        modal.classList.add('active');
    } catch (err) {
        Toast.show(`Could not load session details: ${err.message}`, 'error');
    }
}

function closeSessionModal() {
    document.getElementById('session-modal').classList.remove('active');
}

async function loadNotifications() {
    const container = document.getElementById('notifications-list-container');
    if (!container) return;

    try {
        const data = await API.get('/api/notifications');
        const notifs = data.notifications || [];
        AppState.notifications = notifs;

        const unread = notifs.filter(n => !n.read).length;
        const badge = document.getElementById('notif-count-badge');
        if (badge) badge.innerText = unread;

        if (notifs.length === 0) {
            container.innerHTML = `<div class="text-muted text-center py-4">No notifications present.</div>`;
            return;
        }

        container.innerHTML = notifs.map(n => `
            <div class="notif-item ${n.read ? '' : 'unread'}">
                <div class="notif-icon-col">
                    <i class="fa-solid ${n.category.includes('AI') ? 'fa-robot' : (n.category.includes('Hardware') ? 'fa-microchip' : 'fa-bell')}"></i>
                </div>
                <div class="notif-content-col">
                    <div class="notif-title-row">
                        <span>${escapeHTML(n.title)} <span class="badge badge-primary">${escapeHTML(n.category)}</span></span>
                        <span class="notif-time">${new Date(n.timestamp * 1000).toLocaleTimeString()}</span>
                    </div>
                    <div class="notif-msg">${escapeHTML(n.message)}</div>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error('Failed to load notifications:', err);
    }
}

async function markAllNotificationsRead() {
    try {
        await API.post('/api/notifications/read', { id: 'all' });
        Toast.show('All notifications marked as read', 'info');
        await loadNotifications();
    } catch (err) {
        Toast.show('Failed to mark notifications read', 'error');
    }
}

async function loadFacultyView() {
    const tbody = document.getElementById('faculty-students-table');
    if (!tbody) return;

    try {
        const data = await API.get('/api/faculty/students');
        const students = data.students || [];

        const cohortBadge = document.getElementById('faculty-cohort-count');
        if (cohortBadge) cohortBadge.innerText = `${students.length} Active Students`;

        tbody.innerHTML = students.map(s => `
            <tr>
                <td><strong>${escapeHTML(s.name)}</strong></td>
                <td>${escapeHTML(s.roll_no)}</td>
                <td><span class="badge ${s.status === 'STUDYING' ? 'badge-success' : 'badge-warning'}">${escapeHTML(s.status)}</span></td>
                <td>${escapeHTML(s.subject)}</td>
                <td>${s.session_minutes} mins</td>
                <td>${escapeHTML(s.today_progress)}</td>
                <td>
                    ${s.alerts.length > 0 ? s.alerts.map(a => `<span class="badge badge-warning">${escapeHTML(a)}</span>`).join(' ') : '<span class="text-muted">None</span>'}
                </td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger">Failed to load cohort data.</td></tr>`;
    }
}

// --- 12. CAMERA FEED MANAGER ---

const CameraManager = {
    active: false,
    source: 'SERVER',
    webcamStream: null,
    statusPollInterval: null,

    getElements() {
        return {
            mjpegImg:    document.getElementById('camera-mjpeg-stream'),
            webcamVideo: document.getElementById('camera-webcam-video'),
            placeholder: document.getElementById('camera-placeholder-overlay'),
            toggleBtn:   document.getElementById('btn-toggle-camera'),
            badge:       document.getElementById('camera-status-badge'),
            postureText: document.getElementById('camera-posture-text'),
            faceSub:     document.getElementById('camera-face-sub'),
            gazeText:    document.getElementById('camera-gaze-text'),
        };
    },

    async toggle() {
        if (this.active) {
            await this.stop();
        } else {
            await this.start();
        }
    },

    async start() {
        const els = this.getElements();
        this.source = document.getElementById('camera-source-select')?.value || 'SERVER';
        if (this.source === 'SERVER') {
            await this._startServerStream(els);
        } else {
            await this._startWebcamStream(els);
        }
    },

    async _startServerStream(els) {
        try {
            const data = await API.post('/api/camera/toggle', { enable: true });
            if (!data.success) {
                Toast.show('Server camera could not start. Check webcam connection.', 'error');
                return;
            }
            this.active = true;
            if (els.mjpegImg) {
                els.mjpegImg.onerror = () => {
                    if (!this.active) return;
                    Toast.show('Camera stream interrupted.', 'warning');
                    this.stop();
                };
                els.mjpegImg.src = '/api/camera/stream?t=' + Date.now();
                els.mjpegImg.style.display = 'block';
            }
            if (els.webcamVideo)  els.webcamVideo.style.display  = 'none';
            if (els.placeholder)  els.placeholder.style.display  = 'none';
            this._updateUI(els, true, 'ACTIVE (OpenCV)');
            this._startStatusPolling();
            Toast.show('Camera feed started successfully.', 'success');
        } catch (err) {
            Toast.show('Failed to start camera: ' + err.message, 'error');
        }
    },

    async _startWebcamStream(els) {
        try {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                Toast.show('Your browser does not support camera access.', 'error');
                return;
            }
            this.webcamStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            if (els.webcamVideo) {
                els.webcamVideo.srcObject = this.webcamStream;
                els.webcamVideo.style.display = 'block';
            }
            if (els.mjpegImg) {
                els.mjpegImg.onerror = null;
                els.mjpegImg.style.display = 'none';
                els.mjpegImg.src = '';
            }
            if (els.placeholder) els.placeholder.style.display = 'none';
            this.active = true;
            this._updateUI(els, true, 'ACTIVE (HTML5)');
            if (els.postureText) els.postureText.innerText = 'VISION COMPANION ACTIVE';
            if (els.faceSub)     els.faceSub.innerText     = 'HTML5 WebCam — Local Capture';
            Toast.show('Camera feed started via browser HTML5 WebCam.', 'success');
        } catch (err) {
            if (err.name === 'NotAllowedError') {
                Toast.show('Camera permission denied. Allow access in browser settings.', 'error');
            } else if (err.name === 'NotFoundError') {
                Toast.show('No camera device found on this computer.', 'error');
            } else {
                Toast.show('Camera error: ' + err.message, 'error');
            }
        }
    },

    async stop() {
        const els = this.getElements();
        this.active = false;
        this._stopStatusPolling();

        if (els.mjpegImg) {
            els.mjpegImg.onerror = null;
            els.mjpegImg.style.display = 'none';
            els.mjpegImg.src = '';
        }
        if (this.webcamStream) {
            this.webcamStream.getTracks().forEach(t => t.stop());
            this.webcamStream = null;
        }
        if (els.webcamVideo) {
            els.webcamVideo.style.display = 'none';
            els.webcamVideo.srcObject = null;
        }
        if (els.placeholder) els.placeholder.style.display = 'flex';

        try { await API.post('/api/camera/toggle', { enable: false }); } catch (e) { console.warn(e); }

        this._updateUI(els, false, 'OFFLINE');
        if (els.faceSub)  els.faceSub.innerText = 'Face Detection Idle';
        if (els.gazeText) { els.gazeText.innerText = 'STABLE'; els.gazeText.className = 'pill-value text-success'; }
        Toast.show('Camera feed stopped.', 'info');
    },

    _updateUI(els, active, label) {
        if (els.toggleBtn) {
            els.toggleBtn.innerHTML = active
                ? '<i class="fa-solid fa-video-slash"></i> Stop Camera'
                : '<i class="fa-solid fa-video"></i> Start Camera Feed';
            els.toggleBtn.className = active ? 'btn btn-sm btn-danger' : 'btn btn-sm btn-primary';
        }
        if (els.badge) {
            els.badge.innerText = active ? 'Camera Active' : 'Camera Inactive';
            els.badge.className = active ? 'badge badge-success' : 'badge badge-secondary';
        }
        if (els.postureText) els.postureText.innerText = label;
    },

    _startStatusPolling() {
        this._stopStatusPolling();
        this.statusPollInterval = setInterval(() => this._pollStatus(), 2000);
    },

    _stopStatusPolling() {
        if (this.statusPollInterval) { clearInterval(this.statusPollInterval); this.statusPollInterval = null; }
    },

    async _pollStatus() {
        if (!this.active || this.source !== 'SERVER') return;
        try {
            const data = await API.get('/api/camera/status');
            if (data.success && data.camera) {
                const cam = data.camera;
                const els = this.getElements();

                if (els.postureText) {
                    els.postureText.innerText = cam.posture_label || 'DETECTING...';
                    const isWarn = (cam.posture_label || '').includes('WARNING');
                    els.postureText.className = 'pill-value ' + (isWarn ? 'text-danger' : (cam.face_detected ? 'text-success' : 'text-warning'));
                }

                if (els.faceSub) {
                    if ((cam.posture_label || '').includes('EYES CLOSED')) {
                        els.faceSub.innerText = '⚠ Alert: Eyes Closed / Drowsiness Detected!';
                    } else if ((cam.posture_label || '').includes('TURNED AWAY')) {
                        els.faceSub.innerText = '⚠ Alert: Head Turned Away From Screen!';
                    } else if ((cam.posture_label || '').includes('LOOKING DOWN')) {
                        els.faceSub.innerText = '⚠ Alert: Looking Down / Mobile Device Use!';
                    } else if (cam.face_detected) {
                        els.faceSub.innerText = 'Face Detected — Upright Study Posture';
                    } else {
                        els.faceSub.innerText = '⚠ No Face Detected — Check Posture';
                    }
                }

                if (els.gazeText) {
                    const isWarn = (cam.posture_label || '').includes('WARNING');
                    els.gazeText.innerText = isWarn ? 'DISTRACTED' : (cam.face_detected ? 'ALIGNED' : 'AWAY');
                    els.gazeText.className = 'pill-value ' + (isWarn ? 'text-danger' : (cam.face_detected ? 'text-success' : 'text-warning'));
                }

                // Popup Toast Warning if distraction alert occurs
                if (cam.alert && cam.alert !== 'NORMAL' && cam.alert !== 'STOPPED' && cam.alert !== 'OFFLINE') {
                    if (!this.lastAlertShown || (Date.now() - this.lastAlertShown) > 6000) {
                        this.lastAlertShown = Date.now();
                        Toast.show(`Focus Alert: ${cam.posture_label}`, 'warning', 4000);
                    }
                }
            }
        } catch (err) {
            console.warn('[Camera] Status poll failed:', err);
        }
    }
};

// Wrapper functions called from HTML onclick attributes
function toggleCameraFeed() { CameraManager.toggle(); }

function switchCameraSource() {
    if (CameraManager.active) {
        CameraManager.stop().then(() => setTimeout(() => CameraManager.start(), 400));
    }
}

