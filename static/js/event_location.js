(function () {
    'use strict';

    var DEBOUNCE_MS = 400;

    function initEventLocationMap() {
        var wrap = document.querySelector('.event-location-wrap');
        if (!wrap || typeof L === 'undefined') {
            return;
        }

        var input = document.getElementById('id_location');
        var latInput = document.getElementById('id_location_lat');
        var lngInput = document.getElementById('id_location_lng');
        var dropdown = document.getElementById('locationSuggestDropdown');
        var mapEl = document.getElementById('eventLocationMap');
        if (!input || !latInput || !lngInput || !dropdown || !mapEl) {
            return;
        }

        var suggestUrl = wrap.dataset.suggestUrl || '/events/location/suggest/';
        var debounceTimer = null;
        var map = L.map(mapEl).setView([47.2357, 39.7015], 11);
        var marker = null;

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap',
            maxZoom: 19,
        }).addTo(map);

        function hideDropdown() {
            dropdown.classList.remove('show');
            dropdown.innerHTML = '';
        }

        function escapeHtml(text) {
            var div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function setMarker(lat, lng) {
            if (marker) {
                map.removeLayer(marker);
            }
            marker = L.marker([lat, lng]).addTo(map);
            map.setView([lat, lng], 15);
        }

        function applyLocation(label, lat, lng) {
            input.value = label;
            latInput.value = lat;
            lngInput.value = lng;
            setMarker(lat, lng);
            hideDropdown();
        }

        function renderSuggestions(results) {
            if (!results.length) {
                dropdown.innerHTML = '<div class="location-suggest-empty text-muted">Адрес не найден</div>';
                dropdown.classList.add('show');
                return;
            }
            var html = '';
            results.forEach(function (item) {
                html += '<button type="button" class="location-suggest-item" data-label="' +
                    escapeHtml(item.label) + '" data-lat="' + item.lat + '" data-lng="' + item.lng + '">' +
                    escapeHtml(item.label) + '</button>';
            });
            dropdown.innerHTML = html;
            dropdown.classList.add('show');
            dropdown.querySelectorAll('.location-suggest-item').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    applyLocation(btn.dataset.label, parseFloat(btn.dataset.lat), parseFloat(btn.dataset.lng));
                });
            });
        }

        function fetchSuggestions(query) {
            fetch(suggestUrl + '?q=' + encodeURIComponent(query), {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            })
                .then(function (response) { return response.json(); })
                .then(function (data) { renderSuggestions(data.results || []); })
                .catch(hideDropdown);
        }

        input.addEventListener('input', function () {
            var query = input.value.trim();
            if (query.toLowerCase() === 'онлайн' || query.toLowerCase() === 'online') {
                latInput.value = '';
                lngInput.value = '';
                if (marker) {
                    map.removeLayer(marker);
                    marker = null;
                }
                hideDropdown();
                return;
            }
            clearTimeout(debounceTimer);
            if (query.length < 3) {
                hideDropdown();
                return;
            }
            debounceTimer = setTimeout(function () {
                fetchSuggestions(query);
            }, DEBOUNCE_MS);
        });

        document.addEventListener('click', function (event) {
            if (!wrap.contains(event.target)) {
                hideDropdown();
            }
        });

        var initialLat = parseFloat(latInput.value);
        var initialLng = parseFloat(lngInput.value);
        if (!isNaN(initialLat) && !isNaN(initialLng)) {
            setMarker(initialLat, initialLng);
        }

        setTimeout(function () {
            map.invalidateSize();
        }, 200);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initEventLocationMap);
    } else {
        initEventLocationMap();
    }
})();
