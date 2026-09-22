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
LOGIN_PAGE_URL = f"{APP_URL}?page=login" # Redirects unauthorized users/logouts here

FILES_TO_CONVERT = [
    'landingpage.html'
]

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
    # Fix boolean attributes (e.g., required -> required="required") inside tags
    def fix_booleans(match):
        tag_content = match.group(0)
        boolean_attrs = ['required', 'disabled', 'checked', 'readonly', 'selected', 'multiple', 'autofocus', 'defer', 'async']
        for attr in boolean_attrs:
            # Match the attribute as a whole word, not followed by an equals sign
            pattern = re.compile(r'\b' + attr + r'\b(?!\s*=)', re.IGNORECASE)
            tag_content = pattern.sub(f'{attr}="{attr}"', tag_content)
        return tag_content
    
    html_str = re.sub(r'<[^>]+>', fix_booleans, html_str)

    # Self-close void elements commonly found in HTML
    void_elements = ['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr']
    for tag in void_elements:
        pattern = re.compile(r'<' + tag + r'\b([^>]*?)(?<!/)>', re.IGNORECASE)
        html_str = pattern.sub(r'<' + tag + r'\1/>', html_str)
    
    # Replace bare ampersands with &amp; if they are not already an entity
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

def process_html_variables(content):
    content = re.sub(r'<\?= appUrl \?>', APP_URL, content)
    content = re.sub(r'<\?= data\.appUrl \?>', APP_URL, content)
    content = content.replace('<?= userData.Username ?>', '<span class="kliqify-username-display"></span>')
    content = content.replace('<?= userData.Nama ?>', '<span class="kliqify-username-display"></span>')
    content = re.sub(r'<\?\s*if\s*\(userData\s*&&\s*userData\.UserType.*?\)\s*\{\s*\?>', '', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<\?\s*\}\s*\?>', '', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<\?.*?\?>', '', content, flags=re.DOTALL)
    return content

def process_js_variables(content):
    content = re.sub(r'[\'"]\<\?= appUrl \?\>[\'"]', f"'{APP_URL}'", content)
    content = re.sub(r'[\'"]\<\?= data\.appUrl \?\>[\'"]', f"'{APP_URL}'", content)
    content = re.sub(r'<\?= appUrl \?>', f"'{APP_URL}'", content)
    content = re.sub(r'<\?= data\.appUrl \?>', f"'{APP_URL}'", content)
    decode_js = '(function(w){let u=(new URLSearchParams(w.search)).get("user");if(!u)return"";try{return atob(u)}catch(e){return u;}})(window.location)'
    content = content.replace('<?= userData.Username ?>', f'"+({decode_js} || localStorage.getItem("kliqify_username") || "")+"')
    content = content.replace('<?= userData.Nama ?>', f'"+({decode_js} || localStorage.getItem("kliqify_username") || "")+"')
    content = re.sub(r'<\?= userData\.Today_Earn \|\| 0 \?>', '0', content)
    content = re.sub(r'<\?= userData\.View_Today \|\| 0 \?>', '0', content)
    content = re.sub(r'<\?!= JSON\.stringify\(chartData\) \?>', '{ labels: [], views: [], earnings: [] }', content)
    content = re.sub(r'<\?= JSON\.stringify\(userData\.UserType \? userData\.UserType\.toLowerCase\(\) === \'admin\' : false\) \?>', 'false', content)
    content = re.sub(r'<\?.*?\?>', '', content, flags=re.DOTALL)
    return content

