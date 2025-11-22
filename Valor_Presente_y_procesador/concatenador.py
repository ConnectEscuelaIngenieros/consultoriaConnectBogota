import os
import pandas as pd

# Ruta base
ruta_base = r"Valor_Presente_y_procesador/output"
archivo_entrada = os.path.join(ruta_base, "salida_filtrada.csv")

# Leer archivo filtrado
df = pd.read_csv(archivo_entrada)

# Construir columna final usando jerarquía real
def construir_nombre(row):
    cap = str(row["Nombre_Capitulo"]).strip()
    item = str(row["Nombre_Item"]).strip()

    if item and item != "nan":     # si hay item → Capítulo » Item
        return f"{cap} » {item}"
    else:                          # si no hay item → solo Capítulo
        return cap

df["Nombre_Completo_Capitulo"] = df.apply(construir_nombre, axis=1)

# Seleccionar columnas finales
columnas_finales = [
    "Nombre_Completo_Capitulo",
    "Tipo_Fila",
    "Descripcion",
    "Presup_Capitulo_VP",
    "Proy_Capitulo_VP",
    "Nombre_Proyecto",
]

df_salida = df[columnas_finales]

# Guardar archivo final
archivo_salida = os.path.join(ruta_base, "salida_items_capitulos_min.csv")
df_salida.to_csv(archivo_salida, index=False)

print(f"Archivo generado: {archivo_salida}")
