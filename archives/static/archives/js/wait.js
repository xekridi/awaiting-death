(async function poll() {
    const r = await fetch(progressUrl, {
        credentials: 'same-origin'
    });
    if (!r.ok) {
        console.error('Ошибка сети при опросе статуса:', r.status);
        return;
    }
    const j = await r.json();
    if (j.status === 'ready') {
        window.location = downloadUrl;
        return;
    }
    if (j.status === 'error') {
        document.getElementById('msg').innerText = 'Ошибка: ' + j.message;
        return;
    }
    setTimeout(poll, 2500);
})();