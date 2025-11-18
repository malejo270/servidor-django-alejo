document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById('form-reco');
    const btnGuardar = document.getElementById('btn-guardar');
    const latInput = document.getElementById('latitud');
    const lonInput = document.getElementById('longitud');

    // --- Control de ubicación ---
    const puedeEditar = form.dataset.ordenId && document.querySelector('input[name="latitud"]').value;
    if (btnGuardar && !puedeEditar) btnGuardar.disabled = true;

    if (navigator.geolocation && (!latInput.value || !lonInput.value)) {
        navigator.geolocation.getCurrentPosition(
            pos => {
                latInput.value = pos.coords.latitude.toFixed(6);
                lonInput.value = pos.coords.longitude.toFixed(6);
                btnGuardar.disabled = false;
            },
            err => {
                console.warn("Error geolocalización:", err);
                btnGuardar.disabled = false;
            }
        );
    } else btnGuardar.disabled = false;

    // --- Mostrar/Ocultar detalles TELCO y MANTENIMIENTO ---
    const avisoTelco = document.getElementById("aviso_telco");
    const detalleTelco = document.getElementById("detalle_telco_container");

    const avisoMante = document.getElementById("aviso_mante");
    const detalleMante = document.getElementById("detalle_mante_container");

    if (avisoTelco && detalleTelco) {
        avisoTelco.addEventListener("change", () => {
            detalleTelco.classList.toggle("d-none", !avisoTelco.checked);
        });
    }

    if (avisoMante && detalleMante) {
        avisoMante.addEventListener("change", () => {
            detalleMante.classList.toggle("d-none", !avisoMante.checked);
        });
    }

    // --- Guardado localStorage (solo si es nuevo informe) ---
    const storageKey = "formRecoData_" + (form.dataset.ordenId || 'new');
    if (!puedeEditar) {
        form.querySelectorAll("input, textarea, select").forEach(field => {
            field.addEventListener("input", () => {
                const formData = new FormData(form);
                const data = {};
                for (let [key, value] of formData.entries()) data[key] = value;
                localStorage.setItem(storageKey, JSON.stringify(data));
            });
        });

        window.addEventListener("load", () => {
            const savedData = localStorage.getItem(storageKey);
            if (savedData) {
                const data = JSON.parse(savedData);
                for (let name in data) {
                    const field = form.querySelector(`[name="${name}"]`);
                    if (field) {
                        if (field.type === "checkbox") {
                            field.checked = data[name] === "on";
                            field.dispatchEvent(new Event('change'));
                        } else if (field.type !== "file") field.value = data[name];
                    }
                }
            }
        });
    }

    form.addEventListener("submit", () => {
        if (latInput && lonInput) {
            latInput.value = latInput.value.replace(",", ".");
            lonInput.value = lonInput.value.replace(",", ".");
        }
        localStorage.removeItem(storageKey);
    });

    // --- Vista previa de imágenes con botón X ---
    const fileInputs = document.querySelectorAll('input[type="file"][accept="image/*"]');

    fileInputs.forEach(input => {
      input.addEventListener("change", function (event) {
        const container = this.closest(".border");
        let previewDiv = container.querySelector(".preview-div");

        if (!previewDiv) {
          previewDiv = document.createElement("div");
          previewDiv.classList.add("preview-div", "position-relative", "mt-2");
          container.appendChild(previewDiv);
        }

        previewDiv.innerHTML = "";

        const file = event.target.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = function (e) {
            const img = document.createElement("img");
            img.src = e.target.result;
            img.classList.add("img-fluid", "rounded", "shadow-sm");
            img.style.maxHeight = "150px";
            img.style.objectFit = "cover";

            const removeBtn = document.createElement("button");
            removeBtn.innerHTML = "✖";
            removeBtn.type = "button";
            removeBtn.classList.add("btn", "btn-sm", "btn-danger", "position-absolute");
            removeBtn.style.top = "5px";
            removeBtn.style.right = "5px";
            removeBtn.style.borderRadius = "50%";
            removeBtn.style.padding = "3px 6px";
            removeBtn.style.lineHeight = "1";

            removeBtn.addEventListener("click", function () {
              input.value = "";
              previewDiv.innerHTML = "";
            });

            previewDiv.appendChild(img);
            previewDiv.appendChild(removeBtn);
          };
          reader.readAsDataURL(file);
        }
      });
    });
});