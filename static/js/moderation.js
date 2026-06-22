(function () {
    'use strict';

    function readStopWords() {
        var node = document.getElementById('kver-stop-words');
        if (!node || !node.textContent) {
            return [];
        }
        try {
            return JSON.parse(node.textContent);
        } catch (error) {
            return [];
        }
    }

    function escapeRegex(value) {
        return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    function containsStopWords(text, stopWords) {
        if (!text) {
            return false;
        }
        var normalized = text.toLowerCase();
        for (var i = 0; i < stopWords.length; i += 1) {
            var pattern = new RegExp('(?<!\\w)' + escapeRegex(stopWords[i]) + '(?!\\w)', 'iu');
            if (pattern.test(normalized)) {
                return true;
            }
        }
        return false;
    }

    function showPolicyModal() {
        var modalEl = document.getElementById('moderationPolicyModal');
        if (!modalEl || typeof bootstrap === 'undefined') {
            window.alert('Нарушение политики платформы в связи с попыткой использования нецензурной лексики.');
            return;
        }
        bootstrap.Modal.getOrCreateInstance(modalEl).show();
    }

    function attachModeratedForms(stopWords) {
        document.querySelectorAll('form[data-moderated-form]').forEach(function (form) {
            if (form.dataset.moderationBound === '1') {
                return;
            }
            form.dataset.moderationBound = '1';

            form.addEventListener('submit', function (event) {
                var fields = (form.dataset.moderatedFields || '')
                    .split(',')
                    .map(function (item) { return item.trim(); })
                    .filter(Boolean);

                for (var i = 0; i < fields.length; i += 1) {
                    var field = form.querySelector('[name="' + fields[i] + '"]');
                    if (field && containsStopWords(field.value, stopWords)) {
                        event.preventDefault();
                        event.stopPropagation();
                        showPolicyModal();
                        field.focus();
                        return;
                    }
                }
            });
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        var stopWords = readStopWords();
        attachModeratedForms(stopWords);

        document.querySelectorAll('.alert.moderation').forEach(function () {
            showPolicyModal();
        });
    });

    window.KverModeration = {
        containsStopWords: containsStopWords,
        showPolicyModal: showPolicyModal,
    };
})();
