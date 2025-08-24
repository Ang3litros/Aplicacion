import cv2
import numpy as np
from google.cloud import firestore, storage
import os

# --- Configuración (se debe ajustar en el entorno de Cloud Functions) ---
db = firestore.Client()
storage_client = storage.Client()

def analyze_blueprint(event, context):
    """
    Cloud Function que se activa con la subida de un archivo a Cloud Storage.
    Analiza un plano de construcción para identificar ejes y columnas.
    """
    bucket_name = event['bucket']
    file_name = event['name']

    print(f"Procesando archivo: {file_name} del bucket: {bucket_name}.")

    # --- 1. Descargar la imagen desde Cloud Storage ---
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    # Crear un path temporal para guardar la imagen
    temp_local_path = f"/tmp/{os.path.basename(file_name)}"
    blob.download_to_filename(temp_local_path)

    print(f"Imagen descargada en: {temp_local_path}")

    # --- 2. Procesamiento de la imagen con OpenCV ---
    img = cv2.imread(temp_local_path, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Suavizado para reducir ruido
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Detección de bordes
    edges = cv2.Canny(blurred, 50, 150)

    # --- 3. Detección de columnas (simplificado) ---
    # Esta es la parte más compleja y específica del dominio.
    # Este enfoque busca contornos que parezcan rectángulos sólidos (como columnas).
    # Se necesitaría un ajuste fino basado en planos reales.
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detected_columns = []
    for contour in contours:
        # Aproximar el contorno a un polígono
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.04 * peri, True)

        # Asumimos que las columnas son rectángulos (4 vértices)
        if len(approx) == 4:
            (x, y, w, h) = cv2.boundingRect(approx)
            aspect_ratio = w / float(h)

            # Filtrar por área y relación de aspecto para no detectar cualquier rectángulo
            # Estos valores son de ejemplo y deben ajustarse
            if w * h > 500 and 0.5 < aspect_ratio < 1.5:
                detected_columns.append({
                    "x": x, "y": y, "width": w, "height": h
                })

    print(f"Se detectaron {len(detected_columns)} posibles columnas.")

    # --- 4. Detección de ejes (simplificado) ---
    # Usamos la transformada de Hough para encontrar líneas rectas.
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10)

    horizontal_lines = []
    vertical_lines = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.arctan2(y2 - y1, x2 - x1) * 180. / np.pi
            if -10 < angle < 10: # Líneas horizontales
                horizontal_lines.append(y1)
            elif 80 < abs(angle) < 100: # Líneas verticales
                vertical_lines.append(x1)

    # Simplificar y ordenar ejes (eliminando duplicados cercanos)
    def simplify_axes(axes_list, tolerance=10):
        if not axes_list:
            return []
        axes_list.sort()
        simplified = [axes_list[0]]
        for x in axes_list:
            if x - simplified[-1] > tolerance:
                simplified.append(x)
        return simplified

    vertical_axes = simplify_axes(vertical_lines)
    horizontal_axes = simplify_axes(horizontal_lines)

    print(f"Ejes verticales detectados: {len(vertical_axes)}")
    print(f"Ejes horizontales detectados: {len(horizontal_axes)}")

    # --- 5. Asociar columnas a ejes y guardar en Firestore ---
    plan_id = os.path.splitext(os.path.basename(file_name))[0]
    plan_ref = db.collection('plans').document(plan_id)

    # Guardar la URL de la imagen y la info del plano
    plan_ref.set({
        'imageUrl': f"gs://{bucket_name}/{file_name}",
        'createdAt': firestore.SERVER_TIMESTAMP
    })

    # Asignar etiquetas a los ejes (A, B, C... y 1, 2, 3...)
    vertical_labels = [chr(65 + i) for i in range(len(vertical_axes))]
    horizontal_labels = [str(i + 1) for i in range(len(horizontal_axes))]

    for i, col in enumerate(detected_columns):
        # Encontrar el eje más cercano para esta columna
        col_center_x = col['x'] + col['width'] / 2
        col_center_y = col['y'] + col['height'] / 2

        # Encontrar el índice del eje vertical y horizontal más cercano
        v_axis_idx = np.argmin([abs(ax - col_center_x) for ax in vertical_axes])
        h_axis_idx = np.argmin([abs(ax - col_center_y) for ax in horizontal_axes])

        axis1 = vertical_labels[v_axis_idx]
        axis2 = horizontal_labels[h_axis_idx]

        element_id = f"{axis1}-{axis2}"
        element_ref = plan_ref.collection('elements').document(element_id)

        element_ref.set({
            'axis1': axis1,
            'axis2': axis2,
            'status': 'pending',
            'coordinates': {
                'x': col['x'], 'y': col['y'], 'width': col['width'], 'height': col['height']
            }
        })
        print(f"Guardado elemento {element_id} en Firestore.")

    # --- 6. Limpieza ---
    os.remove(temp_local_path)

    print("Análisis completado.")