def convert_to_blogger(html_file):
    if not os.path.exists(html_file):
        print(f"File not found: {html_file}")
        return
        
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Title extraction
    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
    title_text = title_match.group(1) if title_match else "Kliqify"

    # CSS extraction (<style>)
    css_content = ""
    style_matches = re.finditer(r'<style[^>]*>(.*?)</style>', content, re.IGNORECASE | re.DOTALL)
    for match in style_matches:
        css_content += match.group(1) + "\n"
    
    content_no_style = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.IGNORECASE | re.DOTALL)

    # Automatically Neutralize Blogger Widget Wrappers
    css_content += "\n    /* Fix Blogger Section Wrapper for Flex Layouts */\n"
    css_content += "    body .main.section {\n"
    css_content += "      display: contents;\n"
    css_content += "    }\n    div#main.main.section {\n"
    css_content += "      display: contents;\n"
    css_content += "    }\n    .widget {\n"
    css_content += "      display: contents;\n"
    css_content += "    }\n    .widget-content {\n"
    css_content += "      display: contents;\n"
    css_content += "    }\n"

    # ISOLATE SCRIPTS
    scripts = []
    def script_extractor(match):
        attrs = match.group(1)
        inner = match.group(2)
        inner = process_js_variables(inner) # Handle JS-specific GAS tags
        
        # Strip existing declarations that are now centralized
        if 'var CustomToast =' in inner or 'const CustomToast =' in inner or \
           'var CustomAlert =' in inner or 'const CustomAlert =' in inner or \
           'function showToast' in inner:
            return ""

        placeholder = f"___SCRIPT_PLACEHOLDER_{len(scripts)}___"
        scripts.append((attrs, inner))
        return placeholder
    
    content_no_scripts = re.sub(r'<script([^>]*)>(.*?)</script>', script_extractor, content_no_style, flags=re.IGNORECASE | re.DOTALL)
    
    # Process HTML-specific tags safely
    content_no_scripts = process_html_variables(content_no_scripts)

    # Head extraction
    head_match = re.search(r'<head>(.*?)</head>', content_no_scripts, re.IGNORECASE | re.DOTALL)
    head_content = head_match.group(1) if head_match else ""
    head_content = re.sub(r'<title>.*?</title>', '', head_content, flags=re.IGNORECASE)
    head_content = make_xml_safe(head_content)

    # Body extraction
    body_match = re.search(r'<body[^>]*>(.*?)</body>', content_no_scripts, re.IGNORECASE | re.DOTALL)
    body_content = body_match.group(1) if body_match else ""
    body_content = make_xml_safe(body_content)

    # Restore Scripts with CDATA wraps
    def script_restorer(match):
        idx_str = match.group(1)
        if not idx_str: return ""
        idx = int(idx_str)
        attrs, inner = scripts[idx]
        if inner.strip():
            # Encrypt the isolated script!
            inner = obfuscate_js(inner)
            inner = f"\n//<![CDATA[\n{inner}\n//]]>\n"
        return f"<script{attrs}>{inner}</script>"

    head_content = re.sub(r'___SCRIPT_PLACEHOLDER_(\d+)___', script_restorer, head_content)
    body_content = re.sub(r'___SCRIPT_PLACEHOLDER_(\d+)___', script_restorer, body_content)

    # === COMMON COMPONENTS (Consolidated) ===
    COMMON_SCRIPTS = """
    <script>
    //<![CDATA[
    var CustomToast = {
        show(message, type = 'success', title = null) {
            const container = document.getElementById('toast-container');
            if (!container) return;
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
            requestAnimationFrame(() => { toast.classList.add('show'); });
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
                    this.iconEl.innerHTML = `<i class="fas ${iClass}"></i>`;
                }
                if (this.titleEl) this.titleEl.innerText = title;
                if (this.msgEl) this.msgEl.innerText = message;
                const btn = document.createElement('button');
                btn.className = `modal-btn primary`;
                if (type === 'error') btn.className = `modal-btn danger`;
                btn.innerText = 'OK';
                btn.onclick = () => { this.close(); resolve(true); };
                if (this.actionsEl) this.actionsEl.appendChild(btn);
                this.backdrop.classList.add('active');
            });
        }
    };
    function showToast(msg, type = 'success') { CustomToast.show(msg, type); }
    //]]>
    </script>
    """

    # GAS Proxy Polyfill injection + Auth Gatekeeper
    is_dashboard = 'dashboard.html' in html_file
    dashboard_gatekeeper = f"""
    const KLIQIFY_USER = localStorage.getItem("kliqify_username");
    const KLIQIFY_PASS = localStorage.getItem("kliqify_password");

    // STRICT ROUTING POLICY: If the browser lacks valid session tokens, absolutely boot the user to landing page.
    if (!KLIQIFY_USER || !KLIQIFY_PASS) {{
        window.location.href = "{LOGIN_PAGE_URL}";
    }}
    document.addEventListener("DOMContentLoaded", () => {{
        document.querySelectorAll(".kliqify-username-display").forEach(el => el.innerText = KLIQIFY_USER || "Guest");
        
        // Correctly apply user name to page subtitles on load if SPA logic relies on it
        if (typeof pageTitles !== 'undefined' && pageTitles.dashboard) {{
            pageTitles.dashboard.subtitle = `Welcome back, ${{KLIQIFY_USER}}`;
        }}

        // Auto-fetch dashboard data since fallback PHP tags are necessarily stripped
        if (typeof refreshDashboard === 'function') {{
            refreshDashboard();
        }}
    }});
    """ if is_dashboard else ""

    proxy_script = f"""
    <script>
    //<![CDATA[
    {dashboard_gatekeeper}
    const GAS_APP_URL = "{GAS_APP_URL}";
    if (typeof google === 'undefined') {{
        window.google = {{
            script: {{
                run: new Proxy({{}}, {{
                    get: function(target, prop, receiver) {{
                        if (prop === 'withSuccessHandler') return function(cb) {{ target.onSuccess = cb; return receiver; }};
                        if (prop === 'withFailureHandler') return function(cb) {{ target.onFailure = cb; return receiver; }};
                        
                        return function(...args) {{
                            const payload = {{ action: prop, parameters: args }};
                            fetch(GAS_APP_URL, {{
                                method: 'POST',
                                mode: 'cors',
                                redirect: 'follow',
                                headers: {{ 'Content-Type': 'text/plain;charset=utf-8' }},
                                body: JSON.stringify(payload)
                            }})
                            .then(r => r.json())
                            .then(res => {{ if (target.onSuccess) target.onSuccess(res); }})
                            .catch(err => {{ if (target.onFailure) target.onFailure(err); }});
                        }};
                    }}
                }})
            }}
        }};
    }}
    //]]>
    </script>
    """

    # Extruct JS from strings and obfuscate
    common_js_match = re.search(r'<script>\s*//<!\[CDATA\[(.*?)//\]\]>\s*</script>', COMMON_SCRIPTS, re.IGNORECASE | re.DOTALL)
    if common_js_match:
        obfuscated_common = obfuscate_js(common_js_match.group(1))
        COMMON_SCRIPTS = f"<script>\n//<![CDATA[\n{obfuscated_common}\n//]]>\n</script>"
        
    proxy_js_match = re.search(r'<script>\s*//<!\[CDATA\[(.*?)//\]\]>\s*</script>', proxy_script, re.IGNORECASE | re.DOTALL)
    if proxy_js_match:
        obfuscated_proxy = obfuscate_js(proxy_js_match.group(1))
        proxy_script = f"<script>\n//<![CDATA[\n{obfuscated_proxy}\n//]]>\n</script>"

    body_content = COMMON_SCRIPTS + "\n" + proxy_script + "\n" + body_content

    # The Blogger XML Template
    blogger_xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html>
<html b:css='false' b:defaultwidgetversion='2' b:layoutsVersion='3' b:responsive='true' b:templateUrl='vegeclub.xml' b:templateVersion='1.0.0' expr:dir='data:blog.languageDirection' xmlns='http://www.w3.org/1999/xhtml' xmlns:b='http://www.google.com/2005/gml/b' xmlns:data='http://www.google.com/2005/gml/data' xmlns:expr='http://www.google.com/2005/gml/expr'>
<head>
  <b:include data='blog' name='all-head-content'/>
  <title>{title_text}</title>
  {head_content}
  <b:skin><![CDATA[
{css_content}
  ]]></b:skin>
</head>
<body>
  <b:section class='main' id='main' showaddelement='yes'>
    <b:widget id='HTML1' locked='false' title='Main App' type='HTML' version='2' visible='true'>
      <b:includable id='main'>
{body_content}
      </b:includable>
    </b:widget>
  </b:section>
</body>
</html>
"""

    out_file = html_file.replace('.html', '.xml')
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(blogger_xml)
        
    print(f"Successfully converted {html_file} to {out_file}")

if __name__ == "__main__":
    for f in FILES_TO_CONVERT:
        convert_to_blogger(f)
