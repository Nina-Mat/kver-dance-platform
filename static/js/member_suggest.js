(function () {
    'use strict';

    var DEBOUNCE_MS = 250;

    function initMemberSuggest() {
        var wrap = document.querySelector('.member-suggest-wrap');
        var input = document.getElementById('memberUserInput');
        var dropdown = document.getElementById('memberSuggestDropdown');
        if (!wrap || !input || !dropdown) {
            return;
        }

        var suggestUrl = wrap.dataset.suggestUrl;
        var teamId = wrap.dataset.teamId || '';
        var debounceTimer = null;

        function hideDropdown() {
            dropdown.classList.remove('show');
            dropdown.innerHTML = '';
        }

        function escapeHtml(text) {
            var div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function renderResults(results) {
            if (!results.length) {
                dropdown.innerHTML = '<div class="member-suggest-empty text-muted">Нет подходящих подписок</div>';
                dropdown.classList.add('show');
                return;
            }

            var html = '';
            results.forEach(function (item) {
                html += '<button type="button" class="member-suggest-item" data-value="' + escapeHtml(item.label) + '">';
                html += escapeHtml(item.label);
                if (item.username !== item.nickname) {
                    html += ' <span class="text-muted">(' + escapeHtml(item.username) + ')</span>';
                }
                html += '</button>';
            });
            dropdown.innerHTML = html;
            dropdown.classList.add('show');

            dropdown.querySelectorAll('.member-suggest-item').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    input.value = btn.dataset.value;
                    hideDropdown();
                });
            });
        }

        function fetchSuggestions(query) {
            var url = suggestUrl + '?team_id=' + encodeURIComponent(teamId);
            if (query) {
                url += '&q=' + encodeURIComponent(query);
            }
            fetch(url, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            })
                .then(function (response) { return response.json(); })
                .then(function (data) { renderResults(data.results || []); })
                .catch(hideDropdown);
        }

        input.addEventListener('focus', function () {
            fetchSuggestions(input.value.trim());
        });

        input.addEventListener('input', function () {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function () {
                fetchSuggestions(input.value.trim());
            }, DEBOUNCE_MS);
        });

        document.addEventListener('click', function (event) {
            if (!wrap.contains(event.target)) {
                hideDropdown();
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMemberSuggest);
    } else {
        initMemberSuggest();
    }
})();
