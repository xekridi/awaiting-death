document.addEventListener("DOMContentLoaded", () => {
    const progressEl = document.getElementById("buildProgress");
    if (!progressEl) return;

    const poll = () => {
        fetch(window.progressUrl)
            .then(r => r.json())
            .then(data => {
                progressEl.value = data.pct;
                if (data.pct < 100) {
                    setTimeout(poll, 1000);
                } else {
                    window.location.href = window.downloadUrl;
                }
            })
            .catch(() => setTimeout(poll, 1000));
    };

    poll();
});
