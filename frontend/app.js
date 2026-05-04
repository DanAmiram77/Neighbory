const API_URL = (window.APP_CONFIG && window.APP_CONFIG.API_URL) || 'http://localhost:8000';

const session = { token: null, user: null };

// ----------------------------------------
// API Helper
// ----------------------------------------

async function _pollUntilAwake(maxMs = 90000) {
    const deadline = Date.now() + maxMs;
    while (Date.now() < deadline) {
        try {
            const ctl = new AbortController();
            const tid = setTimeout(() => ctl.abort(), 5000);
            const r = await fetch(API_URL + '/health', { signal: ctl.signal });
            clearTimeout(tid);
            if (r.ok) return true;
        } catch (_) {}
        await new Promise(r => setTimeout(r, 4000));
    }
    return false;
}

async function apiCall(path, options = {}, _retried = false) {
    const opts = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            ...(session.token ? { 'Authorization': `Bearer ${session.token}` } : {}),
            ...options.headers,
        },
        ...options,
    };
    if (opts.body && typeof opts.body === 'object' && !(opts.body instanceof FormData) && !(opts.body instanceof URLSearchParams)) {
        opts.body = JSON.stringify(opts.body);
    }
    try {
        const res = await fetch(API_URL + path, opts);
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.detail || `שגיאה (${res.status})`);
        return data;
    } catch (err) {
        if (err.message === 'Failed to fetch' && !_retried) {
            toast('השרת מתעורר מתרדמה... ממתין ⏳', 'info');
            const ok = await _pollUntilAwake();
            if (ok) return apiCall(path, options, true);
            throw new Error('השרת לא הגיב. אנא נסו שוב בעוד מספר דקות.');
        }
        if (err.message === 'Failed to fetch') throw new Error('השרת לא הגיב. אנא נסו שוב בעוד מספר דקות.');
        throw err;
    }
}

// ----------------------------------------
// Toast
// ----------------------------------------

function toast(msg, type = 'success') {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = `toast show ${type}`;
    setTimeout(() => el.classList.remove('show'), 4500);
}

// ----------------------------------------
// Modal Management
// ----------------------------------------

function showLogin() { closeAllModals(); document.getElementById('modal-login').classList.add('active'); document.body.style.overflow = 'hidden'; }
function showRegister() { closeAllModals(); document.getElementById('modal-register').classList.add('active'); document.body.style.overflow = 'hidden'; }
function closeModal(id) { document.getElementById(id).classList.remove('active'); document.body.style.overflow = ''; }
function closeAllModals() { document.querySelectorAll('.modal').forEach(m => m.classList.remove('active')); document.body.style.overflow = ''; }

function switchTab(which) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.tab')[which === 'child' ? 0 : 1].classList.add('active');
    document.getElementById(`tab-${which}`).classList.add('active');
}

function showForgotPassword() { closeAllModals(); document.getElementById('modal-forgot').classList.add('active'); document.body.style.overflow = 'hidden'; }

async function handleForgotPassword(e) {
    e.preventDefault();
    const msgEl = document.getElementById('forgot-msg');
    msgEl.style.color = 'var(--ink-soft)';
    msgEl.textContent = 'שולח...';
    const email = e.target.email.value;
    try {
        await apiCall(`/auth/forgot-password?email=${encodeURIComponent(email)}`, { method: 'POST' });
        msgEl.style.color = 'var(--green-dark)';
        msgEl.textContent = '✓ אם האימייל קיים, ישלח קישור לאיפוס תוך כמה שניות.';
        e.target.reset();
    } catch (err) {
        msgEl.style.color = 'var(--err)';
        msgEl.textContent = err.message;
    }
}

