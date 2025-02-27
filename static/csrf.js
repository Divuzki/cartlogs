// CSRF Token Management
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

// Add CSRF token to all AJAX requests
function setupCSRFAjax() {
    // Get CSRF token from cookie if available
    const csrftoken = document.cookie.split(';')
        .find(cookie => cookie.trim().startsWith('csrftoken='))?.split('=')[1];

    if (csrftoken) {
        // Add CSRF token to all AJAX requests
        const oldXHROpen = window.XMLHttpRequest.prototype.open;
        window.XMLHttpRequest.prototype.open = function() {
            const result = oldXHROpen.apply(this, arguments);
            this.setRequestHeader('X-CSRFToken', csrftoken);
            return result;
        };

        // Add CSRF token to all fetch requests
        const originalFetch = window.fetch;
        window.fetch = function() {
            let [resource, config] = arguments;
            if (config === undefined) {
                config = {};
            }
            if (config.headers === undefined) {
                config.headers = {};
            }
            config.headers['X-CSRFToken'] = csrftoken;
            const result = originalFetch.apply(this, [resource, config]);
            return result;
        };
    }
}

// Initialize CSRF protection when DOM is loaded
document.addEventListener('DOMContentLoaded', setupCSRFAjax);