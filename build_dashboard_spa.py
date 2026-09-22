import os
import re
import json
import base64
import urllib.parse

def load_config():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for fname in ['config.json', 'config.example.json']:
        fpath = os.path.join(base_dir, fname)
        if os.path.exists(fpath):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
    return {}

_cfg = load_config()
GAS_APP_URL = _cfg.get("gas_app_url", "https://script.google.com/macros/s/AKfycbwfrvMHobcqELJknZzUButaPCZhnWQQbNyYldC_UIHcwQEzgLplcrhaz8lbkApHyvAB/exec")
APP_URL = _cfg.get("app_url", "https://kliqify.my.id")
LOGIN_PAGE_URL = APP_URL

def obfuscate_js(js_code):
    js_code = js_code.strip()
    if not js_code:
        return ""
    # URL encode to handle Unicode/special chars safely, then Base64 encode
    encoded_bytes = urllib.parse.quote(js_code).encode('utf-8')
    b64_str = base64.b64encode(encoded_bytes).decode('utf-8')
    # Return wrapper that decodes and evaluates
    return f"eval(decodeURIComponent(window.atob('{b64_str}')));"

def make_xml_safe(html_str):
    def fix_booleans(match):
        tag_content = match.group(0)
        boolean_attrs = ['required', 'disabled', 'checked', 'readonly', 'selected', 'multiple', 'autofocus', 'defer', 'async']
        for attr in boolean_attrs:
            # Match the attribute only if it's NOT followed by an equals sign.
            # We use a negative lookahead to ensure it's a standalone attribute.
            # Also ensure it's preceded by space or is at start of tag content.
            pattern = re.compile(r'(?<=\s)' + attr + r'\b(?!\s*=)', re.IGNORECASE)
            tag_content = pattern.sub(f'{attr}="{attr}"', tag_content)
        return tag_content
    
    html_str = re.sub(r'<[^>]+>', fix_booleans, html_str)

    void_elements = ['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr']
    for tag in void_elements:
        pattern = re.compile(r'<' + tag + r'\b([^>]*?)(?<!/)>', re.IGNORECASE)
        html_str = pattern.sub(r'<' + tag + r'\1/>', html_str)
    
    html_str = re.sub(r'&(?![A-Za-z0-9#]+;)', '&amp;', html_str)
    
    # Replace common HTML entities that Blogger XML rejects
    html_str = html_str.replace('&copy;', '&#169;')
    html_str = html_str.replace('&nbsp;', '&#160;')
    html_str = html_str.replace('&trade;', '&#8482;')
    html_str = html_str.replace('&reg;', '&#174;')
    html_str = html_str.replace('&middot;', '&#183;')
    html_str = html_str.replace('&bull;', '&#8226;')
    html_str = html_str.replace('&laquo;', '&#171;')
    html_str = html_str.replace('&raquo;', '&#187;')
    
    return html_str

