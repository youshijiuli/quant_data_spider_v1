// Quant Data Spider — Frontend app helpers
(function() {
    'use strict';

    // Clock updater
    function updateClock() {
        var el = document.getElementById('clock');
        if (el) {
            el.textContent = new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' });
        }
    }
    if (document.getElementById('clock')) {
        updateClock();
        setInterval(updateClock, 30000);
    }

    // Toast auto-dismiss
    document.addEventListener('htmx:afterSwap', function(evt) {
        var toast = evt.target.closest('.toast');
        if (toast) {
            var container = document.getElementById('toast-container');
            if (container) {
                container.appendChild(toast);
                setTimeout(function() { toast.remove(); }, 4000);
            }
        }
    });

    // Loading indicator on HTMX requests
    document.addEventListener('htmx:beforeRequest', function(evt) {
        var target = evt.detail.target;
        if (target.tagName === 'BUTTON') {
            target.disabled = true;
            target.setAttribute('data-original-text', target.textContent);
            target.textContent = '...';
        }
    });

    document.addEventListener('htmx:afterRequest', function(evt) {
        var target = evt.detail.target;
        if (target.tagName === 'BUTTON') {
            target.disabled = false;
            var orig = target.getAttribute('data-original-text');
            if (orig) target.textContent = orig;
        }
    });

    // Auto-select stock in chart picker if URL has /stock/TS_CODE
    if (window.location.pathname.startsWith('/charts/stock/')) {
        var code = window.location.pathname.split('/charts/stock/')[1];
        var picker = document.getElementById('stock-picker');
        if (picker && code) {
            picker.value = code;
        }
    }
})();
