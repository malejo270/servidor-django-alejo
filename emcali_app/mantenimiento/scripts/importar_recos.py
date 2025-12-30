import os
import sys
import django
from pathlib import Path
import pandas as pd

# === Configuración Django ===
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emcali_app.settings')
django.setup()

# Importar modelos
from mantenimiento.models import Nodo, Reconectador

def importar_recos():
    # Ruta al Excel
    excel_path = os.path.join(BASE_DIR, "mantenimiento", "scripts", "nuevo-recos1.xlsx")
    df = pd.read_excel(excel_path, sheet_name="Reco")

    # Limpiar nombres de columnas
    df.columns = df.columns.str.strip().str.lower()

    # Limpiar texto en columnas
    for col in ['responsable', 'marca']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace('nan', '')

    # Convertir id_nodo a entero seguro
    if 'id_nodo' in df.columns:
        def convertir_id(val):
            if pd.isna(val) or val == '':
                return None
            try:
                return int(float(val))
            except ValueError:
                return None
        df['id_nodo'] = df['id_nodo'].apply(convertir_id)

    # Eliminar filas con id_nodo vacío
    df = df[df['id_nodo'].notna()]

    print("Columnas detectadas:", df.columns.tolist())
    print(df[['responsable', 'id_nodo']].head())

    recos_bulk = []

    for _, row in df.iterrows():
        try:
            nodo = Nodo.objects.get(id_nodo=row['id_nodo'])
        except Nodo.DoesNotExist:
            print(f"⚠ ID de nodo '{row['id_nodo']}' no encontrado en BD. Reco '{row['responsable']}' no importado.")
            continue

        reco = Reconectador(
            responsable=row.get('responsable', ''),
            marca=row.get('marca', ''),
            id_nodo=nodo
        )
        recos_bulk.append(reco)

    Reconectador.objects.bulk_create(recos_bulk)
    print(f"✅ Se importaron {len(recos_bulk)} recos")

if __name__ == "__main__":
    importar_recos()
