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

    # === Convertir NODO a entero REAL ===
    def convertir_nodo(val):
        if pd.isna(val) or val == '':
            return None
        try:
            return int(float(val))   # 5224080.0 → 5224080 SIEMPRE entero
        except:
            return None

    df['nodo'] = df['nodo'].apply(convertir_nodo)

    # Limpiar texto
    for col in ['direccion', 'circuito 1', 'circuito 2', 'nt', 'clasificacion']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace('nan', '')

    # === Convertir id_subestacion ===
    def convertir_id(val):
        if pd.isna(val) or val == '':
            return None
        try:
            return int(float(val))
        except:
            return None

    df['id_subestacion'] = df['id_subestacion'].apply(convertir_id)

    # Filtrar filas válidas
    df = df[df['nodo'].notna()]
    df = df[df['id_subestacion'].notna()]

    print("Columnas detectadas:", df.columns.tolist())

    nodos_bulk = []
    nodos_no_importados = []

    for _, row in df.iterrows():
        nodo_num = int(row['nodo'])   # 👈 Asegura entero SIN DECIMALES

        try:
            # Buscar subestación
            try:
                subestacion = Subestacion.objects.get(id=row['id_subestacion'])
            except Subestacion.DoesNotExist:
                print(f"⚠ Subestación '{row['id_subestacion']}' no encontrada. Nodo {nodo_num} NO importado.")
                nodos_no_importados.append(nodo_num)
                continue

            # Crear nodo
            nodo = Nodo(
                nodo=nodo_num,
                direccion=row.get('direccion', ''),
                circuito1=row.get('circuito 1', ''),
                circuito2=row.get('circuito 2', ''),
                nt=row.get('nt', ''),
                clasificacion=row.get('clasificacion', ''),
                id_subestacion=subestacion
            )
            nodos_bulk.append(nodo)

        except Exception as e:
            print(f"❌ Error inesperado al importar nodo {nodo_num}: {e}")
            nodos_no_importados.append(nodo_num)
            continue

    # Guardar en bulk
    Nodo.objects.bulk_create(nodos_bulk)
    print(f"✅ Se importaron {len(nodos_bulk)} nodos")

    # Mostrar nodos que fallaron
    if nodos_no_importados:
        print("\n🚨 Nodos que NO se importaron:")
        for nodo in nodos_no_importados:
            print("   -", nodo)
    else:
        print("✅ Todos los nodos se importaron correctamente.")

if __name__ == "__main__":
    importar_nodos()