async function handleResetPassword(e) {
    e.preventDefault();
    const msgEl = document.getElementById('reset-msg');
    const password = e.target.password.value;
    const password2 = e.target.password2.value;
    if (password !== password2) { msgEl.textContent = 'הסיסמאות אינן תואמות'; return; }
    const token = new URLSearchParams(window.location.search).get('reset_token');
    try {
        await apiCall(`/auth/reset-password?token=${encodeURIComponent(token)}&new_password=${encodeURIComponent(password)}`, { method: 'POST' });
        closeAllModals();
        window.history.replaceState({}, '', '/');
        toast('✓ הסיסמה עודכנה! אפשר להתחבר עכשיו.', 'success');
        setTimeout(showLogin, 600);
    } catch (err) { msgEl.textContent = err.message; }
}

// ----------------------------------------
// Landing page
// ----------------------------------------

function goHome() {
    if (session.user) { renderDashboard(); return; }
    renderHome();
}

function renderHome() {
    document.getElementById('nav-actions').innerHTML = `
        <button class="btn btn-secondary" onclick="showLogin()">כניסה</button>
        <button class="btn btn-primary" onclick="showRegister()">הצטרפו 🚀</button>
    `;
    document.getElementById('main-content').innerHTML = `
        <section id="landing" class="landing">
            <div class="landing-content">
                <span class="tag"><span class="tag-emoji">⚡</span>הקהילה הכי בטוחה לבני 13-18</span>
                <h1 class="hero-title">
                    <span class="wiggle">החנות</span> הראשונה<br>
                    <span class="accent-1">שלך</span> מתחילה <span class="accent-2">כאן</span>
                </h1>
                <p class="hero-sub">פותחים חנות, מוכרים דברים שלא צריכים יותר, ומרוויחים כסף משלכם — בסביבה בטוחה עם פיקוח של ההורים. כי ילדים יכולים להיות יזמים! 💪</p>
                <div class="hero-actions">
                    <button class="btn btn-primary btn-large" onclick="showRegister()">בואו נתחיל! 🎉</button>
                    <button class="btn btn-secondary btn-large" onclick="document.getElementById('features').scrollIntoView({behavior:'smooth'})">איך זה עובד? 🤔</button>
                </div>
                <div class="hero-emojis">
                    <span>🎮</span><span>📚</span><span>⚽</span><span>🎨</span>
                </div>
            </div>
            <div class="landing-visual">
                <span class="sticker sticker-1">⭐</span>
                <span class="sticker sticker-2">✨</span>
                <div class="product-card-floating pcf-1">
                    <div class="pcf-img" style="background:linear-gradient(135deg,#FECACA,#F87171);">🎮</div>
                    <div class="pcf-body">
                        <div class="pcf-title">פלייסטיישן משחק</div>
                        <div class="pcf-meta"><span class="pcf-price">120₪</span><span class="pcf-chip">כמו חדש</span></div>
                    </div>
                </div>
                <div class="product-card-floating pcf-2">
                    <div class="pcf-img" style="background:linear-gradient(135deg,#A7F3D0,#34D399);">📚</div>
                    <div class="pcf-body">
                        <div class="pcf-title">ספרי הארי פוטר</div>
                        <div class="pcf-meta"><span class="pcf-price">80₪</span><span class="pcf-chip">משומש</span></div>
                    </div>
                </div>
                <div class="product-card-floating pcf-3">
                    <div class="pcf-img" style="background:linear-gradient(135deg,#FDE68A,#FBBF24);">⚽</div>
                    <div class="pcf-body">
                        <div class="pcf-title">כדורגל חדש</div>
                        <div class="pcf-meta"><span class="pcf-price">45₪</span><span class="pcf-chip">חדש</span></div>
                    </div>
                </div>
            </div>
        </section>

        <section id="features" class="features">
            <div class="section-header">
                <span class="tag"><span class="tag-emoji">🎯</span>איך זה עובד</span>
                <h2>פשוט. כיף. שלכם.</h2>
            </div>
            <div class="features-grid">
                <div class="feature"><div class="feature-emoji">👋</div><h3>מתחילים עם הורה</h3><p>נרשמים, ההורה מאשר במייל, ויוצאים לדרך. שלושים שניות והכל מוכן!</p></div>
                <div class="feature"><div class="feature-emoji">🏪</div><h3>פותחים חנות שווה</h3><p>תנו לחנות שם מגניב, תיאור קצר, ואתם מוכנים להעלות מוצרים!</p></div>
                <div class="feature"><div class="feature-emoji">🛡️</div><h3>נפגשים בבטחה</h3><p>רק במקומות בטוחים — ספריות, מרכזים קהילתיים, ומקומות ציבוריים.</p></div>
                <div class="feature"><div class="feature-emoji">⭐</div><h3>בונים מוניטין</h3><p>כל עסקה מדורגת — אתם בונים שם טוב בקהילה ומרוויחים יותר אמון!</p></div>
            </div>
        </section>

        <section class="safety">
            <div class="safety-content">
                <span class="tag" style="background:var(--white);color:var(--purple-dark);border-color:var(--ink)"><span class="tag-emoji">🛡️</span>בטיחות מעל הכל</span>
                <h2>אתם מוגנים. ההורים שקטים.</h2>
                <div class="safety-list">
                    <div class="safety-item"><div class="check">✓</div><span>כל מוצר עובר אישור הורה</span></div>
                    <div class="safety-item"><div class="check">✓</div><span>הודעות רק מתבניות מוכנות</span></div>
                    <div class="safety-item"><div class="check">✓</div><span>מפגשים רק במקומות בטוחים</span></div>
                    <div class="safety-item"><div class="check">✓</div><span>מחיר מקסימום: 500₪</span></div>
                    <div class="safety-item"><div class="check">✓</div><span>אין מוצרים מסוכנים</span></div>
                    <div class="safety-item"><div class="check">✓</div><span>הורים רואים הכל</span></div>
                </div>
            </div>
        </section>

        <section class="cta">
            <div class="cta-emoji">🚀</div>
            <h2>מוכנים לפתוח חנות?</h2>
            <p>חינם תמיד! עסקאות קטנות בלי עמלה. רק כיף.</p>
            <button class="btn btn-pink btn-large" onclick="showRegister()">בואו נתחיל! 💫</button>
        </section>

        <footer>
            <div class="footer-content">
                <span>© 2026 Neighbory</span>
                <span>·</span>
                <span>נבנה באהבה לילדים יזמים 💜</span>
                <span>·</span>
                <a href="/privacy.html" style="color:white;font-weight:600;">מדיניות פרטיות</a>
                <span>·</span>
                <a href="/terms.html" style="color:white;font-weight:600;">תנאי שימוש</a>
            </div>
        </footer>
    `;
}

