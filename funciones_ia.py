import os
import csv
from datetime import datetime
from PIL import Image
import numpy as np
import joblib
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from sklearn.ensemble import RandomForestClassifier


# ===== CONFIGURACIÓN =====
DATA_ROOT = "data/train"
MODEL_DIR = "models"
REPORT_DIR = "reports"
DEVICES = ["mouse", "keyboard", "screen"]
SUPPORTED_EXT = (".jpg", ".jpeg", ".png", ".bmp")
MIN_IMAGES = 20

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

IMAGE_SIZE = (160, 160)
base_model = MobileNetV2(include_top=False, pooling="avg", input_shape=(160, 160, 3))


# ===== FUNCIONES DE PROCESAMIENTO =====

def load_and_preprocess(img_path):
    """Carga y prepara una imagen para MobileNetV2."""
    img = Image.open(img_path).convert('RGB').resize(IMAGE_SIZE)
    arr = np.array(img)
    arr = np.expand_dims(arr, axis=0)
    return preprocess_input(arr)


def extract_embedding(img_path):
    """Extrae el embedding (vector de características) de una imagen."""
    arr = load_and_preprocess(img_path)
    return base_model.predict(arr, verbose=0).reshape(-1)


def extract_dataset_embeddings(device):
    """Extrae embeddings y etiquetas (1=good, 0=damaged) para un dispositivo."""
    device_path = os.path.join(DATA_ROOT, device)
    good_folder = os.path.join(device_path, "good")
    damaged_folder = os.path.join(device_path, "damaged")

    X, y = [], []

    for label, folder in [(1, good_folder), (0, damaged_folder)]:
        if not os.path.isdir(folder):
            print(f"[ADVERTENCIA] No existe carpeta: {folder}")
            continue

        files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(SUPPORTED_EXT)]
        if len(files) < MIN_IMAGES:
            print(f"[ALERTA] Solo hay {len(files)} imágenes en {folder}, se recomienda >= {MIN_IMAGES}")

        for f in files:
            try:
                X.append(extract_embedding(f))
                y.append(label)
            except Exception as e:
                print(f"[WARNING] No se pudo procesar {f}: {e}")

    return np.array(X), np.array(y)

# ===== CLASIFICACIÓN =====

def load_model(device):
    """Carga un modelo entrenado."""
    path = os.path.join(MODEL_DIR, f"rf_{device}.joblib")
    if not os.path.exists(path):
        raise FileNotFoundError(f"No existe modelo para {device}. Entrénalo primero.")
    return joblib.load(path)


def classify_images(device, image_paths):
    """Clasifica una lista de imágenes con el modelo correspondiente."""
    model = load_model(device)
    results = []

    for f in image_paths:
        emb = extract_embedding(f).reshape(1, -1)
        prob_good = model.predict_proba(emb)[0][1]
        label = "bueno" if prob_good >= 0.5 else "dañado"

        results.append({
            "filename": os.path.basename(f),
            "device": device,
            "score_good": float(prob_good),
            "label": label,
            "timestamp": datetime.now().isoformat()
        })

        print(f"{os.path.basename(f)} → {label} ({prob_good:.2f})")

    return results


# ===== GUARDAR REPORTE =====

def save_report(results):
    """Guarda los resultados de clasificación en un archivo CSV."""
    if not results:
        print("[WARNING] No hay resultados para guardar.")
        return

    filename = f"reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    path = os.path.join(REPORT_DIR, filename)

    with open(path, "w", newline="", encoding="utf-8") as cf:
        writer = csv.DictWriter(cf, fieldnames=["filename", "device", "score_good", "label", "timestamp"])
        writer.writeheader()
        writer.writerows(results)

    print(f"📄 Reporte guardado en: {path}")


# ===== MAIN =====

# def Prueba_dir_carpetas():
#     # Ejemplo de uso:
#     print("=== MODO CONSOLA ===")
#     print("1. Entrenar modelos")
#     print("2. Clasificar imágenes")
#     choice = input("Elige una opción (1/2): ")

#     if choice == "1":
#         print('no disponible')
#     elif choice == "2":
#         device = input(f"Elige dispositivo {DEVICES}: ")
#         image_dir = input("Carpeta con imágenes a clasificar: ")
#         files = [os.path.join(image_dir, f) for f in os.listdir(image_dir) if f.lower().endswith(SUPPORTED_EXT)]
#         results = classify_images(device, files)
#         save_report(results)
#     else:
#         print("Opción no válida.")

def prueba():
    print("=== MODO CONSOLA ===")
    print("1. Entrenar modelos")
    print("2. Clasificar imágenes")
    choice = input("Elige una opción (1/2): ")

    if choice == "1":
        print('no disponible')
    elif choice == "2":

        device = input(f"Elige dispositivo {DEVICES}: ")
        image_path = input("Ingresa la ruta de la imagen a clasificar: ")

        files = [image_path] 
        results = classify_images(device, files)

        # Imprimir resultados en consola sin guardar CSV
        print("\n=== RESULTADOS ===")
        for r in results:
            print(f"{r['filename']:30} | {r['device']:10} | {r['label']:7} | Probabilidad bueno: {r['score_good']:.2f} | {r['timestamp']}")

        else:
            print("Opción no válida.")
        #C:\Users\DELL\Desktop\Teclados\Captura.PNG



def clasificar_dispositivos(file_pantalla, file_teclado, file_mouse):
    resultados = {}

    # ==== Pantalla ====
    device = 'screen'
    results = classify_images(device, [file_pantalla])
    if results:
        r = results[0]
        resultados['pantalla'] = {
            'filename': r['filename'],
            'device': r['device'],
            'label': r['label'],
            'score_good': r['score_good'],
            'timestamp': r['timestamp']
        }

    # ==== Teclado ====
    device = 'keyboard'
    results = classify_images(device, [file_teclado])
    if results:
        r = results[0]
        resultados['teclado'] = {
            'filename': r['filename'],
            'device': r['device'],
            'label': r['label'],
            'score_good': r['score_good'],
            'timestamp': r['timestamp']
        }

    # ==== Mouse ====
    device = 'mouse'
    results = classify_images(device, [file_mouse])
    if results:
        r = results[0]
        resultados['mouse'] = {
            'filename': r['filename'],
            'device': r['device'],
            'label': r['label'],
            'score_good': r['score_good'],
            'timestamp': r['timestamp']
        }

    return resultados

def map_estado(label):
    if label == "bueno":
        return "operativa"
    else:
        return "dañada"