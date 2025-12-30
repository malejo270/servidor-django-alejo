import os
import sys
import django
from pathlib import Path
import pandas as pd

# ==============================
# 🔧 Configuración Django
# ==============================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emcali_app.settings')
django.setup()

from mantenimiento.models import Nodo, Subestacion


def importar_nodos():
    excel_path = os.path.join(
        BASE_DIR, "mantenimiento", "scripts", "nuevo-recos1.xlsx"
    )

    df = pd.read_excel(excel_path, sheet_name="Nodo")
    df.columns = df.columns.str.strip().str.lower()

    print(f"📊 Filas totales en Excel: {len(df)}")

    # ==============================
    # 🧼 LIMPIEZA REAL (ANTI-EXCEL)
    # ==============================

    def limpiar_entero(columna):
        return (
            columna
            .astype(str)
            .str.replace(r'\.0$', '', regex=True)
            .str.strip()
            .replace(['', 'nan', 'NaN', 'None'], None)
        )

    df['nodo'] = limpiar_entero(df['nodo'])
    df['id_subestacion'] = limpiar_entero(df['id_subestacion'])

    def to_int_safe(val):
        try:
            return int(val)
        except:
            return None

    df['nodo'] = df['nodo'].apply(to_int_safe)
    df['id_subestacion'] = df['id_subestacion'].apply(to_int_safe)

    # ==============================
    # 🔍 DETECTAR FILAS PROBLEMÁTICAS
    # ==============================
    errores = df[df['id_subestacion'].isna()]

    if not errores.empty:
        print("⚠️ FILAS CON id_subestacion INVÁLIDO:")
        for i in errores.index:
            print(f"   → Fila Excel {i + 2}")
        print("⚠️ Estas filas se importarán con subestación NULL\n")

    # ==============================
    # 🧽 LIMPIEZA DE TEXTO
    # ==============================
    for col in ['direccion', 'circuito 1', 'circuito 2', 'nt', 'clasificacion']:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .replace(['nan', 'NaN', 'None'], '')
            )

    # ==============================
    # 🚀 IMPORTACIÓN SEGURA
    # ==============================
    nodos_bulk = []

    for i, row in df.iterrows():

        subestacion = None
        if row['id_subestacion'] is not None:
            subestacion = Subestacion.objects.filter(
                id=row['id_subestacion']
            ).first()

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

    print(f"✅ Se importaron {len(nodos_bulk)} nodos correctamente")
    print("🎯 Importación finalizada sin errores")


if __name__ == "__main__":
    importar_nodos()
