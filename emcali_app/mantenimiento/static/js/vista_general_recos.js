// Buscador
function buscar() {
    const input = document.getElementById("buscador").value.toLowerCase();
    const filas = document.querySelectorAll("#tabla tbody tr");

    filas.forEach(function(fila) {
        const nodo = fila.cells[0].textContent.toLowerCase();
        fila.style.display = nodo.includes(input) ? "" : "none";
    });
}

// Ocultar mensajes automáticamente después de 5 segundos
setTimeout(() => {
    const mensajes = document.getElementById("messages-container");
    if (mensajes) {
        mensajes.style.transition = "opacity 0.5s ease";
        mensajes.style.opacity = "0";
        setTimeout(() => mensajes.remove(), 500);
    }
}, 5000);
