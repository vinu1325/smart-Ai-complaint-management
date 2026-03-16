const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? `http://${window.location.hostname}:5000` 
    : window.location.origin;
let currentUser = null;
let currentView = 'dashboard';
let currentLang = localStorage.getItem('vinu_lang') || 'en';

const translations = {
    en: {
        login: "Login",
        join_now: "Join Now",
        hero_title: "Citizen Empowerment Through AI",
        hero_subtitle: "Submit complaints, track resolutions in real-time, and let our AI handle classification, prioritization, and routing — instantly.",
        file_complaint: "File a Complaint",
        lodge_complaint: "Lodge New Complaint",
        comp_title: "Complaint Title",
        placeholder_summary: "Short summary...",
        location: "Location",
        placeholder_location: "Street Name / Area...",
        attachment: "Attachment",
        comp_desc: "Description (AI will auto-categorize this)",
        placeholder_desc: "Detailed explanation of the issue...",
        btn_submit: "Submit To AI Engine",
        user_name: "User",
        mobile: "Mobile",
        description: "Description",
        category: "Category",
        priority: "Priority",
        sla: "SLA Countdown",
        status: "Status",
        action: "Action"
    },
    ta: {
        login: "உள்நுழைக",
        join_now: "இப்போதே சேருங்கள்",
        hero_title: "AI மூலம் குடிமக்கள் அதிகாரமளித்தல்",
        hero_subtitle: "புகார்களைச் சமர்ப்பிக்கவும், நிகழ்நேரத்தில் தீர்வுகளைக் கண்காணிக்கவும், மேலும் வகைப்படுத்துதல் மற்றும் முன்னுரிமை அளிப்பதை எங்கள் AI கையாளட்டும்.",
        file_complaint: "புகார் அளிக்கவும்",
        lodge_complaint: "புதிய புகாரைப் பதிவு செய்யவும்",
        comp_title: "புகார் தலைப்பு",
        placeholder_summary: "சுருக்கமான விவரம்...",
        location: "இடம்",
        placeholder_location: "தெருப் பெயர் / பகுதி...",
        attachment: "இணைப்பு",
        comp_desc: "விளக்கம் (AI இதைப் பிரித்தறியும்)",
        placeholder_desc: "பிரச்சனை பற்றிய விரிவான விளக்கம்...",
        btn_submit: "AI இயந்திரத்திடம் சமர்ப்பிக்கவும்",
        user_name: "பயனர்",
        mobile: "கைபேசி எண்",
        description: "விவரம்",
        category: "வகை",
        priority: "முன்னுரிமை",
        sla: "காலக்கெடு",
        status: "நிலை",
        action: "நடவடிக்கை"
    }
};

const changeLanguage = (lang) => {
    currentLang = lang;
    localStorage.setItem('vinu_lang', lang);
    
    // Update active state of buttons
    document.querySelectorAll('.btn-lang').forEach(btn => {
        btn.classList.toggle('active', btn.innerText.toLowerCase() === lang);
    });

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[lang][key]) {
            // Keep icons if present
            const icon = el.querySelector('i');
            el.innerText = translations[lang][key];
            if (icon) el.prepend(icon);
        }
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (translations[lang][key]) {
            el.placeholder = translations[lang][key];
        }
    });
};

// --- UI Helpers ---
const $ = (id) => document.getElementById(id);
const hideLoader = () => $('loading').classList.remove('active');
const showLoader = () => $('loading').classList.add('active');

const formatRemainingTime = (deadline, status, createdAt, updatedAt) => {
    if (status === 'Resolved') {
        const start = new Date(createdAt);
        const end = new Date(updatedAt || new Date());
        const diffMs = end - start;
        const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
        const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        return `<span class="badge low">Fixed in ${diffHrs}h ${diffMins}m</span>`;
    }
    
    const now = new Date();
    const target = new Date(deadline);
    const diffMs = target - now;
    
    if (diffMs <= 0) return '<span class="badge high">Overdue</span>';
    
    const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    return `<span class="countdown-text">${diffHrs}h ${diffMins}m left</span>`;
};

// --- Auth Handling ---
const handleAuth = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    const isRegister = $('tab-register').classList.contains('active');
    
    showLoader();
    try {
        const endpoint = isRegister ? '/register' : '/login';
        const res = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        
        if (res.ok) {
            localStorage.setItem('vinu_token', result.token);
            localStorage.setItem('vinu_user', JSON.stringify(result));
            initApp();
        } else {
            alert(result.message);
        }
    } catch (err) {
        alert("Server connection failed!");
    }
    hideLoader();
};

