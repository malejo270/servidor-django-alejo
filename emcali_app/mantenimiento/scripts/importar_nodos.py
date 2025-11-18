import os
import sys
import django
from pathlib import Path
import pandas as pd
import math

# === Configuración Django ===
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emcali_app.settings')
django.setup()

# Importar modelos
from mantenimiento.models import Nodo, Subestacion

def importar_nodos():
    # Ruta al Excel
    excel_path = os.path.join(BASE_DIR, "mantenimiento", "scripts", "nuevobd_MAURO24.xlsx")
    df = pd.read_excel(excel_path, sheet_name="Nodo")

    # Limpiar nombres de columnas
    df.columns = df.columns.str.strip().str.lower()

    # Limpiar texto en columnas no numéricas
    for col in ['nodo', 'direccion', 'circuito 1', 'circuito 2', 'nt', 'clasificacion']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace('nan', '')

    # Convertir id_subestacion a entero seguro
    if 'id_subestacion' in df.columns:
        def convertir_id(val):
            if pd.isna(val) or val == '':
                return None
            try:
                return int(float(val))  # Convierte "1.0" o 1.0 en 1
            except ValueError:
                return None
        df['id_subestacion'] = df['id_subestacion'].apply(convertir_id)

    # Eliminar filas con id_subestacion vacío
    df = df[df['id_subestacion'].notna()]

    print("Columnas detectadas:", df.columns.tolist())

    nodos_bulk = []
    nodos_no_importados = []  # 👈 aquí guardamos los que fallan

    for _, row in df.iterrows():
        try:
            subestacion = Subestacion.objects.get(id=row['id_subestacion'])
        except Subestacion.DoesNotExist:
            print(f"⚠ ID de subestación '{row['id_subestacion']}' no encontrado. Nodo '{row['nodo']}' no importado.")
            nodos_no_importados.append(row['nodo'])
            continue

        nodo = Nodo(
            nodo=row['nodo'],
            direccion=row.get('direccion', ''),
            circuito1=row.get('circuito 1', ''),
            circuito2=row.get('circuito 2', ''),
            nt=row.get('nt', ''),
            clasificacion=row.get('clasificacion', ''),
            id_subestacion=subestacion
        )
        nodos_bulk.append(nodo)

    Nodo.objects.bulk_create(nodos_bulk)
    print(f"✅ Se importaron {len(nodos_bulk)} nodos")

    # 👀 Mostrar nodos que no entraron
    if nodos_no_importados:
        print("🚨 Nodos que no se importaron:")
        for nodo in nodos_no_importados:
            print("   -", nodo)
    else:
        print("✅ Todos los nodos se importaron correctamente.")

if __name__ == "__main__":
    importar_nodos()
