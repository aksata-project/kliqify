const fs = require('fs');

const GAS_APP_URL = "https://script.google.com/macros/s/AKfycbwfrvMHobcqELJknZzUButaPCZhnWQQbNyYldC_UIHcwQEzgLplcrhaz8lbkApHyvAB/exec";
const LOGIN_PAGE_URL = "https://kliqify.cokroaksata.my.id";

function makeXmlSafe(htmlStr) {
    const booleanAttrs = ['required', 'disabled', 'checked', 'readonly', 'selected', 'multiple', 'autofocus', 'defer', 'async'];

    htmlStr = htmlStr.replace(/<[^>]+>/g, (tagContent) => {
        booleanAttrs.forEach(attr => {
            const regex = new RegExp(`(?<=\\s)${attr}\\b(?!\\s*=)`, 'ig');
            tagContent = tagContent.replace(regex, `${attr}="${attr}"`);
        });
        return tagContent;
    });

    const voidElements = ['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'];
    voidElements.forEach(tag => {
        const regex = new RegExp(`<${tag}\\b([^>]*?)(?<!/)>`, 'ig');
        htmlStr = htmlStr.replace(regex, `<${tag}$1/>`);
    });

    htmlStr = htmlStr.replace(/&(?![A-Za-z0-9#]+;)/g, '&amp;');
    htmlStr = htmlStr.replace(/&copy;/g, '&#169;')
        .replace(/&nbsp;/g, '&#160;')
        .replace(/&trade;/g, '&#8482;')
        .replace(/&reg;/g, '&#174;')
        .replace(/&middot;/g, '&#183;')
        .replace(/&bull;/g, '&#8226;')
        .replace(/&laquo;/g, '&#171;')
        .replace(/&raquo;/g, '&#187;');

    return htmlStr;
}

function processGasVariables(content, isHtmlContext = true) {
    if (isHtmlContext) {
        content = content.replace(/<\?= appUrl \?>/g, LOGIN_PAGE_URL);
        content = content.replace(/<\?= data\.appUrl \?>/g, LOGIN_PAGE_URL);

        content = content.replace(/<\?= userData\.Username \?>/g, '<span class="kliqify-username-display"></span>');
        content = content.replace(/<\?= userData\.Nama \?>/g, '<span class="kliqify-nama-display"></span>');
        content = content.replace(/<\?=\s*userData\.Status\s*\?>/g, '<span class="kliqify-userstatus-display"></span>');
        content = content.replace(/<\?= userData\.Username\.substring\(0,2\)\.toUpperCase\(\) \?>/g, '<span class="kliqify-userinitials-display"></span>');

        content = content.replace(/<\?= formatNumber\(userData\.Saldo\) \?>/g, '<span class="kliqify-saldo-display">0</span>');
        content = content.replace(/<\?= formatNumber\(userData\.Today_Earn\) \?>/g, '<span class="kliqify-todayearn-display">0</span>');
        content = content.replace(/<\?= formatNumber\(userData\.Total_View\) \?>/g, '<span class="kliqify-totalview-display">0</span>');
        content = content.replace(/<\?= formatNumber\(userData\.View_Today\) \?>/g, '<span class="kliqify-viewtoday-display">0</span>');
        content = content.replace(/<\?= formatNumber\(userData\.Withdraw_Pending \|\| 0\) \?>/g, '<span class="kliqify-withdrawpending-display">0</span>');
        content = content.replace(/<\?= formatNumber\(userData\.Withdraw_Success \|\| 0\) \?>/g, '<span class="kliqify-withdrawsuccess-display">0</span>');
        content = content.replace(/<\?= userData\.Status_Penarikan \|\| 'None' \?>/g, '<span class="kliqify-withdrawstatus-display">None</span>');

        content = content.replace(/<\?= userData\.Last_Activity_Type \|\| 'Belum ada aktivitas' \?>/g, '<span class="kliqify-activity-type">Belum ada aktivitas</span>');
        content = content.replace(/<\?= userData\.Last_Activity_Detail \|\| 'Aktivitas Anda akan muncul di sini\.' \?>/g, '<span class="kliqify-activity-detail">Aktivitas Anda akan muncul di sini.</span>');
        content = content.replace(/<\?= userData\.Announcement \|\| '' \?>/g, '<span class="kliqify-announcement-display"></span>');

        content = content.replace(/<\?\s*if\s*\(userData\s*&&\s*userData\.UserType.*?\)\s*\{\s*\?>/ig, '<!-- ADMIN_ONLY_START -->');
        content = content.replace(/<\?\s*\}\s*\?>/ig, '<!-- ADMIN_ONLY_END -->');

        content = content.replace(/<\?.*?\?>/gs, '');
    } else {
        content = content.replace(/['"]<\?= appUrl \?>['"]/g, `'${LOGIN_PAGE_URL}'`);
        content = content.replace(/['"]<\?= data\.appUrl \?>['"]/g, `'${LOGIN_PAGE_URL}'`);
        content = content.replace(/<\?= appUrl \?>/g, `'${LOGIN_PAGE_URL}'`);
        content = content.replace(/<\?= data\.appUrl \?>/g, `'${LOGIN_PAGE_URL}'`);
        content = content.replace(/<\?= userData\.Username \?>/g, '"+(localStorage.getItem("kliqify_username") || "")+"');
        content = content.replace(/<\?= userData\.Nama \?>/g, '"+(localStorage.getItem("kliqify_username") || "")+"');
        content = content.replace(/<\?= isAdmin \?>/g, 'false');
        content = content.replace(/<\?!= JSON\.stringify\(chartData\) \?>/g, '{ labels: [], views: [], earnings: [] }');
        content = content.replace(/chartData = ;/g, 'chartData = { labels: [], views: [], earnings: [] };');
        content = content.replace(/<\?= userData\.Today_Earn \|\| 0 \?>/g, '0');
        content = content.replace(/<\?= userData\.View_Today \|\| 0 \?>/g, '0');
        content = content.replace(/<\?= JSON\.stringify\(userData\.UserType \? userData\.UserType\.toLowerCase\(\) === 'admin' : false\) \?>/g, 'false');
        content = content.replace(/<\?.*?\?>/gs, '');
    }
    return content;
}

function scopeSelector(sel, p) {
    sel = sel.trim();
    if (!sel) return sel;
    if (sel.startsWith('@') || sel.startsWith(`.${p}-active`) || ['html', 'body', '*'].includes(sel)) {
        return sel;
    }
    return `.${p}-active ${sel}`;
}

function scopeRuleBlock(cssText, p) {
    let result = [];
    let i = 0;
    const n = cssText.length;

    while (i < n) {
        while (i < n && ' \t\n\r'.includes(cssText[i])) {
            result.push(cssText[i]);
            i++;
        }
        if (i >= n) break;

        let selectorStart = i;
        while (i < n && cssText[i] !== '{') {
            if (cssText[i] === '}') {
                result.push(cssText[i]);
                i++;
                selectorStart = i;
                continue;
            }
            i++;
        }

        if (i >= n) {
            result.push(cssText.substring(selectorStart));
            break;
        }

        let selectorText = cssText.substring(selectorStart, i).trim();

        let braceStart = i;
        let depth = 0;
        while (i < n) {
            if (cssText[i] === '{') depth++;
            else if (cssText[i] === '}') {
                depth--;
                if (depth === 0) {
                    i++;
                    break;
                }
            }
            i++;
        }

        let block = cssText.substring(braceStart, i);

        if (!selectorText) {
            result.push(block);
            continue;
        }

        if (selectorText.startsWith('@media') || selectorText.startsWith('@supports')) {
            let inner = block.substring(1, block.length - 1);
            let scopedInner = scopeRuleBlock(inner, p);
            result.push(`${selectorText} {${scopedInner}}`);
        } else if (selectorText.startsWith('@keyframes') || selectorText.startsWith('@font-face') || selectorText.startsWith('@')) {
            result.push(`${selectorText} ${block}`);
        } else {
            let selectors = selectorText.split(',').map(s => s.trim());
            let scoped = selectors.map(s => scopeSelector(s, p));
            result.push(scoped.join(', ') + " " + block);
        }
    }
    return result.join('');
}

function extractComponents(htmlFile, prefix) {
    if (!fs.existsSync(htmlFile)) {
        console.error(`File not found: ${htmlFile}`);
        return ["", "", "", "", []];
    }
    const content = fs.readFileSync(htmlFile, 'utf-8');

    let titleMatch = content.match(/<title>(.*?)<\/title>/i);
    let titleText = titleMatch ? titleMatch[1] : "Kliqify";

    let cssContent = "";
    const styleMatches = content.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/ig);
    for (const match of styleMatches) {
        let cssSegment = match[1];
        cssSegment = cssSegment.replace(/\/\*[\s\S]*?\*\//g, '');

        let rootVars = "";
        const rootMatch = cssSegment.match(/:root\s*\{([^}]*)\}/i);
        if (rootMatch) {
            rootVars = `:root {${rootMatch[1]}}\n`;
        }
        cssSegment = cssSegment.replace(/:root\s*\{[^}]*\}/ig, '');
        cssSegment = cssSegment.replace(/(?<![-a-zA-Z0-9_])body\s*\{/ig, `.${prefix}-active {`);

        if (prefix === 'dashboard') {
            cssSegment = cssSegment.replace(`.${prefix}-active {`, `.${prefix}-active { display: flex; height: 100vh; overflow: hidden; `);
            cssSegment = cssSegment.replace(/\.sidebar \{/g, `.${prefix}-active .sidebar {`);
            cssSegment = cssSegment.replace(/\.main-content \{/g, `.${prefix}-active .main-content {`);
        }
        cssContent += rootVars + scopeRuleBlock(cssSegment, prefix) + "\n";
    }

    let contentNoStyle = content.replace(/<style[^>]*>[\s\S]*?<\/style>/ig, '');

    let scripts = [];
    let scriptCounter = 0;

    let contentNoScripts = contentNoStyle.replace(/<script([^>]*)>([\s\S]*?)<\/script>/ig, (match, attrs, inner) => {
        inner = inner.replace(/\bconst\s+(CustomToast|CustomAlert|initialTodayEarn|initialViewToday|chartData|activityChart|ctx)\b/g, 'var $1');
        inner = processGasVariables(inner, false);
        const placeholder = `___SCRIPT_PLACEHOLDER_${prefix}_${Math.random()}___`;
        scripts.push({ placeholder, attrs, inner });
        scriptCounter++;
        return placeholder;
    });

    contentNoScripts = processGasVariables(contentNoScripts, true);

    let headMatch = contentNoScripts.match(/<head>([\s\S]*?)<\/head>/i);
    let headContent = headMatch ? headMatch[1] : "";
    headContent = headContent.replace(/<title>.*?<\/title>/ig, '');
    headContent = makeXmlSafe(headContent);

    let bodyMatch = contentNoScripts.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
    let bodyContent = bodyMatch ? bodyMatch[1] : "";
    bodyContent = makeXmlSafe(bodyContent);
    // DEBUG: check if body has admin pages
    console.log("Admin Dashboard found in body:", bodyContent.includes("page-admin-dashboard"));

    return [titleText, cssContent, headContent, bodyContent, scripts];
}

function buildDashboardXml() {
    let [t1, css1, head1, body1, scripts1] = extractComponents('dashboard.html', 'dashboard');
    let [t2, css2, head2, body2, scripts2] = extractComponents('login-register.html', 'login');

    const globalModalHtml = `
    <!-- Global SPA Modals -->
    <div id="toast-container" class="song-toast-container"></div>
    <div id="top-loader" style="position: fixed; top: 0; left: 0; width: 0%; height: 3px; background: #10b981; z-index: 99999; transition: width 0.3s ease, opacity 0.3s ease;"></div>
    <div id="loader-status-container" style="position: fixed; bottom: 20px; right: 20px; background: white; padding: 12px 20px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); display: none; align-items: center; gap: 12px; z-index: 99999; border: 1px solid #e2e8f0;">
        <div class="loader-spinner" style="width: 18px; height: 18px; border: 2px solid #d1fae5; border-top: 2px solid #10b981; border-radius: 50%; animation: spin 1s linear infinite; margin: 0;"></div>
        <div id="loader-status" style="font-size: 13px; font-weight: 600; color: #0f172a; font-family: 'Outfit', sans-serif;">Sedang menyiapkan dashboard...</div>
    </div>
    <div id="custom-modal-backdrop" class="custom-modal-backdrop">
        <div class="custom-modal-box">
            <div id="modal-icon" class="custom-modal-icon"><i class="fas fa-info"></i></div>
            <h3 id="modal-title" class="custom-modal-title">Title</h3>
            <p id="modal-message" class="custom-modal-message">Message goes here...</p>
            <div id="modal-actions" class="custom-modal-actions"></div>
        </div>
    </div>`;

    const stripPatterns = [
        /<!-- Shared Components:[^>]*-->/ig,
        /<!-- HTML Structure -->/ig,
        /<div id="toast-container"[^>]*>[\s\S]*?<\/div>/ig,
        /<div id="top-loader"[^>]*>[\s\S]*?<\/div>/ig,
        /<div id="loader-status-container"[^>]*>[\s\S]*?<div id="loader-status"[^>]*>[\s\S]*?<\/div>\s*<\/div>/ig,
        /<div id="custom-modal-backdrop"[^>]*>[\s\S]*?<div id="modal-actions"[^>]*>[\s\S]*?<\/div>\s*<\/div>\s*<\/div>/ig,
        /<!-- Premium Loading Overlay[\s\S]*?<div id="premium-loader".*?<\/div>\s*<\/div>/ig
    ];

    for (let p of stripPatterns) {
        body1 = body1.replace(p, '');
        body2 = body2.replace(p, '');
    }
    console.log("Admin Dashboard found in body AFTER strip check:", body1.includes("page-admin-dashboard"));

    const mergedCss = `
    /* === SKELETON LOADER (Cacing) === */
    .skeleton { background: #e2e8f0; background: linear-gradient(90deg, #f1f5f9 25%, #f8fafc 50%, #f1f5f9 75%); background-size: 200% 100%; animation: skeleton-loading 1.5s infinite; border-radius: 8px; position: relative; overflow: hidden; }
    @keyframes skeleton-loading { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
    .skeleton-text { height: 14px; margin-bottom: 8px; width: 100%; }
    .skeleton-text.short { width: 60%; }
    .skeleton-title { height: 24px; margin-bottom: 12px; width: 40%; }
    .skeleton-card { height: 120px; width: 100%; }
    .skeleton-circle { width: 48px; height: 48px; border-radius: 50%; }
    .is-loading .hide-on-load { display: none !important; }
    .is-loading .show-on-load { display: block !important; }
    .show-on-load { display: none; }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    @keyframes pulseScale { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }

    ${css1}
    ${css2}
    
    body, html { margin: 0; padding: 0; min-height: 100vh; }
    .dashboard-active, .login-active { min-height: 100vh; width: 100%; box-sizing: border-box; }
    .login-active { display: flex; align-items: center; justify-content: center; }
    
    .song-toast-container { position: fixed; bottom: 24px; right: 24px; z-index: 10000; display: flex; flex-direction: column; gap: 12px; pointer-events: none; }
    .song-toast { background: white; box-shadow: 0 10px 30px -5px rgba(0,0,0,0.15); border-radius: 12px; padding: 14px 20px; min-width: 300px; max-width: 400px; display: flex; align-items: flex-start; gap: 14px; transform: translateX(120%); transition: transform 0.4s cubic-bezier(0.16,1,0.3,1), opacity 0.4s ease; border-left: 4px solid #cbd5e1; pointer-events: auto; font-family: 'Outfit', sans-serif; opacity: 0; }
    .song-toast.show { transform: translateX(0); opacity: 1; }
    .song-toast.success { border-left-color: #10b981; } .song-toast.error { border-left-color: #ef4444; } .song-toast.warning { border-left-color: #f59e0b; } .song-toast.info { border-left-color: #3b82f6; }
    .song-toast-icon { font-size: 20px; margin-top: 2px; }
    .song-toast.success .song-toast-icon { color: #10b981; } .song-toast.error .song-toast-icon { color: #ef4444; } .song-toast.warning .song-toast-icon { color: #f59e0b; } .song-toast.info .song-toast-icon { color: #3b82f6; }
    .song-toast-content { flex: 1; }
    .song-toast-title { font-weight: 600; font-size: 15px; color: #0f172a; margin-bottom: 2px; }
    .song-toast-message { font-size: 14px; color: #64748b; line-height: 1.4; }
    .song-toast-close { background: none; border: none; padding: 4px; cursor: pointer; color: #94a3b8; transition: color 0.2s; }
    .song-toast-close:hover { color: #0f172a; }
    
    .custom-modal-backdrop { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15,23,42,0.6); backdrop-filter: blur(8px); z-index: 10001; display: flex; align-items: center; justify-content: center; opacity: 0; pointer-events: none; transition: opacity 0.3s ease; }
    .custom-modal-backdrop.active { opacity: 1; pointer-events: auto; }
    .custom-modal-box { background: white; width: 90%; max-width: 420px; padding: 32px; border-radius: 20px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25); text-align: center; transform: scale(0.95) translateY(10px); transition: all 0.3s cubic-bezier(0.16,1,0.3,1); font-family: 'Outfit', sans-serif; position: relative; overflow: hidden; }
    .custom-modal-backdrop.active .custom-modal-box { transform: scale(1) translateY(0); }
    .custom-modal-icon { width: 64px; height: 64px; background: #f1f5f9; color: #64748b; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center; font-size: 28px; }
    .custom-modal-icon.success { background: #ecfdf5; color: #10b981; } .custom-modal-icon.error { background: #fee2e2; color: #ef4444; } .custom-modal-icon.warning { background: #fef3c7; color: #f59e0b; } .custom-modal-icon.info { background: #dbeafe; color: #3b82f6; }
    .custom-modal-title { font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 12px; }
    .custom-modal-message { font-size: 16px; color: #64748b; line-height: 1.6; margin-bottom: 28px; }
    .custom-modal-actions { display: flex; gap: 12px; justify-content: center; }
    .modal-btn { padding: 12px 24px; border-radius: 10px; font-weight: 600; font-size: 15px; cursor: pointer; transition: all 0.2s; border: none; font-family: inherit; }
    .modal-btn.primary { background: #10b981; color: white; flex: 1; } .modal-btn.primary:hover { background: #059669; }
    .modal-btn.secondary { background: #f1f5f9; color: #475569; flex: 1; } .modal-btn.secondary:hover { background: #e2e8f0; color: #0f172a; }
    .modal-btn.danger { background: #ef4444; color: white; flex: 1; } .modal-btn.danger:hover { background: #dc2626; }
    `;

    let mergedBody = `
    ${globalModalHtml}
    <div id="dashboard-app" class="dashboard-active" style="display:none;">${body1}</div>
    <div id="auth-app" class="login-active" style="display:none;">${body2}</div>
    `;
    console.log("Admin Dashboard found in merged body:", mergedBody.includes("page-admin-dashboard"));

    const COMMON_SCRIPTS = `
    var CustomToast = {
        show(message, type = 'success', title = null) {
            const container = document.getElementById('toast-container');
            if (!container) return;
            const toast = document.createElement('div');
            toast.className = \`song-toast \${type}\`;
            let iconClass = 'fa-check-circle';
            if (type === 'error') iconClass = 'fa-exclamation-circle';
            if (type === 'warning') iconClass = 'fa-exclamation-triangle';
            if (type === 'info') iconClass = 'fa-info-circle';
            const displayTitle = title || (type.charAt(0).toUpperCase() + type.slice(1));
            toast.innerHTML = \`<div class="song-toast-icon"><i class="fas \${iconClass}"></i></div>
                <div class="song-toast-content">
                    <div class="song-toast-title">\${displayTitle}</div>
                    <div class="song-toast-message">\${message}</div>
                </div>
                <button class="song-toast-close" onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>\`;
            container.appendChild(toast);
            requestAnimationFrame(() => toast.classList.add('show'));
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.classList.remove('show');
                    setTimeout(() => toast.remove(), 400);
                }
            }, 4000);
        }
    };
    var CustomAlert = {
        get backdrop() { return document.getElementById('custom-modal-backdrop'); },
        get titleEl() { return document.getElementById('modal-title'); },
        get msgEl() { return document.getElementById('modal-message'); },
        get iconEl() { return document.getElementById('modal-icon'); },
        get actionsEl() { return document.getElementById('modal-actions'); },
        _reset() {
            if (this.iconEl) this.iconEl.className = 'custom-modal-icon';
            if (this.actionsEl) this.actionsEl.innerHTML = '';
            if (this.titleEl) this.titleEl.innerText = '';
            if (this.msgEl) this.msgEl.innerText = '';
        },
        close() { if (this.backdrop) this.backdrop.classList.remove('active'); },
        show(title, message, type = 'info') {
            return new Promise((resolve) => {
                this._reset();
                if (!this.backdrop) return resolve(true);
                if (this.iconEl) {
                    this.iconEl.classList.add(type);
                    let iClass = 'fa-info';
                    if (type === 'success') iClass = 'fa-check';
                    if (type === 'error') iClass = 'fa-times';
                    if (type === 'warning') iClass = 'fa-exclamation';
                    this.iconEl.innerHTML = \`<i class="fas \${iClass}"></i>\`;
                }
                if (this.titleEl) this.titleEl.innerText = title;
                if (this.msgEl) this.msgEl.innerText = message;
                const btn = document.createElement('button');
                btn.className = \`modal-btn \${type==='error'?'danger':'primary'}\`;
                btn.innerText = 'OK';
                btn.onclick = () => { this.close(); resolve(true); };
                if (this.actionsEl) this.actionsEl.appendChild(btn);
                this.backdrop.classList.add('active');
            });
        },
        confirm(title, message, confirmText = 'Ya', cancelText = 'Batal', type = 'warning') {
            return new Promise((resolve) => {
                this._reset();
                if (!this.backdrop) return resolve(false);
                if (this.iconEl) {
                    this.iconEl.classList.add(type);
                    this.iconEl.innerHTML = \`<i class="fas fa-question"></i>\`;
                }
                if (this.titleEl) this.titleEl.innerText = title;
                if (this.msgEl) this.msgEl.innerText = message;
                const cancelBtn = document.createElement('button');
                cancelBtn.className = 'modal-btn secondary';
                cancelBtn.innerText = cancelText;
                cancelBtn.onclick = () => { this.close(); resolve(false); };
                const confirmBtn = document.createElement('button');
                confirmBtn.className = type === 'danger' ? 'modal-btn danger' : 'modal-btn primary';
                confirmBtn.innerText = confirmText;
                confirmBtn.onclick = () => { this.close(); resolve(true); };
                if (this.actionsEl) { this.actionsEl.appendChild(cancelBtn); this.actionsEl.appendChild(confirmBtn); }
                this.backdrop.classList.add('active');
            });
        }
    };
    function showToast(msg, type = 'success') { CustomToast.show(msg, type); }
    `;

    let seenScripts = new Set();
    const allScripts = [
        ...scripts1.map(s => ({ ...s, scriptPrefix: 'dashboard' })),
        ...scripts2.map(s => ({ ...s, scriptPrefix: 'login' }))
    ];

    for (let { placeholder, attrs, inner, scriptPrefix } of allScripts) {
        let innerStripped = inner.trim();

        if (['CustomToast', 'CustomAlert', 'function showToast'].some(k => inner.includes(k)) && inner.length < 1500) {
            head1 = head1.replace(placeholder, "");
            head2 = head2.replace(placeholder, "");
            mergedBody = mergedBody.replace(placeholder, "");
            continue;
        }

        if (seenScripts.has(innerStripped)) {
            head1 = head1.replace(placeholder, "");
            head2 = head2.replace(placeholder, "");
            mergedBody = mergedBody.replace(placeholder, "");
            continue;
        }

        if (scriptPrefix === 'dashboard' && inner.includes('window.addEventListener')) {
            inner += "\ndocument.body.classList.add('is-loading');";
        }

        if (innerStripped) {
            seenScripts.add(innerStripped);
            inner = inner.replace(/window\.top\.location\.href\s*=\s*['"]\/?\?page=login['"];/g, 'window.location.reload();');
            inner = inner.replace('function refreshDashboard() {', 'function refreshDashboard() {\n      if (!localStorage.getItem("kliqify_username")) return;');
            inner = inner.replace('const isAdmin =', 'isAdmin =');
            inner = inner.replace('const pageTitles =', 'pageTitles =');
            inner = inner.replace('const username =', 'username =');
            inner = inner.replace('const appUrl =', 'appUrl =');

            if (!inner.includes('<![CDATA[')) {
                inner = `\n//<![CDATA[\n${inner}\n//]]>\n`;
            }
        }

        const restoredScript = `<script${attrs}>${inner}</script>`;
        head1 = head1.replace(placeholder, restoredScript);
        head2 = head2.replace(placeholder, restoredScript);
        mergedBody = mergedBody.replace(placeholder, restoredScript);
    }
    console.log("Admin Dashboard found in merged body AFTER scripts check:", mergedBody.includes("page-admin-dashboard"));

    const routerScriptLogic = `
    const GAS_APP_URL = "${GAS_APP_URL}";
    window.isAdmin = false;
    window.pageTitles = {
      dashboard: { heading: 'Dashboard Overview', subtitle: 'Welcome back' },
      wallet: { heading: 'Wallet', subtitle: 'Kelola saldo dan tarik dana Anda' },
      history: { heading: 'History', subtitle: 'Riwayat pendapatan dan penarikan' },
      settings: { heading: 'Settings', subtitle: 'Pengaturan akun Anda' },
      admin: { heading: 'Admin Panel', subtitle: 'Kelola Seluruh Pengguna & Penarikan' }
    };
    
    document.addEventListener("DOMContentLoaded", () => {
        const path = window.location.pathname;
        const search = window.location.search;
        const KLIQIFY_USER = localStorage.getItem("kliqify_username");
        const KLIQIFY_PASS = localStorage.getItem("kliqify_password");
        const isLoggedIn = !!(KLIQIFY_USER && KLIQIFY_PASS);
        
        const isLoginRoute = path === '/login' || search.includes('page=login') || search.includes('page=register');
        const dashboardApp = document.getElementById('dashboard-app');
        const authApp = document.getElementById('auth-app');
        
        if (isLoginRoute || !isLoggedIn) {
            dashboardApp.style.display = 'none';
            authApp.style.display = '';
            if (search.includes('page=register') && typeof switchView === 'function') switchView('register');
            else {
                if (typeof switchView === 'function') switchView('login');
                if (typeof checkStoredLogin === 'function') checkStoredLogin();
            }
            window._dashboardReady = false;
        } else {
            dashboardApp.style.display = '';
            authApp.style.display = 'none';
            window._dashboardReady = true;
        }

        document.querySelectorAll(".kliqify-username-display").forEach(el => el.innerText = KLIQIFY_USER || "Guest");
        document.querySelectorAll(".kliqify-nama-display").forEach(el => el.innerText = localStorage.getItem("kliqify_nama") || KLIQIFY_USER || "Guest");
        document.querySelectorAll(".kliqify-userstatus-display").forEach(el => el.innerText = localStorage.getItem("kliqify_status") || "Active");
        document.querySelectorAll(".kliqify-userinitials-display").forEach(el => {
            const nick = KLIQIFY_USER || "GU";
            el.innerText = nick.substring(0, 2).toUpperCase();
        });
        
        window.isAdmin = localStorage.getItem("kliqify_role") === "admin";
        if (window.pageTitles && window.pageTitles.dashboard) {
            window.pageTitles.dashboard.subtitle = 'Welcome back, ' + (KLIQIFY_USER || 'User');
        }

        const isAdminValue = window.isAdmin;
        document.querySelectorAll(".admin-only-wrapper").forEach(el => el.style.display = isAdminValue ? "block" : "none");
        document.querySelectorAll(".admin-only").forEach(el => el.style.display = isAdminValue ? "flex" : "none");
    });

    if (typeof google === 'undefined') {
        function createGASRunner() {
            let handlers = {};
            const proxy = new Proxy({}, {
                get: function(target, prop) {
                    if (prop === 'withSuccessHandler') return function(cb) { handlers.onSuccess = cb; return proxy; };
                    if (prop === 'withFailureHandler') return function(cb) { handlers.onFailure = cb; return proxy; };
                    return function(...args) {
                        const myHandlers = handlers;
                        handlers = {};
                        const payload = { action: prop, parameters: args };
                        fetch(GAS_APP_URL, {
                            method: 'POST',
                            mode: 'cors',
                            redirect: 'follow',
                            headers: { 'Content-Type': 'text/plain;charset=utf-8' },
                            body: JSON.stringify(payload)
                        })
                        .then(r => {
                            const ct = r.headers.get('content-type') || '';
                            if (ct.includes('application/json')) return r.json();
                            return r.text().then(txt => {
                                try { return JSON.parse(txt); } catch(e) { throw new Error('Server returned non-JSON response'); }
                            });
                        })
                        .then(res => { if (myHandlers.onSuccess) myHandlers.onSuccess(res); })
                        .catch(err => { if (myHandlers.onFailure) myHandlers.onFailure(err); });
                    };
                }
            });
            return proxy;
        }
        window.google = { script: { run: createGASRunner() } };
    }
    
    function initiatePWA() {
        if ('serviceWorker' in navigator) { /* basic sw check */ }
    }
    window.addEventListener('load', initiatePWA);
    `;

    let finalXml = `<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html>
<html b:css='false' b:defaultwidgetversion='2' b:layoutsVersion='3' b:responsive='true' b:templateUrl='vegeclub.xml' b:templateVersion='1.0.0' expr:dir='data:blog.languageDirection' xmlns='http://www.w3.org/1999/xhtml' xmlns:b='http://www.google.com/2005/gml/b' xmlns:data='http://www.google.com/2005/gml/data' xmlns:expr='http://www.google.com/2005/gml/expr'>
<head>
  <b:include data='blog' name='all-head-content'/>
  <title>Kliqify URL Shortener</title>
  ${head1}
  <b:skin><![CDATA[${mergedCss}]]></b:skin>
  <b:template-skin><![CDATA[]]></b:template-skin>
</head>
<body>
  <b:section class='main' id='main' showaddelement='yes'>
    <b:widget id='Blog1' locked='true' title='Blog Posts' type='Blog'>
      <b:includable id='main'>
         <!-- SPA Wrapper -->
         <div id="kliqify-spa-root">
             ${mergedBody}
         </div>
      </b:includable>
    </b:widget>
  </b:section>
  <script>//<![CDATA[
    ${COMMON_SCRIPTS}
    ${routerScriptLogic}
  //]]></script>
</body>
</html>`;

    // A few more XML compliance fixes
    // Removed the global & replacement because it was replacing && inside <script> blocks!
    fs.writeFileSync('dashboard.xml', finalXml, 'utf-8');
    console.log(`Generated 'dashboard.xml' (${finalXml.length} bytes).`);
}

buildDashboardXml();