const switchAuthTab = (tab) => {
    if (tab === 'login') {
        $('tab-login').classList.add('active');
        $('tab-register').classList.remove('active');
        $('name-field').style.display = 'none';
        $('phone-field').style.display = 'none';
        $('role-field').style.display = 'none';
        $('dept-field').style.display = 'none';
        $('auth-btn').innerText = 'Sign In';
    } else {
        $('tab-register').classList.add('active');
        $('tab-login').classList.remove('active');
        $('name-field').style.display = 'block';
        $('phone-field').style.display = 'block';
        $('role-field').style.display = 'block';
        $('auth-btn').innerText = 'Create Account';
    }
};

// --- View Navigation ---
const switchView = (view) => {
    document.querySelectorAll('.content-view').forEach(v => v.style.display = 'none');
    $(`view-${view}`).style.display = 'block';
    $('view-title').innerText = view.replace('-', ' ').toUpperCase();
    
    document.querySelectorAll('.nav-links li').forEach(li => {
        li.classList.toggle('active', li.dataset.view === view);
    });
    
    if (view === 'dashboard') loadDashboardData();
    if (view === 'analytics' && currentUser.role === 'admin') loadAnalytics();
};

// --- App Initialization ---
const initApp = () => {
    changeLanguage(currentLang);
    const userString = localStorage.getItem('vinu_user');
    if (!userString) {
        $('landing-page').style.display = 'block';
        $('auth-page').style.display = 'none';
        $('main-app').style.display = 'none';
        hideLoader();
        return;
    }
    
    currentUser = JSON.parse(userString);
    $('landing-page').style.display = 'none';
    $('auth-page').style.display = 'none';
    $('main-app').style.display = 'flex';
    $('user-display-name').innerText = currentUser.name;
    document.querySelector('.avatar').innerText = currentUser.name[0];
    
    // Role based UI
    document.body.className = `${currentUser.role}-theme`;
    document.querySelectorAll('.user-only').forEach(el => el.style.display = currentUser.role === 'user' ? 'flex' : 'none');
    document.querySelectorAll('.admin-only').forEach(el => el.style.display = currentUser.role === 'admin' ? 'flex' : 'none');
    
    switchView('dashboard');
    changeLanguage(currentLang);
    fetchNotifications();
    setInterval(fetchNotifications, 10000); // Check every 10s
    setTimeout(hideLoader, 500);
};

// --- Data Methods ---
const loadDashboardData = async () => {
    const token = localStorage.getItem('vinu_token');
    try {
        const res = await fetch(`${API_URL}/complaints`, {
            headers: { 'Authorization': token }
        });
        const complaints = await res.json();
        
        $('stat-total').innerText = complaints.length;
        $('stat-pending').innerText = complaints.filter(c => c.status === 'Pending').length;
        $('stat-resolved').innerText = complaints.filter(c => c.status === 'Resolved').length;
        
        const tbody = document.querySelector('#complaints-table tbody');
        tbody.innerHTML = complaints.map((c, i) => {
            let actionHtml = '';
            if (currentUser.role === 'admin') {
                actionHtml = `<div class="badge-received"><i class="fas fa-satellite-dish"></i> Complaint Received</div>`;
            } else if (currentUser.role === 'officer') {
                actionHtml = `<select class="inline-select" onchange="updateStatus('${c._id}', this.value)">
                    <option value="Pending" ${c.status === 'Pending' ? 'selected' : ''}>Pending</option>
                    <option value="In Progress" ${c.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                    <option value="Resolved" ${c.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
                   </select>`;
            } else {
                actionHtml = `<div class="user-action-cell">
                    <button class="btn-small" onclick="viewDetails('${c._id}')">Complaint Submitted</button>
                    ${c.viewed_by_officer ? '<span class="viewed-tag"><i class="fas fa-check-double"></i> Viewed</span>' : ''}
                   </div>`;
            }

            return `
            <tr>
                <td>${i + 1}</td>
                <td>${c.title}</td>
                <td>${c.category}</td>
                <td class="admin-officer-only">${c.user_name || 'N/A'}</td>
                <td class="admin-officer-only">${c.user_phone || 'N/A'}</td>
                <td class="admin-officer-only" title="${c.description}">${c.description.substring(0, 30)}${c.description.length > 30 ? '...' : ''}</td>
                <td><span class="badge ${c.priority.toLowerCase()}">${c.priority}</span></td>
                <td>${formatRemainingTime(c.deadline, c.status, c.created_at, c.updated_at)}</td>
                <td><span class="status-${c.status.toLowerCase().replace(' ', '-')}">${c.status}</span></td>
                <td>${actionHtml}</td>
            </tr>
            `;
        }).join('');
    } catch (err) { console.error(err); }
};

const handleComplaintSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('vinu_token');
    const formData = new FormData(e.target);
    
    showLoader();
    try {
        const res = await fetch(`${API_URL}/complaints`, {
            method: 'POST',
            headers: { 'Authorization': token },
            body: formData
        });
        const result = await res.json();
        if (res.ok) {
            alert(result.message);
            switchView('dashboard');
            e.target.reset();
        } else {
            alert(result.message);
        }
    } catch (err) { alert("Submission failed!"); }
    hideLoader();
};

const viewDetails = async (id) => {
    const token = localStorage.getItem('vinu_token');
    
    // Mark as viewed if officer/admin
    if (currentUser.role === 'officer' || currentUser.role === 'admin') {
        fetch(`${API_URL}/complaints/${id}/viewed`, {
            method: 'PATCH',
            headers: { 'Authorization': token }
        });
    }

    const res = await fetch(`${API_URL}/complaints`, { headers: { 'Authorization': token } });
    const complaints = await res.json();
    const c = complaints.find(item => item._id === id);
    
    $('modal-title').innerText = c.title;
    $('modal-desc').innerText = c.description;
    $('modal-loc').innerText = c.location;
    $('modal-deadline').innerText = new Date(c.deadline).toLocaleString();
    
    if (c.image_path) {
        $('modal-img').src = `${API_URL}/uploads/${c.image_path}`;
        $('modal-img').style.display = 'block';
    } else {
        $('modal-img').style.display = 'none';
    }
    
    if (currentUser.role === 'officer' || currentUser.role === 'admin') {
        document.querySelector('.officer-actions').style.display = 'block';
        $('update-status-val').value = c.status;
        $('save-status-btn').onclick = () => updateStatus(id, $('update-status-val').value);
    } else {
        document.querySelector('.officer-actions').style.display = 'none';
    }
    
    $('complaint-modal').style.display = 'block';
};

