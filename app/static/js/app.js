const TalknApp = {
    init() {
        this.setupFlashMessages();
        this.setupPasswordToggles();
    },

    setupFlashMessages() {

        document.querySelectorAll('.flash-message').forEach(msg => {
            msg.addEventListener('click', () => {
                msg.style.animation = 'slideDown 0.3s ease reverse';
                setTimeout(() => msg.remove(), 300);
            });
        });
    },

    setupPasswordToggles() {

        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.password-toggle-btn');
            if (!btn) return;
            e.preventDefault();

            const targetId = btn.getAttribute('data-target') || 'password';
            const group = btn.closest('.password-input-group');
            const input = document.getElementById(targetId) || (group ? group.querySelector('input') : null);
            if (!input) return;

            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';

            const newIconName = isPassword ? 'eye-off' : 'eye';
            btn.innerHTML = `<i data-lucide="${newIconName}"></i>`;
            if (window.lucide && window.lucide.createIcons) {
                window.lucide.createIcons();
            }
        });
    }
};

document.addEventListener('DOMContentLoaded', () => {
    TalknApp.init();
});
