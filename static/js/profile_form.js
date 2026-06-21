(function () {
    'use strict';

    function formatPhoneInput(input) {
        var digits = input.value.replace(/\D/g, '');
        if (digits.startsWith('8')) {
            digits = '7' + digits.slice(1);
        }
        if (digits.startsWith('7')) {
            digits = digits.slice(1);
        }
        digits = digits.slice(0, 10);

        if (!digits) {
            input.value = '';
            return;
        }

        var formatted = '+7';
        if (digits.length > 0) {
            formatted += ' (' + digits.slice(0, 3);
        }
        if (digits.length >= 3) {
            formatted += ') ' + digits.slice(3, 6);
        }
        if (digits.length >= 6) {
            formatted += '-' + digits.slice(6, 8);
        }
        if (digits.length >= 8) {
            formatted += '-' + digits.slice(8, 10);
        }
        input.value = formatted;
    }

    function initPhoneMasks() {
        document.querySelectorAll('[data-phone-mask]').forEach(function (input) {
            input.addEventListener('input', function () {
                formatPhoneInput(input);
            });
            input.addEventListener('focus', function () {
                if (!input.value) {
                    input.value = '+7 (';
                }
            });
            input.addEventListener('blur', function () {
                if (input.value === '+7 (' || input.value === '+7') {
                    input.value = '';
                }
            });
        });
    }

    function initGradientPreview() {
        var preview = document.querySelector('[data-gradient-preview]');
        if (!preview) {
            return;
        }

        var startInput = document.querySelector('[name="cover_gradient_start"]');
        var endInput = document.querySelector('[name="cover_gradient_end"]');
        if (!startInput || !endInput) {
            return;
        }

        function updatePreview() {
            var start = startInput.value || '#EC4899';
            var end = endInput.value || '#8B5CF6';
            preview.style.background = 'linear-gradient(135deg, ' + start + ' 0%, ' + end + ' 100%)';
        }

        startInput.addEventListener('input', updatePreview);
        endInput.addEventListener('input', updatePreview);
        updatePreview();
    }

    function initExtraSocialLinks() {
        var container = document.querySelector('[data-extra-social-container]');
        var addBtn = document.getElementById('add-social-link-btn');
        var template = document.getElementById('extra-social-row-template');
        if (!container || !addBtn || !template) {
            return;
        }

        function bindRemoveButtons(scope) {
            scope.querySelectorAll('[data-remove-social-row]').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    var row = btn.closest('[data-extra-social-row]');
                    if (row) {
                        row.remove();
                    }
                });
            });
        }

        addBtn.addEventListener('click', function () {
            var clone = template.content.cloneNode(true);
            container.appendChild(clone);
            bindRemoveButtons(container);
        });

        bindRemoveButtons(container);
    }

    function initPhotoCardLinkFields() {
        var linkTypeSelect = document.querySelector('[name="link_type"]');
        if (!linkTypeSelect) {
            return;
        }

        var eventField = document.querySelector('.photocard-field-event');
        var coverField = document.querySelector('.photocard-field-cover');
        var urlField = document.querySelector('.photocard-field-url');

        function updateVisibility() {
            var value = linkTypeSelect.value;
            if (eventField) {
                eventField.style.display = value === 'event' ? '' : 'none';
            }
            if (coverField) {
                coverField.style.display = value === 'cover' ? '' : 'none';
            }
            if (urlField) {
                urlField.style.display = (value === 'performance' || value === 'url') ? '' : 'none';
            }
        }

        linkTypeSelect.addEventListener('change', updateVisibility);
        updateVisibility();
    }

    function initTabFromHash() {
        var hash = window.location.hash;
        if (!hash) {
            return;
        }
        var trigger = document.querySelector('[data-bs-target="' + hash + '"]');
        if (trigger && window.bootstrap && bootstrap.Tab) {
            bootstrap.Tab.getOrCreateInstance(trigger).show();
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        initPhoneMasks();
        initGradientPreview();
        initExtraSocialLinks();
        initPhotoCardLinkFields();
        initTabFromHash();
    });
})();