def process_gas_variables(content, is_html_context=True):
    if is_html_context:
        # Handle dynamic variables in HTML text or attributes
        content = re.sub(r'<\?= appUrl \?>', APP_URL, content)
        content = re.sub(r'<\?= data\.appUrl \?>', APP_URL, content)
        
        # Username and Name displays
        content = content.replace('<?= userData.Username ?>', '<span class="kliqify-username-display"></span>')
        content = content.replace('<?= userData.Nama ?>', '<span class="kliqify-nama-display"></span>')
        
        # User details from localStorage (placeholders that JS will fill)
        content = re.sub(r'<\?=\s*userData\.Status\s*\?>', '<span class="kliqify-userstatus-display"></span>', content)
        content = content.replace('<?= userData.Username.substring(0,2).toUpperCase() ?>', '<span class="kliqify-userinitials-display"></span>')
        
        # Financial variables (Add specific classes for JS to target)
        content = content.replace('<?= formatNumber(userData.Saldo) ?>', '<span class="kliqify-saldo-display">0</span>')
        content = content.replace('<?= formatNumber(userData.Today_Earn) ?>', '<span class="kliqify-todayearn-display">0</span>')
        content = content.replace('<?= formatNumber(userData.Total_View) ?>', '<span class="kliqify-totalview-display">0</span>')
        content = content.replace('<?= formatNumber(userData.View_Today) ?>', '<span class="kliqify-viewtoday-display">0</span>')
        content = content.replace('<?= formatNumber(userData.Withdraw_Pending || 0) ?>', '<span class="kliqify-withdrawpending-display">0</span>')
        content = content.replace('<?= formatNumber(userData.Withdraw_Success || 0) ?>', '<span class="kliqify-withdrawsuccess-display">0</span>')
        content = content.replace('<?= userData.Status_Penarikan || \'None\' ?>', '<span class="kliqify-withdrawstatus-display">None</span>')

        # Fallback values
        content = content.replace('<?= userData.Last_Activity_Type || \'Belum ada aktivitas\' ?>', '<span class="kliqify-activity-type">Belum ada aktivitas</span>')
        content = content.replace('<?= userData.Last_Activity_Detail || \'Aktivitas Anda akan muncul di sini.\' ?>', '<span class="kliqify-activity-detail">Aktivitas Anda akan muncul di sini.</span>')
        content = content.replace('<?= userData.Announcement || \'\' ?>', '<span class="kliqify-announcement-display"></span>')
        
        # Control flow tags
        content = re.sub(r'<\?\s*if\s*\(userData\s*&&\s*userData\.UserType.*?\)\s*\{\s*\?>', '<!-- ADMIN_ONLY_START -->', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<\?\s*\}\s*\?>', '<!-- ADMIN_ONLY_END -->', content, flags=re.IGNORECASE | re.DOTALL)
        
        # General cleanup of any remaining tags
        content = re.sub(r'<\?.*?\?>', '', content, flags=re.DOTALL)
    else:
        content = re.sub(r'[\'"]\<\?= appUrl \?\>[\'"]', f"'{APP_URL}'", content)
        content = re.sub(r'[\'"]\<\?= data\.appUrl \?\>[\'"]', f"'{APP_URL}'", content)
        content = re.sub(r'<\?= appUrl \?>', f"'{APP_URL}'", content)
        content = re.sub(r'<\?= data\.appUrl \?>', f"'{APP_URL}'", content)
        content = content.replace('<?= userData.Username ?>', '"+(localStorage.getItem("kliqify_username") || "")+"')
        content = content.replace('<?= userData.Nama ?>', '"+(localStorage.getItem("kliqify_username") || "")+"')
        content = re.sub(r'<\?= isAdmin \?>', 'false', content)
        content = re.sub(r'<\?!= JSON\.stringify\(chartData\) \?>', '{ labels: [], views: [], earnings: [] }', content)
        content = content.replace('chartData = ;', 'chartData = { labels: [], views: [], earnings: [] };')
        content = re.sub(r'<\?= userData\.Today_Earn \|\| 0 \?>', '0', content)
        content = re.sub(r'<\?= userData\.View_Today \|\| 0 \?>', '0', content)
        content = re.sub(r'<\?= JSON\.stringify\(userData\.UserType \? userData\.UserType\.toLowerCase\(\) === \'admin\' : false\) \?>', 'false', content)
        content = re.sub(r'<\?.*?\?>', '', content, flags=re.DOTALL)
    return content

