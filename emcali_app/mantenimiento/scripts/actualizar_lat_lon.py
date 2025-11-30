import os
import sys
import django
import pandas as pd
from pathlib import Path

# === Configuración Django ===
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "emcali_app.settings")

django.setup()

from mantenimiento.models import Nodo

def actualizar_lat_lon():
    excel_path = os.path.join(BASE_DIR, "mantenimiento", "scripts", "nodos.xlsx")
    df = pd.read_excel(excel_path)

    # Normalizar columnas
    df.columns = df.columns.str.strip().str.lower()

    # Columnas esperadas
    if not all(col in df.columns for col in ["nodo", "lat", "lon"]):
        print("❌ El Excel NO contiene las columnas necesarias: nodo, lat, lon")
        print("Columnas encontradas:", df.columns.tolist())
        return

    actualizados = 0
    no_encontrados = []

    for _, row in df.iterrows():
        nodo_nombre = str(row["nodo"]).strip()

        try:
            nodo = Nodo.objects.get(nodo=nodo_nombre)

            # --- Actualiza coordenadas SIEMPRE ---
            nodo.latitud = float(row["lat"]) if pd.notna(row["lat"]) else None
            nodo.longitud = float(row["lon"]) if pd.notna(row["lon"]) else None

            nodo.save()
            actualizados += 1
            print(f"✔ Actualizado: {nodo_nombre}")

        except Nodo.DoesNotExist:
            no_encontrados.append(nodo_nombre)
            print(f"❌ No existe en BD: {nodo_nombre}")

    print("\n=============================")
    print(f"✅ Total actualizados: {actualizados}")
    print(f"❗ No encontrados: {len(no_encontrados)}")
    print("=============================")

if __name__ == "__main__":
    actualizar_lat_lon()
