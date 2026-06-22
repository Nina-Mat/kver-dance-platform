(function () {
    function initPostExpand(root) {
        root.querySelectorAll('[data-post-expand]').forEach(function (block) {
            if (block.dataset.expandReady) return;
            block.dataset.expandReady = '1';

            var content = block.querySelector('.post-text__content');
            var toggle = block.querySelector('.post-text__toggle');
            if (!content || !toggle) return;

            if (content.scrollHeight <= content.clientHeight + 4) {
                content.classList.remove('post-text__content--clamped');
                return;
            }

            toggle.hidden = false;
            toggle.addEventListener('click', function () {
                var expanded = content.classList.toggle('post-text__content--expanded');
                if (expanded) {
                    content.classList.remove('post-text__content--clamped');
                    toggle.textContent = 'Свернуть';
                } else {
                    content.classList.add('post-text__content--clamped');
                    toggle.textContent = 'Показать ещё';
                }
            });
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        initPostExpand(document);
    });
})();
