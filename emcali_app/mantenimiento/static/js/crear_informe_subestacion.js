window.onload = function () {
    const btnGuardar = document.getElementById('btn-guardar');
    const form = document.getElementById('form-subestacion');

    // ⏱️ Hora de inicio
    if (!document.getElementById('hora_inicio').value) {
        document.getElementById('hora_inicio').value = new Date().toISOString();
    }

    // ✅ Restaurar datos escritos desde localStorage
    for (let i = 0; i < form.elements.length; i++) {
        let el = form.elements[i];
        if (el.name && localStorage.getItem(el.name)) {
            el.value = localStorage.getItem(el.name);
        }
    }

    // Guardar en localStorage cada cambio
    form.addEventListener('input', function (e) {
        if (e.target.name) {
            localStorage.setItem(e.target.name, e.target.value);
        }
    });

    // 🌍 Geolocalización
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function (position) {
                document.getElementById('id_latitud_sub').value = position.coords.latitude.toFixed(6);
                document.getElementById('id_longitud_sub').value = position.coords.longitude.toFixed(6);
                btnGuardar.disabled = false; // habilitar botón
            },
            function () {
                alert("⚠️ Debes activar la ubicación para poder enviar el formulario.");
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
    } else {
        alert("Tu navegador no soporta geolocalización.");
    }

    // ⏱️ Hora de cierre antes de enviar
    form.addEventListener('submit', function (e) {
        document.getElementById('hora_cierre').value = new Date().toISOString();

        const lat = document.getElementById('id_latitud_sub').value;
        const lon = document.getElementById('id_longitud_sub').value;

        if (!lat || !lon) {
            e.preventDefault();
            alert("⚠️ No se detectó tu ubicación, no puedes enviar el formulario.");
        } else {
            // 🗑️ Limpiar localStorage al enviar con éxito
            for (let i = 0; i < form.elements.length; i++) {
                let el = form.elements[i];
                if (el.name) {
                    localStorage.removeItem(el.name);
                }
            }
        }
    });
};