def extract_components(html_file, prefix):
    if not os.path.exists(html_file):
        print(f"File not found: {html_file}")
        return "", "", "", []
        
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Title extraction
    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
    title_text = title_match.group(1) if title_match else "Kliqify"

    # CSS extraction (<style>)
    css_content = ""
    style_matches = re.finditer(r'<style[^>]*>(.*?)</style>', content, re.IGNORECASE | re.DOTALL)
    for match in style_matches:
        css_segment = match.group(1)
        
        # Robust Scoping: Prefixes all non-at-rule selectors with the app-specific class
        # This prevents global bleeding (e.g., dashboard's .btn affecting login's .btn)
        def scope_selector(sel, p):
            """Prefix a single selector with .{p}-active unless it's already scoped or is a special selector."""
            sel = sel.strip()
            if not sel:
                return sel
            # Don't scope @-rules, already-scoped selectors, or html/body
            if sel.startswith('@') or sel.startswith(f'.{p}-active') or sel in ('html', 'body', '*'):
                return sel
            return f".{p}-active {sel}"

        def scope_rule_block(css_text, p):
            """Parse CSS text into top-level rule blocks using brace-balancing, then scope selectors."""
            result = []
            i = 0
            n = len(css_text)
            while i < n:
                # Skip whitespace
                while i < n and css_text[i] in ' \t\n\r':
                    result.append(css_text[i])
                    i += 1
                if i >= n:
                    break

                # Read the selector/at-rule part (everything before the opening brace)
                selector_start = i
                while i < n and css_text[i] != '{':
                    if css_text[i] == '}':
                        # Stray closing brace, just emit it
                        result.append(css_text[i])
                        i += 1
                        selector_start = i
                        continue
                    i += 1
                
                if i >= n:
                    # No opening brace found, emit remaining text as-is
                    result.append(css_text[selector_start:])
                    break

                selector_text = css_text[selector_start:i].strip()
                
                # Now read the full brace-balanced block including the opening '{'
                brace_start = i
                depth = 0
                while i < n:
                    if css_text[i] == '{':
                        depth += 1
                    elif css_text[i] == '}':
                        depth -= 1
                        if depth == 0:
                            i += 1
                            break
                    i += 1
                
                block = css_text[brace_start:i]  # includes { ... }
                
                if not selector_text:
                    result.append(block)
                    continue
                
                # Check if this is an @-rule (media query, keyframes, etc.)
                if selector_text.startswith('@media') or selector_text.startswith('@supports'):
                    # Recursively scope the inner rules
                    inner = block[1:-1]  # strip outer { }
                    scoped_inner = scope_rule_block(inner, p)
                    result.append(f"{selector_text} {{{scoped_inner}}}")
                elif selector_text.startswith('@keyframes') or selector_text.startswith('@font-face') or selector_text.startswith('@'):
                    # Don't scope keyframes or font-face internals
                    result.append(f"{selector_text} {block}")
                else:
                    # Regular rule: scope the selector(s)
                    selectors = [s.strip() for s in selector_text.split(',')]
                    scoped = [scope_selector(s, p) for s in selectors]
                    result.append(", ".join(scoped) + " " + block)
            
            return "".join(result)

        # Pre-process: strip CSS comments that corrupt selector parsing
        css_segment = re.sub(r'/\*.*?\*/', '', css_segment, flags=re.DOTALL)
        
        # Preserve :root CSS custom properties by extracting them before scoping
        # Merge ALL apps' :root vars so variables like --gradient from login are available
        root_vars = ""
        root_match = re.search(r':root\s*\{([^}]*)\}', css_segment, flags=re.IGNORECASE | re.DOTALL)
        if root_match:
            root_vars = f":root {{{root_match.group(1)}}}\n"
        # Remove :root blocks from the segment (they're hoisted globally)
        css_segment = re.sub(r':root\s*\{[^}]*\}', '', css_segment, flags=re.IGNORECASE | re.DOTALL)
        # Remap body to the app's wrapper class
        # Also ensure we catch body tags in media queries
        css_segment = re.sub(r'(?<![-a-zA-Z0-9_])body\s*\{', f'.{prefix}-active {{', css_segment, flags=re.IGNORECASE)
        
        # Crucial: If the body had display:flex, the remapped class needs it too
        # Many designs rely on body { display: flex; height: 100vh; overflow: hidden; }
        # We ensure these properties are preserved in the remapped class.
        # Crucial: If the body had display:flex, the remapped class needs it too
        # Many designs rely on body { display: flex; height: 100vh; overflow: hidden; }
        # We ensure these properties are preserved in the remapped class.
        if prefix == 'dashboard':
            # Dashboard specific fixes
            css_segment = css_segment.replace(f'.{prefix}-active {{', f'.{prefix}-active {{ display: flex; height: 100vh; overflow: hidden; ')
            # Fix Sidebar layout inside the active class
            css_segment = css_segment.replace('.sidebar {', f'.{prefix}-active .sidebar {{')
            css_segment = css_segment.replace('.main-content {', f'.{prefix}-active .main-content {{')
        
        css_content += root_vars + scope_rule_block(css_segment, prefix) + "\n"
    
    content_no_style = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.IGNORECASE | re.DOTALL)

    # ISOLATE SCRIPTS
    scripts = []
    def script_extractor(match):
        attrs = match.group(1)
        inner = match.group(2)
        
        # Prevent Identifier Redeclaration SyntaxErrors when merged into 1 SPA
        # Important for components like CustomAlert/CustomToast that might exist in both files
        inner = re.sub(r'\bconst\s+(CustomToast|CustomAlert|initialTodayEarn|initialViewToday|chartData|activityChart|ctx)\b', r'var \1', inner)
        
        inner = process_gas_variables(inner, is_html_context=False) 
        placeholder = f"___SCRIPT_PLACEHOLDER_{prefix}_{len(scripts)}___"
        scripts.append((placeholder, attrs, inner))
        return placeholder
    
    content_no_scripts = re.sub(r'<script([^>]*)>(.*?)</script>', script_extractor, content_no_style, flags=re.IGNORECASE | re.DOTALL)
    content_no_scripts = process_gas_variables(content_no_scripts, is_html_context=True)

    # Head extraction
    head_match = re.search(r'<head>(.*?)</head>', content_no_scripts, re.IGNORECASE | re.DOTALL)
    head_content = head_match.group(1) if head_match else ""
    head_content = re.sub(r'<title>.*?</title>', '', head_content, flags=re.IGNORECASE)
    head_content = make_xml_safe(head_content)

    # Body extraction
    body_match = re.search(r'<body[^>]*>(.*?)</body>', content_no_scripts, re.IGNORECASE | re.DOTALL)
    body_content = body_match.group(1) if body_match else ""
    body_content = make_xml_safe(body_content)

    return title_text, css_content, head_content, body_content, scripts

