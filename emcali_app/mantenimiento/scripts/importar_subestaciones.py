import os
import sys
import django
from pathlib import Path
import pandas as pd

# === Configuración Django ===
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # sube hasta la raíz del proyecto (donde está manage.py)
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emcali_app.settings')  # asegúrate de que el nombre del proyecto sea correcto
django.setup()

# Importar modelo desde tu app mantenimiento
from mantenimiento.models import Subestacion

def importar_subestaciones():
    # Ruta al Excel
    excel_path = os.path.join(BASE_DIR, "mantenimiento", "scripts", "nuevo-recos1.xlsx")
    df = pd.read_excel(excel_path)

    # Mostrar columnas reales del archivo
    print("📋 Columnas detectadas:", df.columns.tolist())
    print(df.head())

    # Verificar que tenga la columna esperada
    if "subestacion" not in df.columns:
        print("❌ No se encontró la columna 'subestacion' en el Excel.")
        return

    # Limpiar datos
    df["subestacion"] = df["subestacion"].astype(str).str.strip()

    subestaciones_bulk = []
    for _, row in df.iterrows():
        nombre = row["subestacion"]
        if not nombre or nombre.lower() == "nan":
            continue  # ignorar filas vacías

        sub = Subestacion(nombre=nombre, ubicacion="Sin ubicación")  # valor por defecto
        subestaciones_bulk.append(sub)

    # Evitar duplicados
    nombres_existentes = set(Subestacion.objects.values_list("nombre", flat=True))
    subestaciones_bulk = [s for s in subestaciones_bulk if s.nombre not in nombres_existentes]

    # Crear en bloque
    Subestacion.objects.bulk_create(subestaciones_bulk)
    print(f"✅ Se importaron {len(subestaciones_bulk)} subestaciones nuevas.")

if __name__ == "__main__":
    importar_subestaciones()
