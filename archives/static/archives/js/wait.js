document.addEventListener('DOMContentLoaded', () => {
    const progressEl = document.getElementById('wait-progress');
    const textEl = document.getElementById('wait-text');
    const code = progressEl.dataset.code;
    const pollUrl = progressEl.dataset.progressUrl;

    async function poll() {
        const resp = await fetch(pollUrl);
        const data = await resp.json();
        const pct = data.pct || 0;
        progressEl.value = pct;
        textEl.textContent = pct + '%';

        if (pct < 100) {
            setTimeout(poll, 1000);
        } else {
            window.location.href = `/d/${code}/preview/`;
        }
    }

    poll();
});