def build_dashboard_xml():
    # 1. Fetch Dashboard Components
    t1, css1, head1, body1, scripts1 = extract_components('dashboard.html', 'dashboard')
    
    # Fetch Login/Register Components
    t2, css2, head2, body2, scripts2 = extract_components('login-register.html', 'login')
    
    # We will manually inject a clean copy of the Modal HTML at the end of the body
    global_modal_html = """
    <!-- Global SPA Modals -->
    <div id="toast-container" class="song-toast-container"></div>
    
    <!-- Top Progress Bar (Subtle replacement for full-page loader) -->
    <div id="top-loader" style="position: fixed; top: 0; left: 0; width: 0%; height: 3px; background: #10b981; z-index: 99999; transition: width 0.3s ease, opacity 0.3s ease;"></div>

    <!-- Loading Status Indicator (Subtle bottom-right) -->
    <div id="loader-status-container" style="position: fixed; bottom: 20px; right: 20px; background: white; padding: 12px 20px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); display: none; align-items: center; gap: 12px; z-index: 99999; border: 1px solid #e2e8f0;">
        <div class="loader-spinner" style="width: 18px; height: 18px; border: 2px solid #d1fae5; border-top: 2px solid #10b981; border-radius: 50%; animation: spin 1s linear infinite; margin: 0;"></div>
        <div id="loader-status" style="font-size: 13px; font-weight: 600; color: #0f172a; font-family: 'Outfit', sans-serif;">Sedang menyiapkan dashboard...</div>
    </div>

    <div id="custom-modal-backdrop" class="custom-modal-backdrop">
        <div class="custom-modal-box">
            <div id="modal-icon" class="custom-modal-icon"><i class="fas fa-info"></i></div>
            <h3 id="modal-title" class="custom-modal-title">Title</h3>
            <p id="modal-message" class="custom-modal-message">Message goes here...</p>
            <div id="modal-actions" class="custom-modal-actions">
            </div>
        </div>
    </div>
    """
    
    # Define individual patterns to strip (Consolidation)
    # Since we are using CDATA, we can be much more liberal with stripping,
    # but we still need to avoid duplicate IDs for the final DOM.
    # We use simple lookaheads to match the specific container and its immediate closing tag.
    strip_patterns = [
        r'<!-- Shared Components:[^>]*-->',
        r'<!-- HTML Structure -->',
        r'<div id="toast-container"[^>]*>.*?</div>',
        r'<div id="top-loader"[^>]*>.*?</div>',
        r'<div id="loader-status-container"[^>]*>.*?<div id="loader-status"[^>]*>.*?</div>\s*</div>',
        r'<div id="custom-modal-backdrop"[^>]*>.*?<div id="modal-actions"[^>]*>.*?</div>\s*</div>\s*</div>',
        r'<!-- Premium Loading Overlay.*?<div id="premium-loader".*?</div>\s*</div>'
    ]
    
    # Apply stripping to both bodies
    for pattern in strip_patterns:
        body1 = re.sub(pattern, '', body1, flags=re.DOTALL | re.IGNORECASE)
        body2 = re.sub(pattern, '', body2, flags=re.DOTALL | re.IGNORECASE)

    # Merge CSS
    merged_css = f"""
    /* === SKELETON LOADER (Cacing) === */
    .skeleton {{
      background: #e2e8f0;
      background: linear-gradient(90deg, #f1f5f9 25%, #f8fafc 50%, #f1f5f9 75%);
      background-size: 200% 100%;
      animation: skeleton-loading 1.5s infinite;
      border-radius: 8px;
      position: relative;
      overflow: hidden;
    }}
    @keyframes skeleton-loading {{
      0% {{ background-position: 200% 0; }}
      100% {{ background-position: -200% 0; }}
    }}
    .skeleton-text {{ height: 14px; margin-bottom: 8px; width: 100%; }}
    .skeleton-text.short {{ width: 60%; }}
    .skeleton-title {{ height: 24px; margin-bottom: 12px; width: 40%; }}
    .skeleton-card {{ height: 120px; width: 100%; }}
    .skeleton-circle {{ width: 48px; height: 48px; border-radius: 50%; }}

    .is-loading .hide-on-load {{ display: none !important; }}
    .is-loading .show-on-load {{ display: block !important; }}
    .show-on-load {{ display: none; }}

    @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
    @keyframes pulseScale {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.05); }} }}

    /* --- DASHBOARD CSS --- */
    {css1}
    /* --- LOGIN CSS --- */
    {css2}
    
    /* Global fixes for the SPA router */
    body, html {{
        margin: 0;
        padding: 0;
        min-height: 100vh;
    }}
    /* When active, make the container fill the screen just like the body used to */
    .dashboard-active, .login-active {{
        min-height: 100vh; 
        width: 100%;
        box-sizing: border-box;
    }}
    .login-active {{
        display: flex; /* The login page relied on flexbox body */
        align-items: center;
        justify-content: center;
    }}
    
    /* === GLOBAL MODAL & TOAST (outside scoped apps) === */
    .song-toast-container {{
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 10000;
        display: flex;
        flex-direction: column;
        gap: 12px;
        pointer-events: none;
    }}
    .song-toast {{
        background: white;
        box-shadow: 0 10px 30px -5px rgba(0,0,0,0.15);
        border-radius: 12px;
        padding: 14px 20px;
        min-width: 300px;
        max-width: 400px;
        display: flex;
        align-items: flex-start;
        gap: 14px;
        transform: translateX(120%);
        transition: transform 0.4s cubic-bezier(0.16,1,0.3,1), opacity 0.4s ease;
        border-left: 4px solid #cbd5e1;
        pointer-events: auto;
        font-family: 'Outfit', sans-serif;
        opacity: 0;
    }}
    .song-toast.show {{ transform: translateX(0); opacity: 1; }}
    .song-toast.success {{ border-left-color: #10b981; }}
    .song-toast.error {{ border-left-color: #ef4444; }}
    .song-toast.warning {{ border-left-color: #f59e0b; }}
    .song-toast.info {{ border-left-color: #3b82f6; }}
    .song-toast-icon {{ font-size: 20px; margin-top: 2px; }}
    .song-toast.success .song-toast-icon {{ color: #10b981; }}
    .song-toast.error .song-toast-icon {{ color: #ef4444; }}
    .song-toast.warning .song-toast-icon {{ color: #f59e0b; }}
    .song-toast.info .song-toast-icon {{ color: #3b82f6; }}
    .song-toast-content {{ flex: 1; }}
    .song-toast-title {{ font-weight: 600; font-size: 15px; color: #0f172a; margin-bottom: 2px; }}
    .song-toast-message {{ font-size: 14px; color: #64748b; line-height: 1.4; }}
    .song-toast-close {{ background: none; border: none; padding: 4px; cursor: pointer; color: #94a3b8; transition: color 0.2s; }}
    .song-toast-close:hover {{ color: #0f172a; }}
    
    .custom-modal-backdrop {{
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background: rgba(15,23,42,0.6);
        backdrop-filter: blur(8px);
        z-index: 10001;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.3s ease;
    }}
    .custom-modal-backdrop.active {{
        opacity: 1;
        pointer-events: auto;
    }}
    .custom-modal-box {{
        background: white;
        width: 90%;
        max-width: 420px;
        padding: 32px;
        border-radius: 20px;
        box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
        text-align: center;
        transform: scale(0.95) translateY(10px);
        transition: all 0.3s cubic-bezier(0.16,1,0.3,1);
        font-family: 'Outfit', sans-serif;
        position: relative;
        overflow: hidden;
    }}
    .custom-modal-backdrop.active .custom-modal-box {{
        transform: scale(1) translateY(0);
    }}
    .custom-modal-icon {{
        width: 64px; height: 64px;
        background: #f1f5f9; color: #64748b;
        border-radius: 50%;
        margin: 0 auto 20px;
        display: flex; align-items: center; justify-content: center;
        font-size: 28px;
    }}
    .custom-modal-icon.success {{ background: #ecfdf5; color: #10b981; }}
    .custom-modal-icon.error {{ background: #fee2e2; color: #ef4444; }}
    .custom-modal-icon.warning {{ background: #fef3c7; color: #f59e0b; }}
    .custom-modal-icon.info {{ background: #dbeafe; color: #3b82f6; }}
    .custom-modal-title {{
        font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 12px;
    }}
    .custom-modal-message {{
        font-size: 16px; color: #64748b; line-height: 1.6; margin-bottom: 28px;
    }}
    .custom-modal-actions {{
        display: flex; gap: 12px; justify-content: center;
    }}
    .modal-btn {{
        padding: 12px 24px; border-radius: 10px; font-weight: 600;
        font-size: 15px; cursor: pointer; transition: all 0.2s;
        border: none; font-family: inherit;
    }}
    .modal-btn.primary {{ background: #10b981; color: white; flex: 1; }}
    .modal-btn.primary:hover {{ background: #059669; }}
    .modal-btn.secondary {{ background: #f1f5f9; color: #475569; flex: 1; }}
    .modal-btn.secondary:hover {{ background: #e2e8f0; color: #0f172a; }}
    .modal-btn.danger {{ background: #ef4444; color: white; flex: 1; }}
    .modal-btn.danger:hover {{ background: #dc2626; }}
    """

    # Start merging HTML (injected directly into one body wrapper)
    merged_body = f"""
    {global_modal_html}
    
    <div id="dashboard-app" class="dashboard-active" style="display:none;">
        {body1}
    </div>
    
    <div id="auth-app" class="login-active" style="display:none;">
        {body2}
    </div>
    """

    # === COMMON COMPONENTS (Consolidated) ===
    # These are handled centrally to avoid duplicates and null reference errors
    COMMON_SCRIPTS = """
    /**
     * Modern Toast Notification System (Consolidated)
     */
    var CustomToast = {
        show(message, type = 'success', title = null) {
            const container = document.getElementById('toast-container');
            if (!container) {
                console.error('[CustomToast] Container #toast-container not found');
                return;
            }
            const toast = document.createElement('div');
            toast.className = `song-toast ${type}`;

            let iconClass = 'fa-check-circle';
            if (type === 'error') iconClass = 'fa-exclamation-circle';
            if (type === 'warning') iconClass = 'fa-exclamation-triangle';
            if (type === 'info') iconClass = 'fa-info-circle';

            const displayTitle = title || (type.charAt(0).toUpperCase() + type.slice(1));

            toast.innerHTML = `
                <div class="song-toast-icon"><i class="fas ${iconClass}"></i></div>
                <div class="song-toast-content">
                    <div class="song-toast-title">${displayTitle}</div>
                    <div class="song-toast-message">${message}</div>
                </div>
                <button class="song-toast-close" onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>
            `;

            container.appendChild(toast);

            requestAnimationFrame(() => {
                toast.classList.add('show');
            });

            setTimeout(() => {
                if (toast.parentNode) {
                    toast.classList.remove('show');
                    setTimeout(() => toast.remove(), 400);
                }
            }, 4000);
        }
    };

    /**
     * Modern Alert & Confirm System (Consolidated)
     */
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

        close() {
            if (this.backdrop) this.backdrop.classList.remove('active');
        },

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
                    this.iconEl.innerHTML = `<i class="fas ${iClass}"></i>`;
                }

                if (this.titleEl) this.titleEl.innerText = title;
                if (this.msgEl) this.msgEl.innerText = message;

                const btn = document.createElement('button');
                btn.className = `modal-btn primary`;
                if (type === 'error') btn.className = `modal-btn danger`;
                btn.innerText = 'OK';
                btn.onclick = () => {
                    this.close();
                    resolve(true);
                };
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
                    this.iconEl.innerHTML = `<i class="fas fa-question"></i>`;
                }

                if (this.titleEl) this.titleEl.innerText = title;
                if (this.msgEl) this.msgEl.innerText = message;

                const cancelBtn = document.createElement('button');
                cancelBtn.className = 'modal-btn secondary';
                cancelBtn.innerText = cancelText;
                cancelBtn.onclick = () => {
                    this.close();
                    resolve(false);
                };

                const confirmBtn = document.createElement('button');
                confirmBtn.className = type === 'danger' ? 'modal-btn danger' : 'modal-btn primary';
                confirmBtn.innerText = confirmText;
                confirmBtn.onclick = () => {
                    this.close();
                    resolve(true);
                };

                if (this.actionsEl) {
                    this.actionsEl.appendChild(cancelBtn);
                    this.actionsEl.appendChild(confirmBtn);
                }

                this.backdrop.classList.add('active');
            });
        }
    };

    /**
     * Bridge function for legacy calls
     */
    function showToast(msg, type = 'success') {
        CustomToast.show(msg, type);
    }
    """

    # Restore ALL scripts from BOTH pages into their appropriate DOM nodes
    seen_scripts = set()
    all_scripts = [(p, a, i, 'dashboard') for p, a, i in scripts1] + \
                  [(p, a, i, 'login') for p, a, i in scripts2]

    for placeholder, attrs, inner, script_prefix in all_scripts:
        inner_stripped = inner.strip()
        
        # Strip small utility scripts that are now centralized (Toast/Alert/etc.)
        # But NEVER strip the large dashboard logic block (which contains navigateTo, etc.)
        if ('var CustomToast =' in inner or 'const CustomToast =' in inner or \
           'var CustomAlert =' in inner or 'const CustomAlert =' in inner or \
           'function showToast' in inner) and len(inner) < 1500:
            if placeholder in head1: head1 = head1.replace(placeholder, "")
            if placeholder in head2: head2 = head2.replace(placeholder, "")
            merged_body = merged_body.replace(placeholder, "")
            continue

        if inner_stripped in seen_scripts:
            if placeholder in head1: head1 = head1.replace(placeholder, "")
            if placeholder in head2: head2 = head2.replace(placeholder, "")
            merged_body = merged_body.replace(placeholder, "")
            continue
            
        # Ensure is-loading class is handled correctly on initial load
        if script_prefix == 'dashboard' and 'window.addEventListener' in inner:
             inner += "\ndocument.body.classList.add('is-loading');"

        if inner_stripped:
            seen_scripts.add(inner_stripped)
            
            # 2. Patch logout (redirects to ?page=login)
            # We use reload() to cleanly reset the SPA state and trigger the router logic
            inner = inner.replace('window.top.location.href = "/?page=login";', 'window.location.reload();')
            inner = inner.replace("window.top.location.href = '/?page=login';", 'window.location.reload();')
            inner = inner.replace('window.top.location.href = "?page=login";', 'window.location.reload();')
            inner = inner.replace("window.top.location.href = '?page=login';", 'window.location.reload();')

            # 3. Patch refreshDashboard to prevent loop if not logged in
            inner = inner.replace('function refreshDashboard() {', 'function refreshDashboard() {\n      if (!localStorage.getItem("kliqify_username")) return;')

            # 4. Surgically replace global consts to prevent redeclaration errors since we define them globally in router_script
            inner = inner.replace('const isAdmin =', 'isAdmin =')
            inner = inner.replace('const pageTitles =', 'pageTitles =')
            inner = inner.replace('const username =', 'username =')
            inner = inner.replace('const appUrl =', 'appUrl =')

            if '<![CDATA[' not in inner:
                inner = obfuscate_js(inner)
                inner = f"\n//<![CDATA[\n{inner}\n//]]>\n"
            else:
                # If it already had CDATA somehow, extract and obfuscate
                extracted = re.sub(r'//<!\[CDATA\[(.*?)//\]\]>', r'\1', inner, flags=re.DOTALL)
                inner = f"\n//<![CDATA[\n{obfuscate_js(extracted)}\n//]]>\n"
        
        restored_script = f"<script{attrs}>{inner}</script>"
        if placeholder in head1: head1 = head1.replace(placeholder, restored_script)
        if placeholder in head2: head2 = head2.replace(placeholder, restored_script)
        merged_body = merged_body.replace(placeholder, restored_script)
    
    # SPA Router Logic & GAS Proxy Polyfill
    router_script_logic = f"""
    const GAS_APP_URL = "{GAS_APP_URL}";
    
    // Global State for SPA Fidelity
    window.isAdmin = false;
    window.pageTitles = {{
      dashboard: {{ heading: 'Dashboard Overview', subtitle: 'Welcome back' }},
      wallet: {{ heading: 'Wallet', subtitle: 'Kelola saldo dan tarik dana Anda' }},
      history: {{ heading: 'History', subtitle: 'Riwayat pendapatan dan penarikan' }},
      settings: {{ heading: 'Settings', subtitle: 'Pengaturan akun Anda' }},
      admin: {{ heading: 'Admin Panel', subtitle: 'Kelola Seluruh Pengguna & Penarikan' }}
    }};
    
    document.addEventListener("DOMContentLoaded", () => {{
        const path = window.location.pathname;
        const search = window.location.search;
        
        const KLIQIFY_USER = localStorage.getItem("kliqify_username");
        const KLIQIFY_PASS = localStorage.getItem("kliqify_password");
        const isLoggedIn = !!(KLIQIFY_USER && KLIQIFY_PASS);
        
        const isLoginRoute = path === '/login' || search.includes('page=login') || search.includes('page=register');
        
        const dashboardApp = document.getElementById('dashboard-app');
        const authApp = document.getElementById('auth-app');
        
        if (isLoginRoute || !isLoggedIn) {{
            // Hide Dashboard, Show Auth
            dashboardApp.style.display = 'none';
            authApp.style.display = '';
            
            // Trigger specific view inside auth app
            if (search.includes('page=register')) {{
                if (typeof switchView === 'function') switchView('register');
            }} else {{
                if (typeof switchView === 'function') switchView('login');
                if (typeof checkStoredLogin === 'function') checkStoredLogin();
            }}

            // Disable dashboard load listeners to prevent loops
            window._dashboardReady = false;
        }} else {{
            // Hide Auth, Show Dashboard
            dashboardApp.style.display = '';
            authApp.style.display = 'none';
            window._dashboardReady = true;
        }}

        document.querySelectorAll(".kliqify-username-display").forEach(el => el.innerText = KLIQIFY_USER || "Guest");
        document.querySelectorAll(".kliqify-nama-display").forEach(el => el.innerText = localStorage.getItem("kliqify_nama") || KLIQIFY_USER || "Guest");
        
        // Populate new identity displays for 100% fidelity
        document.querySelectorAll(".kliqify-userstatus-display").forEach(el => el.innerText = localStorage.getItem("kliqify_status") || "Free Member");
        document.querySelectorAll(".kliqify-userinitials-display").forEach(el => {{
            const nick = KLIQIFY_USER || "GU";
            el.innerText = nick.substring(0, 2).toUpperCase();
        }});
        
        // Population of financial stats is handled in navigateTo or refreshDashboard in dashboard.html
        // But we ensure the classes exist for them to target.

        // Update Global State
        window.isAdmin = localStorage.getItem("kliqify_role") === "admin";
        if (window.pageTitles && window.pageTitles.dashboard) {{
            window.pageTitles.dashboard.subtitle = 'Welcome back, ' + (KLIQIFY_USER || 'User');
        }}

        // Handle Admin-only content visibility
        const isAdminValue = window.isAdmin;
        document.querySelectorAll(".admin-only-wrapper").forEach(el => {{
            el.style.display = isAdminValue ? "block" : "none";
        }});
        document.querySelectorAll(".admin-only").forEach(el => {{
            el.style.display = isAdminValue ? "flex" : "none";
        }});
        document.querySelectorAll(".user-only").forEach(el => {{
            el.style.display = isAdminValue ? "none" : "flex";
        }});
        
        // Initial data fetch is now handled by the dashboard's own 'load' event listener
        // to avoid duplicate calls and ensure proper sequencing.
    }});

    // Setup GAS Polyfill
    if (typeof google === 'undefined') {{
        function createGASRunner() {{
            let handlers = {{}};
            const proxy = new Proxy({{}}, {{
                get: function(target, prop) {{
                    if (prop === 'withSuccessHandler') return function(cb) {{ handlers.onSuccess = cb; return proxy; }};
                    if (prop === 'withFailureHandler') return function(cb) {{ handlers.onFailure = cb; return proxy; }};
                    return function(...args) {{
                        const myHandlers = handlers;
                        handlers = {{}};
                        const payload = {{ action: prop, parameters: args }};
                        fetch(GAS_APP_URL, {{
                            method: 'POST',
                            mode: 'cors',
                            redirect: 'follow',
                            headers: {{ 'Content-Type': 'text/plain;charset=utf-8' }},
                            body: JSON.stringify(payload)
                        }})
                        .then(r => {{
                            const ct = r.headers.get('content-type') || '';
                            if (ct.includes('application/json')) return r.json();
                            return r.text().then(txt => {{
                                try {{ return JSON.parse(txt); }}
                                catch(e) {{
                                    console.error('[GAS Polyfill] Non-JSON response:', txt.substring(0, 200));
                                    throw new Error('Server returned non-JSON response');
                                }}
                            }});
                        }})
                        .then(res => {{
                            if (myHandlers.onSuccess) myHandlers.onSuccess(res);
                        }})
                        .catch(err => {{
                            console.error('[GAS Polyfill] Error:', prop, err);
                            if (myHandlers.onFailure) myHandlers.onFailure(err);
                        }});
                    }};
                }}
            }});
            return proxy;
        }}
        window.google = {{
            script: {{
                get run() {{ return createGASRunner(); }}
            }}
        }};
    }}
    """
    # Obfuscate the consolidated scripts
    obfuscated_common = obfuscate_js(COMMON_SCRIPTS)
    obfuscated_router = obfuscate_js(router_script_logic)
    
    # Consolidate router logic and common scripts into a single clean block
    merged_logic = obfuscated_common + "\n" + obfuscated_router
    router_script = f"<script>\n//<![CDATA[\n{merged_logic}\n//]]>\n</script>"

    merged_body = router_script + merged_body

    blogger_xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html>
<html b:css='false' b:defaultwidgetversion='2' b:layoutsVersion='3' b:responsive='true' b:templateUrl='vegeclub.xml' b:templateVersion='1.0.0' expr:dir='data:blog.languageDirection' xmlns='http://www.w3.org/1999/xhtml' xmlns:b='http://www.google.com/2005/gml/b' xmlns:data='http://www.google.com/2005/gml/data' xmlns:expr='http://www.google.com/2005/gml/expr'>
<head>
  <b:include data='blog' name='all-head-content'/>
  <title>Kliqify URL Shortener</title>
  {head1}
  {head2}
  <b:skin><![CDATA[
{merged_css}
  ]]></b:skin>
</head>
<body>
  <b:section class='main' id='main' showaddelement='yes'>
    <b:widget id='HTML1' locked='false' title='Main App' type='HTML' version='2' visible='true'>
      <b:includable id='main'>
{merged_body}
      </b:includable>
    </b:widget>
  </b:section>
</body>
</html>
"""

    with open('dashboard.xml', 'w', encoding='utf-8') as f:
        f.write(blogger_xml)
        
    print(f"Successfully merged dashboard and auth into dashboard.xml")

if __name__ == "__main__":
    build_dashboard_xml()
