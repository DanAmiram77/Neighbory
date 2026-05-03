// ========================================
// Neighbory Frontend - App Logic
// ========================================

// Read API URL from config.js (loaded before this script in index.html)
const API_URL = (window.APP_CONFIG && window.APP_CONFIG.API_URL) || 'http://localhost:8000';

// ----------------------------------------
// Storage helpers (in-memory only, per session)
// ----------------------------------------

const session = {
    token: null,
    user: null,
};

// ----------------------------------------
// API Helpers
// ----------------------------------------

async function apiCall(path, options = {}) {
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
        if (!res.ok) {
            throw new Error(data.detail || `שגיאה (${res.status})`);
        }
        return data;
    } catch (err) {
        if (err.message === 'Failed to fetch') {
            throw new Error('לא ניתן להתחבר לשרת. ודאו שה-Backend רץ על ' + API_URL);
        }
        throw err;
    }
}

// ----------------------------------------
// Modal Management
// ----------------------------------------

function showLogin() {
    closeAllModals();
    document.getElementById('modal-login').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function showRegister() {
    closeAllModals();
    document.getElementById('modal-register').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
    document.body.style.overflow = '';
}

function closeAllModals() {
    document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
    document.body.style.overflow = '';
}

function switchTab(which) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    const tabs = document.querySelectorAll('.tab');
    tabs[which === 'child' ? 0 : 1].classList.add('active');
    document.getElementById(`tab-${which}`).classList.add('active');
}

// ----------------------------------------
// Toast
// ----------------------------------------

function toast(msg, type = 'success') {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = `toast show ${type}`;
    setTimeout(() => el.classList.remove('show'), 4000);
}

// ----------------------------------------
// Form handlers
// ----------------------------------------

function formToObject(form) {
    const data = {};
    new FormData(form).forEach((value, key) => {
        data[key] = key === 'age' ? parseInt(value, 10) : value;
    });
    return data;
}

async function handleLogin(e) {
    e.preventDefault();
    const errEl = document.getElementById('login-error');
    errEl.textContent = '';

    const data = formToObject(e.target);
    const body = new URLSearchParams();
    body.append('username', data.email);
    body.append('password', data.password);

    try {
        const res = await apiCall('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body,
        });

        session.token = res.access_token;
        session.user = res.user;
        closeAllModals();
        toast(`ברוכים השבים, ${res.user.full_name}!`);
        renderDashboard();
    } catch (err) {
        errEl.textContent = err.message;
    }
}

async function handleChildRegister(e) {
    e.preventDefault();
    const errEl = document.getElementById('register-child-error');
    errEl.textContent = '';

    const data = formToObject(e.target);

    try {
        const res = await apiCall('/auth/register/child', {
            method: 'POST',
            body: data,
        });

        closeAllModals();
        toast(
            `✓ ההרשמה הצליחה! ההורה יקבל קוד אישור. (במצב פיתוח: ${res.approval_code_for_testing})`,
            'success'
        );
    } catch (err) {
        errEl.textContent = err.message;
    }
}

async function handleParentRegister(e) {
    e.preventDefault();
    const errEl = document.getElementById('register-parent-error');
    errEl.textContent = '';

    const data = formToObject(e.target);

    try {
        await apiCall('/auth/register/parent', {
            method: 'POST',
            body: data,
        });

        closeAllModals();
        toast('✓ נרשמתם בהצלחה! אפשר להתחבר עכשיו.');
        setTimeout(showLogin, 500);
    } catch (err) {
        errEl.textContent = err.message;
    }
}

// ----------------------------------------
// Dashboard
// ----------------------------------------

function renderDashboard() {
    const isParent = session.user.role === 'parent';

    document.body.innerHTML = `
        <div class="grid-bg"></div>
        <nav class="nav">
            <div class="nav-logo">
                <div class="logo-mark">
                    <svg viewBox="0 0 40 40" width="32" height="32">
                        <circle cx="20" cy="20" r="16" fill="none" stroke="currentColor" stroke-width="2.5"/>
                        <path d="M 12 20 L 18 26 L 28 14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <span class="logo-text">KidsTrade</span>
            </div>
            <div class="nav-actions">
                <span style="color: var(--ink-500); font-size: 14px; margin-left: 12px;">
                    ${session.user.full_name} · ${isParent ? 'הורה' : 'ילד/ה'}
                </span>
                <button class="btn-ghost" onclick="logout()">יציאה</button>
            </div>
        </nav>
        <div class="dashboard" id="dashboard-main"></div>
        <div id="toast" class="toast"></div>
    `;

    if (isParent) {
        renderParentDashboard();
    } else {
        renderChildDashboard();
    }
}

