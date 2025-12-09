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
    excel_path = os.path.join(BASE_DIR, "mantenimiento", "scripts", "nuevobd_MAURO24.xlsx")
    df = pd.read_excel(excel_path, sheet_name="Reco")

    # Limpiar nombres de columnas
    df.columns = df.columns.str.strip().str.lower()

    # --- Asegurar columna NODO ---
    if "nodo" not in df.columns:
        print("❌ ERROR: La hoja 'Reco' debe tener una columna llamada 'Nodo'.")
        return

    # Convertir nodo a entero
    def convertir_nodo(val):
        if pd.isna(val) or val == "":
            return None
        try:
            return int(float(val))  # 5224080.0 → 5224080
        except:
            return None

    df["nodo"] = df["nodo"].apply(convertir_nodo)

    # Limpiar texto en columnas
    for col in ["responsable", "marca"]:
        if col in df.columns:
            df[col] = df[col].astype(str).strip().replace("nan", "")

    # Eliminar filas sin nodo válido
    df = df[df["nodo"].notna()]

    print("Columnas detectadas:", df.columns.tolist())
    print(df[["responsable", "nodo"]].head())

    recos_bulk = []
    recos_no_importados = []

    for _, row in df.iterrows():
        nodo_excel = row.get("nodo")
        responsable_excel = row.get("responsable", "")

        try:
            # Buscar nodo por su número real
            try:
                nodo = Nodo.objects.get(nodo=nodo_excel)
            except Nodo.DoesNotExist:
                print(f"⚠ NO existe el nodo '{nodo_excel}'. RECO '{responsable_excel}' NO importado.")
                recos_no_importados.append((nodo_excel, responsable_excel))
                continue

            # Crear objeto reconectador
            reco = Reconectador(
                responsable=responsable_excel,
                marca=row.get("marca", ""),
                id_nodo=nodo
            )
            recos_bulk.append(reco)

        except Exception as e:
            print(f"❌ Error inesperado con NODO '{nodo_excel}' y RECO '{responsable_excel}': {e}")
            recos_no_importados.append((nodo_excel, responsable_excel))
            continue

    # Guardado en bulk
    Reconectador.objects.bulk_create(recos_bulk)
    print(f"\n✅ Se importaron {len(recos_bulk)} recos correctamente")

    # Mostrar recos fallidos
    if recos_no_importados:
        print("\n🚨 RECOS que NO se importaron:")
        for nodo_fallido, responsable_fallido in recos_no_importados:
            print(f"   - Nodo: {nodo_fallido} | Responsable: {responsable_fallido}")
    else:
        print("✅ Todos los RECOs se importaron correctamente.")

if __name__ == "__main__":
    importar_recos()