const updateStatus = async (id, status) => {
    const token = localStorage.getItem('vinu_token');
    const res = await fetch(`${API_URL}/complaints/${id}/status`, {
        method: 'PATCH',
        headers: { 'Authorization': token, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
    });
    if (res.ok) {
        alert("Status updated!");
        $('complaint-modal').style.display = 'none';
        loadDashboardData();
    }
};

const loadAnalytics = async () => {
    const token = localStorage.getItem('vinu_token');
    const res = await fetch(`${API_URL}/stats`, { headers: { 'Authorization': token } });
    const stats = await res.json();
    
    // SLA Percentage
    const slaPercent = stats.total === 0 ? 100 : Math.round((stats.resolved / stats.total) * 100);
    $('stat-sla').innerText = `${slaPercent}%`;

    // Alerts
    const alertsBox = $('escalation-alerts');
    alertsBox.innerHTML = stats.escalations.length > 0 
        ? `<h4><i class="fas fa-exclamation-triangle"></i> Authority Alerts</h4>` + stats.escalations.map(id => `
            <div class="escalation-alert">
                <span>Complaint #${id.substring(0,8)} has breached SLA!</span>
                <button class="btn-primary btn-small" style="width:auto">Alert Officer</button>
            </div>
        `).join('')
        : '';

    // Trends Chart
    new Chart($('trendChart'), {
        type: 'line',
        data: {
            labels: stats.daily_trend.map(d => d.day),
            datasets: [{
                label: 'New Reports',
                data: stats.daily_trend.map(d => d.count),
                borderColor: '#6366f1',
                tension: 0.4,
                fill: true,
                backgroundColor: 'rgba(99, 102, 241, 0.1)'
            }]
        },
        options: { 
            plugins: { legend: { display: false } },
            scales: { y: { ticks: { color: 'white' }, grid: { color: 'rgba(255,255,255,0.1)' } }, x: { ticks: { color: 'white' } } }
        }
    });

    // Resolution Rate Chart (Bar)
    new Chart($('categoryChart'), {
        type: 'bar',
        data: {
            labels: stats.category_stats.map(s => s.category),
            datasets: [{
                label: 'Resolution Rate (%)',
                data: stats.category_stats.map(s => s.resolution_rate),
                backgroundColor: '#10b981'
            }]
        },
        options: { 
            plugins: { legend: { display: false } },
            scales: { y: { ticks: { color: 'white' }, grid: { color: 'rgba(255,255,255,0.1)' }, max: 100 }, x: { ticks: { color: 'white' } } }
        }
    });

    // Performance Chart (Avg Time)
    new Chart($('performanceChart'), {
        type: 'bar',
        data: {
            labels: stats.category_stats.map(s => s.category),
            datasets: [{
                label: 'Avg Resolution Time (Hours)',
                data: stats.category_stats.map(s => s.avg_res_time),
                backgroundColor: '#f59e0b'
            }]
        },
        options: { 
            indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: { x: { ticks: { color: 'white' }, grid: { color: 'rgba(255,255,255,0.1)' } }, y: { ticks: { color: 'white' } } }
        }
    });

    // AI Insights
    const insights = [];
    const topCategory = [...stats.category_stats].sort((a,b) => b.count - a.count)[0];
    if (topCategory) insights.push(`Primary focus: <b>${topCategory.category}</b> accounts for ${Math.round((topCategory.count / stats.total) * 100)}% of volume.`);
    
    const worstSla = [...stats.category_stats].sort((a,b) => a.resolution_rate - b.resolution_rate)[0];
    if (worstSla && worstSla.resolution_rate < 50) insights.push(`Bottleneck detected in <b>${worstSla.category}</b> with only ${worstSla.resolution_rate}% resolution.`);
    
    if (stats.escalations.length > 5) insights.push(`Resource alert: High number of SLA breaches (${stats.escalations.length}) detected.`);
    
    $('ai-insights-list').innerHTML = insights.map(i => `<p class="insight-p"><i class="fas fa-chevron-right"></i> ${i}</p>`).join('');
};

// --- Notification Logic ---
const fetchNotifications = async () => {
    const token = localStorage.getItem('vinu_token');
    if (!token) return;
    
    try {
        const res = await fetch(`${API_URL}/notifications`, {
            headers: { 'Authorization': token }
        });
        const notifs = await res.json();
        const unread = notifs.filter(n => !n.read).length;
        
        $('notif-count').innerText = unread;
        $('notif-count').style.display = unread > 0 ? 'block' : 'none';
        
        $('notif-list').innerHTML = notifs.length ? notifs.map(n => `
            <div class="notif-item ${n.read ? '' : 'unread'}">
                <span class="n-title">${n.title}</span>
                <span class="n-msg">${n.message}</span>
                <div class="n-time">${new Date(n.created_at).toLocaleTimeString()}</div>
            </div>
        `).join('') : '<p class="subtitle" style="text-align:center">No notifications</p>';
    } catch (err) { console.error(err); }
};

const markNotifsRead = async () => {
    const token = localStorage.getItem('vinu_token');
    await fetch(`${API_URL}/notifications/read`, {
        method: 'POST',
        headers: { 'Authorization': token }
    });
    fetchNotifications();
};

const toggleNotifs = (e) => {
    e.stopPropagation();
    $('notif-dropdown').classList.toggle('show');
    if ($('notif-dropdown').classList.contains('show')) {
        markNotifsRead();
    }
};

// --- Event Listeners ---
$('notif-bell').onclick = toggleNotifs;
document.addEventListener('click', () => $('notif-dropdown').classList.remove('show'));
$('notif-dropdown').onclick = (e) => e.stopPropagation();

$('auth-form').onsubmit = handleAuth;
$('complaint-form').onsubmit = handleComplaintSubmit;
$('tab-login').onclick = () => switchAuthTab('login');
$('tab-register').onclick = () => switchAuthTab('register');
$('logout-btn').onclick = () => { localStorage.clear(); initApp(); };
document.querySelector('.close').onclick = () => $('complaint-modal').style.display = 'none';

document.querySelectorAll('.nav-links li[data-view]').forEach(li => {
    li.onclick = () => switchView(li.dataset.view);
});

$('role-field').querySelector('select').onchange = (e) => {
    $('dept-field').style.display = e.target.value === 'officer' ? 'flex' : 'none';
};

// Landing page triggers
document.querySelectorAll('.login-trigger').forEach(btn => {
    btn.onclick = () => {
        $('landing-page').style.display = 'none';
        $('auth-page').style.display = 'flex';
        switchAuthTab('login');
    };
});

document.querySelectorAll('.register-trigger').forEach(btn => {
    btn.onclick = () => {
        $('landing-page').style.display = 'none';
        $('auth-page').style.display = 'flex';
        switchAuthTab('register');
    };
});

$('back-to-landing').onclick = () => {
    $('auth-page').style.display = 'none';
    $('landing-page').style.display = 'block';
};

window.onload = initApp;
