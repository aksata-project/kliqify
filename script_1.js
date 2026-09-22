
    
    
    const searchUser = (new URLSearchParams(window.location.search)).get("user");
    const pathUser = window.location.pathname.split("/").filter(Boolean).pop();
    const rawUser = searchUser || (pathUser && pathUser !== "login" && pathUser !== "register" && !pathUser.includes(".html") ? pathUser : null);
    const KLIQIFY_USER = (rawUser ? (function(u){try{return atob(u)}catch(e){return u;}})(rawUser) : null) || localStorage.getItem("kliqify_username");
    
    // Auto-persist the session so cross-domain redirects stay logged in
    if (KLIQIFY_USER) localStorage.setItem("kliqify_username", KLIQIFY_USER);

    if (!KLIQIFY_USER) {
        window.location.href = "https://kliqify.my.id/login";
    }
    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll(".kliqify-username-display").forEach(el => el.innerText = KLIQIFY_USER || "Guest");
        
        // Correctly apply user name to page subtitles on load if SPA logic relies on it
        if (typeof pageTitles !== 'undefined' && pageTitles.dashboard) {
            pageTitles.dashboard.subtitle = `Welcome back, ${KLIQIFY_USER}`;
        }
    });
    
    const GAS_APP_URL = "https://script.google.com/macros/s/AKfycbwfrvMHobcqELJknZzUButaPCZhnWQQbNyYldC_UIHcwQEzgLplcrhaz8lbkApHyvAB/exec";
    if (typeof google === 'undefined') {
        window.google = {
            script: {
                run: new Proxy({}, {
                    get: function(target, prop) {
                        if (prop === 'withSuccessHandler') return function(cb) { target.onSuccess = cb; return this; }.bind(target);
                        if (prop === 'withFailureHandler') return function(cb) { target.onFailure = cb; return this; }.bind(target);
                        
                        return function(...args) {
                            const payload = { action: prop, parameters: args };
                            fetch(GAS_APP_URL, {
                                method: 'POST',
                                mode: 'cors',
                                redirect: 'follow',
                                headers: { 'Content-Type': 'text/plain;charset=utf-8' },
                                body: JSON.stringify(payload)
                            })
                            .then(r => r.json())
                            .then(res => { if (target.onSuccess) target.onSuccess(res); })
                            .catch(err => { if (target.onFailure) target.onFailure(err); });
                        };
                    }
                })
            }
        };
    }
    
    