async function renderChildDashboard() {
    const main = document.getElementById('dashboard-main');
    main.innerHTML = `
        <div class="dashboard-header">
            <div class="dashboard-title">
                <h1>החנות שלי</h1>
                <p>נהלו את המוצרים שלכם ועקבו אחרי ההתעניינות</p>
            </div>
            <button class="btn-primary" onclick="showCreateProduct()">+ העלאת מוצר</button>
        </div>
        <div id="store-content">
            <div style="text-align: center; padding: 40px; color: var(--ink-500);">טוען...</div>
        </div>
    `;

    try {
        // Check if store exists
        let store;
        try {
            store = await apiCall('/stores/me');
        } catch (err) {
            // No store yet - show create store
            main.querySelector('#store-content').innerHTML = `
                <div class="empty-state">
                    <h3>פתחו את החנות הראשונה שלכם</h3>
                    <p>פשוט תנו לה שם ותיאור, ותוכלו להתחיל למכור.</p>
                    <button class="btn-primary btn-large" onclick="showCreateStore()">פתיחת חנות</button>
                </div>
            `;
            return;
        }

        // Load products
        const pendingPromise = apiCall(`/products/?limit=50`).catch(() => []);
        const allProducts = await pendingPromise;

        // We only got active products; for pending, query all by my store
        // In our MVP backend, there is no "my products" endpoint, so we display active ones
        const myActive = allProducts.filter(p => p.store_id === store.id);

        main.querySelector('#store-content').innerHTML = `
            <div style="background: var(--white); padding: 24px; border-radius: var(--radius-lg); border: 1px solid var(--ink-100); margin-bottom: 28px;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
                    <div>
                        <h2 style="font-family: var(--font-display); font-size: 22px; font-weight: 700; margin-bottom: 4px;">${store.name}</h2>
                        <p style="color: var(--ink-500); font-size: 14px;">${store.description || 'אין תיאור'}</p>
                    </div>
                    <div style="display: flex; gap: 24px; text-align: center;">
                        <div>
                            <div style="font-family: var(--font-display); font-weight: 800; font-size: 22px;">${store.total_sales}</div>
                            <div style="font-size: 12px; color: var(--ink-500);">עסקאות</div>
                        </div>
                        <div>
                            <div style="font-family: var(--font-display); font-weight: 800; font-size: 22px;">${store.rating.toFixed(1)} ★</div>
                            <div style="font-size: 12px; color: var(--ink-500);">דירוג</div>
                        </div>
                    </div>
                </div>
            </div>

            <h3 style="font-family: var(--font-display); font-weight: 700; font-size: 18px; margin-bottom: 16px;">המוצרים שלי</h3>
            <div class="dashboard-grid" id="products-grid"></div>
        `;

        const grid = document.getElementById('products-grid');
        if (myActive.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <h3>עדיין אין מוצרים</h3>
                    <p>המוצרים שתעלו יופיעו כאן לאחר אישור הורה</p>
                    <button class="btn-primary" onclick="showCreateProduct()">+ העלאת מוצר ראשון</button>
                </div>
            `;
        } else {
            grid.innerHTML = myActive.map(p => productCardHTML(p)).join('');
        }

        // Also show marketplace
        main.innerHTML += `
            <h3 style="font-family: var(--font-display); font-weight: 700; font-size: 18px; margin: 40px 0 16px;">מוצרים באזור שלכם</h3>
            <div class="dashboard-grid" id="marketplace-grid"></div>
        `;
        const others = allProducts.filter(p => p.store_id !== store.id);
        const mpGrid = document.getElementById('marketplace-grid');
        if (others.length === 0) {
            mpGrid.innerHTML = `<div class="empty-state"><p>עדיין אין מוצרים של משתמשים אחרים</p></div>`;
        } else {
            mpGrid.innerHTML = others.map(p => productCardHTML(p)).join('');
        }
    } catch (err) {
        toast(err.message, 'error');
    }
}

async function renderParentDashboard() {
    const main = document.getElementById('dashboard-main');
    main.innerHTML = `
        <div class="dashboard-header">
            <div class="dashboard-title">
                <h1>לוח בקרה הורי</h1>
                <p>מוצרים שממתינים לאישור שלכם</p>
            </div>
        </div>
        <div id="pending-products">
            <div style="text-align: center; padding: 40px; color: var(--ink-500);">טוען...</div>
        </div>
    `;

    try {
        const pending = await apiCall('/products/pending-approval');
        const container = document.getElementById('pending-products');

        if (pending.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>אין מוצרים הממתינים לאישור</h3>
                    <p>כאשר ילדכם יעלה מוצר, הוא יופיע כאן לאישורכם</p>
                </div>
            `;
        } else {
            container.innerHTML = `<div class="dashboard-grid">
                ${pending.map(p => `
                    <div class="product-card">
                        <div class="product-img">${categoryIcon(p.category)}</div>
                        <div class="product-info">
                            <div class="product-title">${escape(p.title)}</div>
                            <div style="color: var(--ink-500); font-size: 13px; margin-bottom: 12px; line-height: 1.5;">${escape(p.description.substring(0, 100))}${p.description.length > 100 ? '...' : ''}</div>
                            <div class="product-meta">
                                <span class="product-price">${p.price}₪</span>
                                <span class="status-badge status-pending">ממתין לאישור</span>
                            </div>
                            <div style="display: flex; gap: 8px; margin-top: 16px;">
                                <button class="btn-primary" style="flex: 1; padding: 10px; font-size: 13px;" onclick="approveProduct(${p.id})">✓ אישור</button>
                                <button class="btn-ghost" style="flex: 1; padding: 10px; font-size: 13px;" onclick="rejectProduct(${p.id})">דחייה</button>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>`;
        }
    } catch (err) {
        toast(err.message, 'error');
    }
}

// ----------------------------------------
// Product helpers
// ----------------------------------------

function categoryIcon(cat) {
    const map = {
        toys: '🧸', books: '📚', games: '🎮', clothes: '👕',
        sports: '⚽', collectibles: '🎴', electronics: '🎧',
        handmade: '🎨', other: '📦'
    };
    return map[cat] || '📦';
}

function escape(s) {
    return String(s || '').replace(/[<>&"']/g, c =>
        ({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&#39;'}[c]));
}

function productCardHTML(p) {
    return `
        <div class="product-card">
            <div class="product-img">${categoryIcon(p.category)}</div>
            <div class="product-info">
                <div class="product-title">${escape(p.title)}</div>
                <div class="product-meta">
                    <span class="product-price">${p.price}₪</span>
                    <span class="status-badge status-${p.status === 'active' ? 'active' : 'pending'}">
                        ${p.status === 'active' ? 'פעיל' : 'ממתין'}
                    </span>
                </div>
            </div>
        </div>
    `;
}

async function approveProduct(id) {
    try {
        await apiCall(`/products/${id}/approve`, { method: 'POST' });
        toast('המוצר אושר');
        renderParentDashboard();
    } catch (err) {
        toast(err.message, 'error');
    }
}

async function rejectProduct(id) {
    if (!confirm('בטוחים שאתם רוצים לדחות את המוצר?')) return;
    try {
        await apiCall(`/products/${id}/reject`, { method: 'POST' });
        toast('המוצר נדחה');
        renderParentDashboard();
    } catch (err) {
        toast(err.message, 'error');
    }
}

// ----------------------------------------
// Create store / product modals
// ----------------------------------------

function showCreateStore() {
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.id = 'modal-store';
    modal.innerHTML = `
        <div class="modal-backdrop" onclick="document.getElementById('modal-store').remove()"></div>
        <div class="modal-content">
            <button class="modal-close" onclick="document.getElementById('modal-store').remove()">×</button>
            <h2 class="modal-title">פתיחת חנות</h2>
            <p class="modal-sub">תנו לחנות שלכם שם ותיאור</p>
            <form onsubmit="handleCreateStore(event)">
                <div class="field">
                    <label>שם החנות</label>
                    <input type="text" name="name" required minlength="2" placeholder="לדוגמה: משחקים של דני">
                </div>
                <div class="field">
                    <label>תיאור קצר</label>
                    <input type="text" name="description" placeholder="מה תמכרו? לאיזה גילאים?">
                </div>
                <div class="field-row">
                    <div class="field">
                        <label>רדיוס משלוח (ק"מ)</label>
                        <input type="number" name="delivery_radius_km" value="5" min="1" max="50">
                    </div>
                </div>
                <div class="error-msg" id="store-error"></div>
                <button type="submit" class="btn-primary btn-full">פתיחת חנות</button>
            </form>
        </div>
    `;
    document.body.appendChild(modal);
}

async function handleCreateStore(e) {
    e.preventDefault();
    const data = formToObject(e.target);
    data.latitude = 32.0853;   // ברירת מחדל - בפועל נשתמש ב-geolocation
    data.longitude = 34.7818;
    data.delivery_radius_km = parseInt(data.delivery_radius_km, 10) || 5;

    try {
        await apiCall('/stores/', { method: 'POST', body: data });
        document.getElementById('modal-store').remove();
        toast('החנות נפתחה! עכשיו אפשר להעלות מוצרים');
        renderChildDashboard();
    } catch (err) {
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
            <h2 class="modal-title">העלאת מוצר</h2>
            <p class="modal-sub">המוצר יפורסם רק לאחר אישור הורה</p>
            <form onsubmit="handleCreateProduct(event)">
                <div class="field">
                    <label>כותרת</label>
                    <input type="text" name="title" required minlength="3" placeholder="לדוגמה: משחק קטאן במצב מעולה">
                </div>
                <div class="field">
                    <label>תיאור</label>
                    <input type="text" name="description" required minlength="10" placeholder="תיאור מפורט של המוצר, מצב, כולל מה">
                </div>
                <div class="field-row">
                    <div class="field">
                        <label>מחיר (₪)</label>
                        <input type="number" name="price" required min="1" max="500" placeholder="80">
                    </div>
                    <div class="field">
                        <label>קטגוריה</label>
                        <select name="category" required style="width: 100%; padding: 12px 16px; font-size: 15px; border: 1.5px solid var(--ink-100); border-radius: var(--radius-md); background: var(--white);">
                            <option value="">בחרו קטגוריה</option>
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
                <div class="field">
                    <label>מצב המוצר</label>
                    <select name="condition" required style="width: 100%; padding: 12px 16px; font-size: 15px; border: 1.5px solid var(--ink-100); border-radius: var(--radius-md); background: var(--white);">
                        <option value="">בחרו מצב</option>
                        <option value="new">חדש באריזה</option>
                        <option value="like_new">כמו חדש</option>
                        <option value="used">משומש</option>
                    </select>
                </div>
                <div class="error-msg" id="product-error"></div>
                <button type="submit" class="btn-primary btn-full">העלאת המוצר</button>
            </form>
        </div>
    `;
    document.body.appendChild(modal);
}

async function handleCreateProduct(e) {
    e.preventDefault();
    const form = e.target;
    const data = {
        title: form.title.value,
        description: form.description.value,
        price: parseFloat(form.price.value),
        category: form.category.value,
        condition: form.condition.value,
        images: [],
    };

    try {
        await apiCall('/products/', { method: 'POST', body: data });
        document.getElementById('modal-product').remove();
        toast('✓ המוצר הועלה וממתין לאישור הורה');
        renderChildDashboard();
    } catch (err) {
        document.getElementById('product-error').textContent = err.message;
    }
}

// ----------------------------------------
// Logout
// ----------------------------------------

function logout() {
    session.token = null;
    session.user = null;
    location.reload();
}

// ----------------------------------------
// Scroll
// ----------------------------------------

function scrollToFeatures() {
    document.getElementById('features').scrollIntoView({ behavior: 'smooth' });
}

// Close modal on Escape
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeAllModals();
});
