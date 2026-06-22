(function () {
    'use strict';

    function initEventDetailMap() {
        var mapEl = document.getElementById('eventDetailMap');
        if (!mapEl || typeof L === 'undefined') {
            return;
        }

        var lat = parseFloat(mapEl.dataset.lat);
        var lng = parseFloat(mapEl.dataset.lng);
        if (isNaN(lat) || isNaN(lng)) {
            return;
        }

        var map = L.map(mapEl).setView([lat, lng], 15);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap',
            maxZoom: 19,
        }).addTo(map);
        L.marker([lat, lng]).addTo(map);

        setTimeout(function () {
            map.invalidateSize();
        }, 200);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initEventDetailMap);
    } else {
        initEventDetailMap();
    }
})();
