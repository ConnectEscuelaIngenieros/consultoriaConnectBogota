import os
import pandas as pd

# Ruta del archivo original
ruta_base = r"Valor_Presente_y_procesador/output"
archivo_entrada = os.path.join(ruta_base, "salida.csv")

# Leer CSV
detalle = pd.read_csv(archivo_entrada)

# Filtrar solo CAPITULO y ITEM
detalle_filtrado = detalle[detalle["Tipo_Fila"].isin(["CAPITULO", "ITEM"])]

# Guardar filtrado
archivo_salida = os.path.join(ruta_base, "salida_filtrada_items.csv")
detalle_filtrado.to_csv(archivo_salida, index=False)

print(f"Archivo filtrado generado: {archivo_salida}")
