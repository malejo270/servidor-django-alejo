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
from mantenimiento.models import Reconectador, Comunicacion

def importar_comunicaciones():
    # Ruta al Excel
    excel_path = os.path.join(BASE_DIR, "mantenimiento", "scripts", "nuevo-recos1.xlsx")
    df = pd.read_excel(excel_path, sheet_name="Comunicacion")

    # Limpiar nombres de columnas
    df.columns = df.columns.str.strip().str.lower()

    # Limpiar texto en columnas
    columnas_texto = [
        'modem', 'ip', 'ip vieja', 'asdu', 'estado',
        'tecnologia','observacion scada / apn','estado'
    ]
    for col in columnas_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace('nan', '')

    # --- 🔧 Corrección específica para ASDU ---
    if 'asdu' in df.columns:
        df['asdu'] = df['asdu'].apply(
            lambda x: str(int(float(x))) if x.replace('.', '', 1).isdigit() else str(x)
        )

    # Reemplazar ip vacía por "sin ip"
    df['ip'] = df['ip'].replace('', 'sin ip')
    df['ip vieja'] = df['ip vieja'].replace('', 'sin ip')

    # Convertir id_reco a entero seguro
    if 'id_reco' in df.columns:
        def convertir_id(val):
            if pd.isna(val) or val == '':
                return None
            try:
                return int(float(val))
            except ValueError:
                return None
        df['id_reco'] = df['id_reco'].apply(convertir_id)

    # Eliminar filas con id_reco vacío
    df = df[df['id_reco'].notna()]

    print("Columnas detectadas:", df.columns.tolist())
    print(df[['modem', 'ip', 'id_reco', 'asdu']].head())

    comunicaciones_bulk = []

    for _, row in df.iterrows():
        try:
            reco = Reconectador.objects.get(id_reco=row['id_reco'])
        except Reconectador.DoesNotExist:
            print(f"⚠ ID de reco '{row['id_reco']}' no encontrado en BD. Comunicación con modem '{row['modem']}' no importada.")
            continue

        comunicacion = Comunicacion(
            modem=row.get('modem', ''),
            ip=row.get('ip', 'sin ip'),
            ip_vieja=row.get('ip vieja', 'sin ip'),
            asdu=row.get('asdu', ''),
            estado=row.get('estado', ''),
            tecnologia=row.get('tecnologia', ''),
            estado_actividad=row.get('actividades', ''),
            id_reco=reco
        )
        comunicaciones_bulk.append(comunicacion)

    Comunicacion.objects.bulk_create(comunicaciones_bulk)
    print(f"✅ Se importaron {len(comunicaciones_bulk)} comunicaciones")

if __name__ == "__main__":
    importar_comunicaciones()
