(function () {
    'use strict';

    var DEBOUNCE_MS = 300;
    var debounceTimer = null;
    var activeIndex = -1;

    function initGlobalSearch() {
        var wrap = document.getElementById('globalSearchWrap');
        var input = document.getElementById('globalSearchInput');
        var dropdown = document.getElementById('globalSearchDropdown');
        if (!wrap || !input || !dropdown) {
            return;
        }

        var suggestUrl = wrap.dataset.suggestUrl || '/search/suggest/';
        var searchUrl = wrap.dataset.searchUrl || '/search/';

        function hideDropdown() {
            dropdown.classList.remove('show');
            dropdown.innerHTML = '';
            activeIndex = -1;
        }

        function renderResults(data) {
            if (!data.results || !data.results.length) {
                dropdown.innerHTML = '<div class="search-suggest-empty text-muted">Ничего не найдено</div>';
                dropdown.classList.add('show');
                return;
            }

            var html = '';
            var lastCategory = '';

            data.results.forEach(function (item, index) {
                if (item.category_label !== lastCategory) {
                    if (lastCategory) {
                        html += '</div>';
                    }
                    html += '<div class="search-suggest-group">';
                    html += '<div class="search-suggest-group-title">' + escapeHtml(item.category_label) + '</div>';
                    lastCategory = item.category_label;
                }

                var thumb = item.image_url
                    ? '<img src="' + escapeAttr(item.image_url) + '" alt="" class="search-suggest-thumb">'
                    : '<span class="search-suggest-thumb search-suggest-thumb-empty"><i class="bi bi-search"></i></span>';

                html += '<a href="' + escapeAttr(item.url) + '" class="search-suggest-item" data-index="' + index + '">';
                html += thumb;
                html += '<span class="search-suggest-text">';
                html += '<span class="search-suggest-title">' + escapeHtml(item.title) + '</span>';
                html += '<span class="search-suggest-subtitle">' + escapeHtml(item.subtitle) + '</span>';
                html += '</span></a>';
            });

            if (lastCategory) {
                html += '</div>';
            }

            html += '<a href="' + escapeAttr(data.search_url || (searchUrl + '?q=' + encodeURIComponent(data.query))) + '" class="search-suggest-all">';
            html += 'Показать все результаты (' + data.total + ')</a>';

            dropdown.innerHTML = html;
            dropdown.classList.add('show');
        }

        function fetchSuggestions(query) {
            fetch(suggestUrl + '?q=' + encodeURIComponent(query), {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            })
                .then(function (response) { return response.json(); })
                .then(renderResults)
                .catch(function () {
                    hideDropdown();
                });
        }

        input.addEventListener('input', function () {
            var query = input.value.trim();
            clearTimeout(debounceTimer);

            if (query.length < 2) {
                hideDropdown();
                return;
            }

            debounceTimer = setTimeout(function () {
                fetchSuggestions(query);
            }, DEBOUNCE_MS);
        });

        input.addEventListener('keydown', function (event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                var query = input.value.trim();
                if (query) {
                    window.location.href = searchUrl + '?q=' + encodeURIComponent(query);
                }
                return;
            }

            if (event.key === 'Escape') {
                hideDropdown();
                input.blur();
            }
        });

        document.addEventListener('click', function (event) {
            if (!wrap.contains(event.target)) {
                hideDropdown();
            }
        });

        input.addEventListener('focus', function () {
            if (input.value.trim().length >= 2 && dropdown.innerHTML) {
                dropdown.classList.add('show');
            }
        });
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }

    function escapeAttr(text) {
        return String(text || '')
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    document.addEventListener('DOMContentLoaded', initGlobalSearch);
})();
