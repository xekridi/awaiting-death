document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("uploadForm");
    const progress = document.getElementById("uploadProgress");
    if (!form) return;

    form.addEventListener("submit", e => {
        e.preventDefault();
        progress.style.display = "block";
        progress.value = 0;

        const data = new FormData(form);
        const xhr = new XMLHttpRequest();
        xhr.open("POST", form.action);
        xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");

        xhr.upload.onprogress = evt => {
            if (evt.lengthComputable) {
                progress.value = Math.round(evt.loaded / evt.total * 100);
            }
        };

        xhr.onload = () => {
            const loc = xhr.getResponseHeader("Location");
            if (loc) {
                window.location.href = loc;
            } else if (xhr.status === 200) {
                try {
                    const j = JSON.parse(xhr.responseText);
                    if (j.wait_url) window.location.href = j.wait_url;
                } catch { }
            } else {
                alert("Ошибка загрузки: " + xhr.status);
            }
        };

        xhr.onerror = () => alert("Сетевая ошибка при загрузке");
        xhr.send(data);
    });
});
