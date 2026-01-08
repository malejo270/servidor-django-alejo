import pandas as pd
from django.http import HttpResponse
from datetime import datetime

from mantenimiento.models import (
    Subestacion,
    Subestacion_comu_informe,
    RevisionSubestacion,
    Nodo,
    Reconectador,
    Comunicacion,
    Rol,
    Trabajador,
    Orden,
    InformeReco,
    FotoInformeReco,
    ComentarioIngeniero,
    HistoricoReco,
    Historicosubcomu,
)


def exportar_tablas_seleccionadas_excel():
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"backup_emcali_{fecha}.xlsx"

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'

    modelos = {
        "Subestacion": Subestacion,
        "Subestacion_comu_informe": Subestacion_comu_informe,
        "RevisionSubestacion": RevisionSubestacion,
        "Nodo": Nodo,
        "Reconectador": Reconectador,
        "Comunicacion": Comunicacion,
        "Rol": Rol,
        "Trabajador": Trabajador,
        "Orden": Orden,
        "InformeReco": InformeReco,
        "FotoInformeReco": FotoInformeReco,
        "ComentarioIngeniero": ComentarioIngeniero,
        "HistoricoReco": HistoricoReco,
        "Historicosubcomu": Historicosubcomu,
    }

    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        for nombre_hoja, modelo in modelos.items():
            qs = modelo.objects.all().values()

            if not qs.exists():
                continue

            df = pd.DataFrame(list(qs))

            # 🔥 SOLUCIÓN CLAVE: quitar timezone de columnas datetime
            for columna in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[columna]):
                    df[columna] = df[columna].dt.tz_localize(None)

            df.to_excel(
                writer,
                sheet_name=nombre_hoja[:31],  # límite de Excel
                index=False
            )

    return response