// ----------------------------------------
// Form helpers
// ----------------------------------------

function formToObject(form) {
    const data = {};
    new FormData(form).forEach((value, key) => { data[key] = key === 'age' ? parseInt(value, 10) : value; });
    return data;
}

function esc(s) {
    return String(s || '').replace(/[<>&"']/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&#39;'}[c]));
}

// ----------------------------------------
// Auth handlers
// ----------------------------------------

function _disableBtn(btn, text) { btn.disabled = true; btn.dataset.orig = btn.textContent; btn.textContent = text; }
function _enableBtn(btn) { btn.disabled = false; btn.textContent = btn.dataset.orig; }

async function handleLogin(e) {
    e.preventDefault();
    const errEl = document.getElementById('login-error');
    const btn = e.target.querySelector('button[type=submit]');
    errEl.textContent = '';
    _disableBtn(btn, 'מתחבר...');
    const data = formToObject(e.target);
    const body = new URLSearchParams();
    body.append('username', data.email);
    body.append('password', data.password);
    try {
        const res = await apiCall('/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body });
        session.token = res.access_token;
        session.user = res.user;
        closeAllModals();
        toast(`👋 ברוכים השבים, ${res.user.full_name}!`);
        renderDashboard();
    } catch (err) { errEl.textContent = err.message; _enableBtn(btn); }
}

async function handleChildRegister(e) {
    e.preventDefault();
    const errEl = document.getElementById('register-child-error');
    const btn = e.target.querySelector('button[type=submit]');
    errEl.textContent = '';
    _disableBtn(btn, 'שולח... ⏳');
    const data = formToObject(e.target);
    try {
        await apiCall('/auth/register/child', { method: 'POST', body: data });
        closeAllModals();
        toast('🎯 ההרשמה הצליחה! שלחנו קוד אישור למייל ההורה.', 'success');
    } catch (err) { errEl.textContent = err.message; _enableBtn(btn); }
}

async function handleParentRegister(e) {
    e.preventDefault();
    const errEl = document.getElementById('register-parent-error');
    const btn = e.target.querySelector('button[type=submit]');
    errEl.textContent = '';
    _disableBtn(btn, 'שולח... ⏳');
    const data = formToObject(e.target);
    try {
        await apiCall('/auth/register/parent', { method: 'POST', body: data });
        closeAllModals();
        toast('🎉 נרשמתם בהצלחה! אפשר להתחבר עכשיו.');
        setTimeout(showLogin, 500);
    } catch (err) { errEl.textContent = err.message; _enableBtn(btn); }
}

// ----------------------------------------
// Dashboard
// ----------------------------------------

function renderDashboard() {
    const isParent = session.user.role === 'parent';
    document.getElementById('nav-actions').innerHTML = `
        <span class="user-pill">${isParent ? '👨‍👩‍👧' : '🎒'} ${esc(session.user.full_name)}</span>
        <button class="btn btn-secondary" onclick="logout()">יציאה 👋</button>
    `;
    if (isParent) renderParentDashboard();
    else renderChildDashboard();
}

async function renderChildDashboard() {
    const main = document.getElementById('main-content');
    main.innerHTML = `<div class="dashboard"><div style="text-align:center;padding:60px;font-size:40px;">⏳</div></div>`;

    try {
        let store;
        try { store = await apiCall('/stores/me'); } catch (_) { store = null; }

        if (!store) {
            main.innerHTML = `<div class="dashboard">
                <div class="dashboard-header">
                    <div class="dashboard-title"><h1>🏪 החנות שלי</h1><p>היי ${esc(session.user.full_name)}, מה נמכור היום?</p></div>
                </div>
                <div class="empty-state">
                    <div class="empty-state-emoji">🚀</div>
                    <h3>בואו נפתח חנות יחד!</h3>
                    <p>תנו לה שם מגניב ותתחילו למכור</p>
                    <button class="btn btn-primary btn-large" onclick="showCreateStore()">פתיחת חנות 🎉</button>
                </div>
            </div>`;
            return;
        }

        const allProducts = await apiCall('/products/?limit=50').catch(() => []);
        const myProducts = allProducts.filter(p => p.store_id === store.id);
        const others = allProducts.filter(p => p.store_id !== store.id);

        let html = `<div class="dashboard">
            <div class="dashboard-header">
                <div class="dashboard-title"><h1>🏪 החנות שלי</h1><p>היי ${esc(session.user.full_name)}, מה נמכור היום?</p></div>
                <button class="btn btn-pink btn-large" onclick="showCreateProduct()">➕ מוצר חדש</button>
            </div>
            <div class="store-info">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px">
                    <div>
                        <h2 style="font-family:var(--font-display);font-size:28px;font-weight:700;margin-bottom:4px">${esc(store.name)}</h2>
                        <p style="color:var(--ink-soft);font-size:15px;font-weight:500">${esc(store.description || 'בלי תיאור עדיין')}</p>
                    </div>
                    <div style="display:flex;gap:20px;text-align:center">
                        <div style="background:var(--yellow-light);padding:14px 18px;border-radius:var(--r-sm);border:3px solid var(--ink)">
                            <div style="font-family:var(--font-display);font-weight:700;font-size:26px">${store.total_sales}</div>
                            <div style="font-size:12px;color:var(--ink-soft);font-weight:600;margin-top:2px">עסקאות</div>
                        </div>
                        <div style="background:var(--pink-light);padding:14px 18px;border-radius:var(--r-sm);border:3px solid var(--ink)">
                            <div style="font-family:var(--font-display);font-weight:700;font-size:26px">⭐ ${store.rating.toFixed(1)}</div>
                            <div style="font-size:12px;color:var(--ink-soft);font-weight:600;margin-top:2px">דירוג</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="section-title">📦 המוצרים שלי</div>
            <div class="dashboard-grid">`;

        if (myProducts.length === 0) {
            html += `<div class="empty-state"><div class="empty-state-emoji">📦</div><h3>בואו נעלה מוצר ראשון!</h3><p>ההורה יאשר וזה יופיע בשוק</p><button class="btn btn-primary btn-large" onclick="showCreateProduct()">➕ העלאת מוצר</button></div>`;
        } else {
            html += myProducts.map(p => productCardHTML(p)).join('');
        }

        html += `</div>
            <div style="margin-top:40px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
                <div class="section-title" style="margin:0">🔍 מוצרים באזור</div>
                <div style="display:flex;gap:10px;flex-wrap:wrap">
                    <input id="market-search" type="text" placeholder="🔎 חיפוש..." onInput="filterMarketplace()" style="padding:10px 16px;border:3px solid var(--ink);border-radius:100px;font-family:var(--font-body);font-size:14px;font-weight:500;background:var(--white);width:180px;">
                    <select id="market-category" onchange="filterMarketplace()" style="padding:10px 16px;border:3px solid var(--ink);border-radius:100px;font-family:var(--font-body);font-size:14px;font-weight:600;background:var(--white);cursor:pointer;">
                        <option value="">כל הקטגוריות</option>
                        <option value="toys">🧸 צעצועים</option>
                        <option value="books">📚 ספרים</option>
                        <option value="games">🎮 משחקים</option>
                        <option value="clothes">👕 בגדים</option>
                        <option value="sports">⚽ ספורט</option>
                        <option value="collectibles">🎴 אספנות</option>
                        <option value="electronics">🎧 אלקטרוניקה</option>
                        <option value="handmade">🎨 יצירה</option>
                        <option value="other">📦 אחר</option>
                    </select>
                </div>
            </div>
            <div class="dashboard-grid" id="marketplace-grid">`;

        if (others.length === 0) {
            html += `<div class="empty-state"><div class="empty-state-emoji">🛍️</div><p>עדיין אין מוצרים של אחרים בשוק</p></div>`;
        } else {
            html += others.map(p => productCardHTML(p)).join('');
        }
        html += `</div></div>`;
        main.innerHTML = html;

        // store for filtering
        window._marketplaceProducts = others;
    } catch (err) { toast(err.message, 'error'); }
}

async function approveChild(childId) {
    const code = prompt('הזינו את קוד האישור שנשלח לאימייל שלכם:');
    if (!code) return;
    try {
        await apiCall(`/auth/parent/approve/${childId}`, { method: 'POST', body: { approval_code: code } });
        toast('✅ חשבון הילד/ה אושר בהצלחה!', 'success');
        renderParentDashboard();
    } catch (err) { toast(err.message, 'error'); }
}

async function renderParentDashboard() {
    const main = document.getElementById('main-content');
    main.innerHTML = `<div class="dashboard"><div style="text-align:center;padding:60px;font-size:40px;">⏳</div></div>`;

    try {
        const [pendingChildren, pendingProducts] = await Promise.all([
            apiCall('/auth/parent/pending-children').catch(() => []),
            apiCall('/products/pending-approval').catch(() => []),
        ]);

        let html = `<div class="dashboard">
            <div class="dashboard-header">
                <div class="dashboard-title"><h1>👨‍👩‍👧 לוח הבקרה שלכם</h1><p>אישור פעילות ילדיכם בקליק</p></div>
            </div>`;

        if (pendingChildren.length > 0) {
            html += `<div class="section-title">👶 ילדים שממתינים לאישור חשבון</div>
            <div class="dashboard-grid">` + pendingChildren.map(c => `
                <div class="product-card">
                    <div class="product-img" style="font-size:48px;display:flex;align-items:center;justify-content:center">🧒</div>
                    <div class="product-info">
                        <div class="product-title">${esc(c.full_name)}</div>
                        <div style="color:var(--ink-soft);font-size:13px;margin-bottom:12px;font-weight:500">@${esc(c.username)} · גיל ${c.age}</div>
                        <button class="btn btn-primary btn-full" style="font-size:13px" onclick="approveChild(${c.id})">✅ אישור חשבון</button>
                    </div>
                </div>`).join('') + `</div>`;
        }

        html += `<div class="section-title">📦 מוצרים שמחכים לאישור</div>`;
        if (pendingProducts.length === 0) {
            html += `<div class="empty-state"><div class="empty-state-emoji">🎉</div><h3>הכל בשליטה!</h3><p>אין מוצרים שמחכים לאישור עכשיו</p></div>`;
        } else {
            html += `<div class="dashboard-grid">` + pendingProducts.map(p => `
                <div class="product-card">
                    <div class="product-img">${categoryIcon(p.category)}</div>
                    <div class="product-info">
                        <div class="product-title">${esc(p.title)}</div>
                        <div style="color:var(--ink-soft);font-size:13px;margin-bottom:12px;line-height:1.5;font-weight:500">${esc(p.description.substring(0, 90))}${p.description.length > 90 ? '...' : ''}</div>
                        <div class="product-meta"><span class="product-price">${p.price}₪</span><span class="status-badge status-pending">⏳ ממתין</span></div>
                        <div style="display:flex;gap:8px;margin-top:14px">
                            <button class="btn btn-primary" style="flex:1;padding:10px;font-size:13px" onclick="approveProduct(${p.id})">✓ אישור</button>
                            <button class="btn btn-secondary" style="flex:1;padding:10px;font-size:13px" onclick="rejectProduct(${p.id})">דחייה</button>
                        </div>
                    </div>
                </div>`).join('') + `</div>`;
        }
        html += `</div>`;
        main.innerHTML = html;
    } catch (err) { toast(err.message, 'error'); }
}

// ----------------------------------------
// Marketplace filter
// ----------------------------------------

function filterMarketplace() {
    const search = (document.getElementById('market-search')?.value || '').toLowerCase();
    const category = document.getElementById('market-category')?.value || '';
    const grid = document.getElementById('marketplace-grid');
    if (!grid) return;

    const filtered = (window._marketplaceProducts || []).filter(p => {
        const matchText = !search || p.title.toLowerCase().includes(search) || p.description.toLowerCase().includes(search);
        const matchCat = !category || p.category === category;
        return matchText && matchCat;
    });

    if (filtered.length === 0) {
        grid.innerHTML = `<div class="empty-state"><div class="empty-state-emoji">🔍</div><p>לא נמצאו מוצרים תואמים</p></div>`;
    } else {
        grid.innerHTML = filtered.map(p => productCardHTML(p)).join('');
    }
}

// ----------------------------------------
// Product helpers
// ----------------------------------------

function categoryIcon(cat) {
    return ({toys:'🧸',books:'📚',games:'🎮',clothes:'👕',sports:'⚽',collectibles:'🎴',electronics:'🎧',handmade:'🎨',other:'📦'})[cat] || '📦';
}

function productCardHTML(p) {
    const imgContent = (p.images && p.images.length > 0)
        ? `<img src="${p.images[0]}" style="width:100%;height:100%;object-fit:cover;">`
        : categoryIcon(p.category);
    return `<div class="product-card">
        <div class="product-img">${imgContent}</div>
        <div class="product-info">
            <div class="product-title">${esc(p.title)}</div>
            <div class="product-meta">
                <span class="product-price">${p.price}₪</span>
                <span class="status-badge status-${p.status === 'active' ? 'active' : 'pending'}">${p.status === 'active' ? '✓ פעיל' : '⏳ ממתין'}</span>
            </div>
        </div>
    </div>`;
}

async function approveProduct(id) {
    try { await apiCall(`/products/${id}/approve`, { method: 'POST' }); toast('✓ המוצר אושר ונכנס לשוק'); renderParentDashboard(); }
    catch (err) { toast(err.message, 'error'); }
}

async function rejectProduct(id) {
    if (!confirm('בטוחים שאתם רוצים לדחות את המוצר?')) return;
    try { await apiCall(`/products/${id}/reject`, { method: 'POST' }); toast('המוצר נדחה'); renderParentDashboard(); }
    catch (err) { toast(err.message, 'error'); }
}

// ----------------------------------------
// Create store / product
// ----------------------------------------

function showCreateStore() {
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.id = 'modal-store';
    modal.innerHTML = `
        <div class="modal-backdrop" onclick="document.getElementById('modal-store').remove()"></div>
        <div class="modal-content">
            <button class="modal-close" onclick="document.getElementById('modal-store').remove()">×</button>
            <div class="modal-emoji">🏪</div>
            <h2 class="modal-title">פותחים חנות!</h2>
            <p class="modal-sub">תנו לחנות שלכם שם מגניב ותיאור</p>
            <form onsubmit="handleCreateStore(event)">
                <div class="field"><label>שם החנות</label><input type="text" name="name" required minlength="2" placeholder="לדוגמה: החנות של דני"></div>
                <div class="field"><label>תיאור קצר</label><input type="text" name="description" placeholder="מה תמכרו?"></div>
                <div class="field"><label>רדיוס משלוח (ק"מ)</label><input type="number" name="delivery_radius_km" value="5" min="1" max="50"></div>
                <div class="error-msg" id="store-error"></div>
                <button type="submit" class="btn btn-primary btn-full btn-large">פותחים חנות! 🎉</button>
            </form>
        </div>`;
    document.body.appendChild(modal);
}

async function handleCreateStore(e) {
    e.preventDefault();
    const data = formToObject(e.target);
    data.delivery_radius_km = parseInt(data.delivery_radius_km, 10) || 5;

    const btn = e.target.querySelector('button[type=submit]');
    btn.textContent = '📍 מאתר מיקום...';
    btn.disabled = true;

    try {
        const pos = await new Promise((resolve, reject) =>
            navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 6000 })
        );
        data.latitude = pos.coords.latitude;
        data.longitude = pos.coords.longitude;
    } catch (_) {
        data.latitude = 32.0853;
        data.longitude = 34.7818;
    }

    try {
        await apiCall('/stores/', { method: 'POST', body: data });
        document.getElementById('modal-store').remove();
        toast('🎉 החנות נפתחה! עכשיו אפשר להעלות מוצרים');
        renderChildDashboard();
    } catch (err) {
        btn.textContent = 'פותחים חנות! 🎉';
        btn.disabled = false;
        document.getElementById('store-error').textContent = err.message;
    }
}

function showCreateProduct() {
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.id = 'modal-product';
    modal.innerHTML = `
        <div class="modal-backdrop" onclick="document.getElementById('modal-product').remove()"></div>
        <div class="modal-content">
            <button class="modal-close" onclick="document.getElementById('modal-product').remove()">×</button>
            <div class="modal-emoji">📦</div>
            <h2 class="modal-title">מעלים מוצר חדש!</h2>
            <p class="modal-sub">המוצר יפורסם רק לאחר אישור הורה</p>
            <form onsubmit="handleCreateProduct(event)">
                <div class="field"><label>כותרת</label><input type="text" name="title" required minlength="3" placeholder="לדוגמה: משחק קטאן במצב מעולה"></div>
                <div class="field"><label>תיאור</label><input type="text" name="description" required minlength="10" placeholder="תיאור מפורט של המוצר"></div>
                <div class="field-row">
                    <div class="field"><label>מחיר (₪)</label><input type="number" name="price" required min="1" max="500" placeholder="80"></div>
                    <div class="field"><label>קטגוריה</label>
                        <select name="category" required>
                            <option value="">בחרו</option>
                            <option value="toys">🧸 צעצועים</option>
                            <option value="books">📚 ספרים</option>
                            <option value="games">🎮 משחקים</option>
                            <option value="clothes">👕 בגדים</option>
                            <option value="sports">⚽ ספורט</option>
                            <option value="collectibles">🎴 אספנות</option>
                            <option value="electronics">🎧 אלקטרוניקה</option>
                            <option value="handmade">🎨 יצירה</option>
                            <option value="other">📦 אחר</option>
                        </select>
                    </div>
                </div>
                <div class="field"><label>מצב</label>
                    <select name="condition" required>
                        <option value="">בחרו</option>
                        <option value="new">✨ חדש באריזה</option>
                        <option value="like_new">⭐ כמו חדש</option>
                        <option value="used">👍 משומש</option>
                    </select>
                </div>
                <div class="field">
                    <label>תמונה (אופציונלי, עד 500KB)</label>
                    <input type="file" id="product-image-input" accept="image/*" onchange="previewProductImage(this)" style="width:100%;padding:10px;border:3px solid var(--ink);border-radius:var(--r-sm);background:var(--white);cursor:pointer;">
                    <div id="product-image-preview" style="margin-top:10px;display:none;">
                        <img id="product-image-thumb" style="width:100%;max-height:180px;object-fit:cover;border-radius:var(--r-sm);border:3px solid var(--ink);">
                        <button type="button" onclick="clearProductImage()" style="margin-top:6px;font-size:13px;background:none;border:none;color:var(--err);cursor:pointer;font-weight:600;">✕ הסר תמונה</button>
                    </div>
                </div>
                <div class="error-msg" id="product-error"></div>
                <button type="submit" class="btn btn-primary btn-full btn-large">העלאת המוצר! 🚀</button>
            </form>
        </div>`;
    document.body.appendChild(modal);
}

let _productImageBase64 = null;

function previewProductImage(input) {
    const file = input.files[0];
    if (!file) return;
    if (file.size > 500 * 1024) {
        document.getElementById('product-error').textContent = 'התמונה גדולה מדי — מקסימום 500KB';
        input.value = '';
        return;
    }
    const reader = new FileReader();
    reader.onload = e => {
        _productImageBase64 = e.target.result;
        document.getElementById('product-image-thumb').src = _productImageBase64;
        document.getElementById('product-image-preview').style.display = 'block';
    };
    reader.readAsDataURL(file);
}

function clearProductImage() {
    _productImageBase64 = null;
    document.getElementById('product-image-input').value = '';
    document.getElementById('product-image-preview').style.display = 'none';
}

async function handleCreateProduct(e) {
    e.preventDefault();
    const form = e.target;
    const data = {
        title: form.title.value, description: form.description.value,
        price: parseFloat(form.price.value), category: form.category.value,
        condition: form.condition.value,
        images: _productImageBase64 ? [_productImageBase64] : [],
    };
    try {
        await apiCall('/products/', { method: 'POST', body: data });
        _productImageBase64 = null;
        document.getElementById('modal-product').remove();
        toast('🎯 המוצר עלה! ההורה יאשר אותו');
        renderChildDashboard();
    } catch (err) { document.getElementById('product-error').textContent = err.message; }
}

// ----------------------------------------
// Logout
// ----------------------------------------

function logout() {
    session.token = null;
    session.user = null;
    renderHome();
}

// ----------------------------------------
// Init
// ----------------------------------------

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeAllModals(); });

// Wake up the API on page load — show a banner until it responds
(async () => {
    const banner = document.createElement('div');
    banner.id = 'wake-banner';
    banner.style.cssText = 'position:fixed;top:0;left:0;right:0;background:#7C3AED;color:#fff;text-align:center;padding:10px;font-family:var(--font-body,sans-serif);font-weight:600;font-size:14px;z-index:999;border-bottom:3px solid #1F2937';
    banner.textContent = '⏳ השרת מתעורר — אנא המתינו כמה שניות...';
    let shown = false;
    const tid = setTimeout(() => { document.body.appendChild(banner); shown = true; }, 2000);
    await _pollUntilAwake(60000);
    clearTimeout(tid);
    if (shown) banner.remove();
})();

const resetToken = new URLSearchParams(window.location.search).get('reset_token');
if (resetToken) {
    renderHome();
    document.getElementById('modal-reset').classList.add('active');
    document.body.style.overflow = 'hidden';
} else {
    renderHome();
}
