########### AUTOMATIZADOR VARIACIÓN PROMEDIO CON VALOR PRESENTE - PROYECTOS ARPRO #################

import os
import re
from datetime import date
import traceback
from typing import Dict, Any, List

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

import os
import re
import io
from contextlib import redirect_stdout
from collections import Counter
from typing import Dict, Any, List
from datetime import date

import pandas as pd

import warnings
warnings.simplefilter(action="ignore", category=FutureWarning)

###
import os

# =========================
# CONFIGURACIÓN DE RUTAS
# =========================

# Carpeta base del proyecto (donde está este archivo procesador_informes.py)
base_project_directory = os.path.dirname(os.path.abspath(__file__))

# Ruta completa al archivo de IPC históricos (IPC_HISTORICOS.xlsx)
ipc_historicos_file_path = os.path.join(
    base_project_directory,
    "IPC_HISTORICOS.xlsx"
)

# Ruta completa al archivo de fechas de proyecto (Proyecto_fechas.xlsx)
project_dates_file_path = os.path.join(
    base_project_directory,
    "Proyecto_fechas.xlsx"
)

# Carpeta donde están los presupuestos de entrada (input/)
input_budgets_directory = os.path.join(
    base_project_directory,
    "input/xlsx"
)

# Carpeta donde se guardarán los archivos de salida (output/)
output_reports_directory = os.path.join(
    base_project_directory,
    "output"
)



######## FUNCIÓN PARA LIMPIAR VALORES MONETARIOS ########
def limpiar_moneda(valor):
    """
    Elimina símbolos no numéricos y convierte a float.
    """
    if pd.isna(valor):
        return pd.NA
    texto = str(valor)
    texto_limpio = re.sub(r"[^0-9.\-]", "", texto)
    if texto_limpio in ("", ".", "-", "-."):
        return pd.NA
    try:
        return float(texto_limpio)
    except ValueError:
        return pd.NA


######## FUNCIÓN PARA CARGAR IPC HISTÓRICOS ########
def cargar_ipc_historicos() -> Dict[str, Any]:
    print("\n>>> Cargando IPC_HISTORICOS.xlsx...")
    ruta_ipc = ipc_historicos_file_path  # usa la ruta centralizada

    if not os.path.exists(ruta_ipc):
        raise FileNotFoundError("No se encontró el archivo IPC_HISTORICOS.xlsx en la ruta esperada")

    # Leemos 2 primeras columnas, saltando 3 filas como en R
    ipc_raw = pd.read_excel(ruta_ipc, skiprows=3, header=None, usecols=[0, 1])
    ipc_raw.columns = ["Fecha_raw", "IPC_raw"]

    # ---- LIMPIAR IPC ----
    ipc_raw["IPC"] = ipc_raw["IPC_raw"].apply(limpiar_moneda)

    # ---- DETECTAR Y LIMPIAR FECHA ----
    # Caso 1: ya es datetime
    if pd.api.types.is_datetime64_any_dtype(ipc_raw["Fecha_raw"]):
        ipc_raw["Fecha"] = pd.to_datetime(ipc_raw["Fecha_raw"], errors="coerce")
    else:
        # Intento 1: tratar como número (serial de Excel)
        fecha_num = pd.to_numeric(ipc_raw["Fecha_raw"], errors="coerce")
        if fecha_num.notna().any():
            ipc_raw["Fecha"] = pd.to_datetime(fecha_num, unit="d", origin="1899-12-30", errors="coerce")
        else:
            # Intento 2: tratar como texto de fecha
            ipc_raw["Fecha"] = pd.to_datetime(ipc_raw["Fecha_raw"], errors="coerce", dayfirst=True)

    # Filtrar filas válidas
    ipc_limpio = ipc_raw.dropna(subset=["Fecha", "IPC"]).copy()

    if len(ipc_limpio) == 0:
        print("[DEBUG] Primeras filas leídas de IPC_HISTORICOS.xlsx:")
        print(ipc_raw.head())
        raise ValueError(
            "Después de limpiar IPC_HISTORICOS.xlsx no quedó ningún registro válido.\n"
            "Revisa las columnas de fecha e IPC (formato, tipo de dato, filas vacías, etc.)."
        )

    # Añadir columnas de año/mes
    ipc_limpio["Año"] = ipc_limpio["Fecha"].dt.year
    ipc_limpio["Mes"] = ipc_limpio["Fecha"].dt.month
    ipc_limpio["Mes_Año"] = ipc_limpio["Fecha"].dt.strftime("%Y-%m")
    ipc_limpio = ipc_limpio[["Fecha", "Año", "Mes", "Mes_Año", "IPC"]].sort_values("Fecha").reset_index(drop=True)

    print(f"IPC históricos cargados: {len(ipc_limpio)} registros")
    fecha_min = ipc_limpio["Fecha"].min()
    fecha_max = ipc_limpio["Fecha"].max()
    print(f"Rango: {fecha_min.strftime('%d/%m/%Y')} a {fecha_max.strftime('%d/%m/%Y')}")

    fila_actual = ipc_limpio.iloc[-1]
    ipc_actual = float(fila_actual["IPC"])
    fecha_actual = fila_actual["Fecha"].date()
    print(f"IPC de referencia (más reciente): {ipc_actual} - Fecha: {fecha_actual.strftime('%d/%m/%Y')}")

    return {
        "tabla": ipc_limpio,
        "ipc_actual": ipc_actual,
        "fecha_actual": fecha_actual,
    }


######## FUNCIÓN PARA CALCULAR VALOR PRESENTE ########
def calcular_vp(serie_valores: pd.Series, ipc_historico: float, ipc_actual: float) -> pd.Series:
    if pd.isna(ipc_historico) or ipc_historico == 0:
        return pd.Series([pd.NA] * len(serie_valores), index=serie_valores.index)
    factor = ipc_actual / ipc_historico

    def convertir(valor):
        if pd.isna(valor):
            return pd.NA
        try:
            return float(valor) * factor
        except (TypeError, ValueError):
            return pd.NA

    return serie_valores.apply(convertir)


######## FUNCIÓN PARA EXTRAER CÓDIGO DEL PROYECTO ########
def extraer_codigo_proyecto(nombre_archivo: str) -> str:
    base = os.path.basename(nombre_archivo)
    coincidencia = re.match(r"^(\d+)", base)
    if not coincidencia:
        print(f"[ADVERTENCIA] No se pudo extraer código del archivo: {nombre_archivo}")
        return ""
    return coincidencia.group(1)


######## FUNCIÓN PARA EXTRAER NOMBRE DEL PROYECTO ########
def extraer_nombre_proyecto(ruta_archivo: str) -> str:
    nombre_archivo = os.path.basename(ruta_archivo)
    nombre_sin_ext = os.path.splitext(nombre_archivo)[0]

    primeras_filas = pd.read_excel(ruta_archivo, sheet_name=0, nrows=5, header=None)

    for _, fila in primeras_filas.iterrows():
        for valor in fila:
            if pd.isna(valor):
                continue
            texto = str(valor)
            if re.search(r"Proyecto\s*:", texto, flags=re.IGNORECASE):
                nombre = re.sub(r".*Proyecto\s*:?\s*", "", texto, flags=re.IGNORECASE).strip()
                if nombre:
                    return nombre

    return nombre_sin_ext



DEBUG_CLASIFICADOR_TIPO_FILA = False  # ponlo en True cuando quieras ver el detalle

def clasificar_tipo_fila(fila):
    descripcion = str(fila.get("Descripcion", "")).strip()
    tipo = str(fila.get("Tipo", "")).strip()
    codigo = str(fila.get("Codigo", "")).strip()
    desc_upper = descripcion.upper()

    #

    # 1) Totales explícitos
    if desc_upper.startswith("TOTAL"):
        resultado = "TOTAL"

    # 2) Items: 1.001-Texto, 2.3-Texto, 3.12-Texto, etc.
    elif re.match(r"^\d+(\.\d+)+\s*-\s*", descripcion):
        resultado = "ITEM"

    # 3) Capítulos:
    #    - 1-PRELIMINARES, 2-OTRO, etc.
    #    - o líneas en mayúsculas completas (COSTOS DIRECTOS)
    elif re.match(r"^\d+\s*-\s*", descripcion) or desc_upper == descripcion:
        resultado = "CAPITULO"

    # 4) Si no es nada de lo anterior y tiene Tipo, lo consideramos insumo
    elif tipo != "":
        resultado = "INSUMO"

    else:
        resultado = "INSUMO"

    if DEBUG_CLASIFICADOR_TIPO_FILA:
        print(
            f"[DEBUG] Desc='{descripcion}' | Tipo='{tipo}' | Codigo='{codigo}' "
            f"-> Tipo_Fila={resultado}"
        )

    return resultado

######## FUNCIÓN PRINCIPAL - PROCESAR PRESUPUESTO CON VP ########
def procesar_presupuesto(
    nombre_archivo_presupuesto: str,
    ipc_data: Dict[str, Any],
    datos_fechas: pd.DataFrame,
) -> Dict[str, Any]:
    print("\n" + "=" * 80)
    print(f"PROCESANDO: {nombre_archivo_presupuesto}")
    print("=" * 80)

    # --- Preparar rutas y extraer metadatos del proyecto ---
    ruta_presupuesto = os.path.join(input_budgets_directory, nombre_archivo_presupuesto)
    print(f"[DEBUG] Ruta presupuesto: {ruta_presupuesto}")

    print("[DEBUG] Extrayendo código y nombre de proyecto...")
    codigo_proyecto = extraer_codigo_proyecto(nombre_archivo_presupuesto)
    nombre_proyecto = extraer_nombre_proyecto(ruta_presupuesto)

    print(f"[DEBUG] Código proyecto: {codigo_proyecto}")
    print(f"[DEBUG] Nombre proyecto: {nombre_proyecto}")

    # --- Cargar archivo y normalizar columnas ---
    print("\n>>> Leyendo datos del presupuesto...")
    datos = pd.read_excel(ruta_presupuesto, sheet_name=0, skiprows=5)
    print(f"[DEBUG] Shape datos crudos: {datos.shape}")

    if datos.shape[1] == 25:
        print("[DEBUG] Estructura de 25 columnas detectada. Renombrando...")
        datos.columns = [
            "Descripcion", "Tipo", "Codigo", "UM",
            "Presup_Cantidad", "Presup_Valor",
            "Proy_Cantidad", "Proy_Valor",
            "Dif_Cantidad", "Dif_Valor",
            "Contratado_Cantidad", "Contratado_Valor",
            "Comprado_Cantidad", "Comprado_Valor",
            "Asegurado_Cantidad", "Asegurado_Valor",
            "Invertido_Cantidad", "Invertido_Valor",
            "Consumido_Cantidad", "Consumido_Valor",
            "PorConsumir_Cantidad", "PorConsumir_Valor",
            "Desviacion_Valor",
            "Norma1_ConsuMenorProy",
            "Norma2_AsegMenorProy",
        ]
    else:
        print(f"[DEBUG] Número de columnas inesperado: {datos.shape[1]}")
        raise ValueError("Estructura de columnas no reconocida para este tipo de archivo")

    print("[DEBUG] Asignando columnas auxiliares Presup/Proy *_Insumo/Item/Capitulo...")
    datos = datos.assign(
        Presup_Insumo=datos["Presup_Valor"],
        Presup_Item=pd.NA,
        Presup_Capitulo=pd.NA,
        Proy_Insumo=datos["Proy_Valor"],
        Proy_Item=pd.NA,
        Proy_Capitulo=pd.NA,
    )

    print("[DEBUG] Limpiando columnas monetarias...")
    for columna in [
        "Presup_Insumo", "Presup_Item", "Presup_Capitulo",
        "Proy_Insumo", "Proy_Item", "Proy_Capitulo",
    ]:
        datos[columna] = datos[columna].apply(limpiar_moneda)
    print("[DEBUG] Limpieza monetaria completada")

    # --- Extraer datos del proyecto y validar fechas ---
    print("\n>>> Buscando fecha de elaboración en Proyecto_fechas...")
    if "Codigo Proyecto" not in datos_fechas.columns:
        raise KeyError("La tabla Proyecto_fechas no tiene la columna 'Codigo Proyecto'")

    codigo_str = str(codigo_proyecto).strip()
    print(f"[DEBUG] Buscando código en Proyecto_fechas: '{codigo_str}'")
    proyecto_info = datos_fechas[
        datos_fechas["Codigo Proyecto"].astype(str).str.strip() == codigo_str
    ]

    if proyecto_info.empty:
        print(f"⚠️ ADVERTENCIA: Código {codigo_proyecto} no encontrado en Proyecto_fechas")
        print("   No se aplicará conversión a Valor Presente")
        fecha_elaboracion = pd.NA
        fecha_inicio = pd.NA
        fecha_finalizacion = pd.NA
        estado = pd.NA
        macroproyecto = "No pertenece a ningún macroproyecto"
        ipc_historico = pd.NA
        factor_ipc = pd.NA
        aplicar_vp = False
    else:
        print("✅ Proyecto encontrado en Proyecto_fechas")
        fila_proyecto = proyecto_info.iloc[0]

        fecha_elaboracion = fila_proyecto.get("Fecha De Elaboracion", pd.NA)
        fecha_inicio = fila_proyecto.get("Fecha De Inicio", pd.NA)
        fecha_finalizacion = fila_proyecto.get("Fecha De Finalizacion", pd.NA)
        estado = fila_proyecto.get("Estado", pd.NA)

        print(f"[DEBUG] Fecha elaboración (raw): {fecha_elaboracion}")
        print(f"[DEBUG] Fecha inicio (raw): {fecha_inicio}")
        print(f"[DEBUG] Fecha finalización (raw): {fecha_finalizacion}")
        print(f"[DEBUG] Estado: {estado}")

        if "MacroProyecto" in proyecto_info.columns:
            valor_macro = fila_proyecto.get("MacroProyecto", "")
            if pd.isna(valor_macro) or str(valor_macro).strip() == "":
                macroproyecto = "No pertenece a ningún macroproyecto"
            else:
                macroproyecto = str(valor_macro)
        else:
            macroproyecto = "No pertenece a ningún macroproyecto"
        print(f"[DEBUG] Macroproyecto: {macroproyecto}")

        # --- Calcular o descartar Valor Presente ---
        if pd.isna(fecha_elaboracion):
            print("⚠️ Fecha de elaboración vacía, no se puede calcular IPC histórico")
            ipc_historico = pd.NA
            factor_ipc = pd.NA
            aplicar_vp = False
        else:
            if isinstance(fecha_elaboracion, pd.Timestamp):
                fecha_elab_date = fecha_elaboracion.date()
            else:
                fecha_elab_date = pd.to_datetime(fecha_elaboracion).date()

            print(f"Fecha de elaboración: {fecha_elab_date.strftime('%d/%m/%Y')}")
            mes_año_elab = fecha_elab_date.strftime("%Y-%m")
            print(f"[DEBUG] Mes-Año elaboración para IPC: {mes_año_elab}")

            ipc_tabla = ipc_data["tabla"]
            fila_ipc = ipc_tabla[ipc_tabla["Mes_Año"] == mes_año_elab]
            print(f"[DEBUG] Filas IPC encontradas: {len(fila_ipc)}")

            if fila_ipc.empty:
                print(f"⚠️ No se encontró IPC para {mes_año_elab}")
                ipc_historico = pd.NA
                factor_ipc = pd.NA
                aplicar_vp = False
            else:
                ipc_historico = float(fila_ipc.iloc[0]["IPC"])
                print(f"IPC histórico encontrado: {ipc_historico}")
                factor_ipc = float(ipc_data["ipc_actual"]) / ipc_historico
                print(f"Factor de conversión: {factor_ipc:.6f}")
                aplicar_vp = True

    # --- Aplicar conversión a VP según disponibilidad ---
    if aplicar_vp:
        print("\n>>> Convirtiendo valores a Valor Presente...")
        datos = datos.assign(
            Estado="" if pd.isna(estado) else str(estado),
            Macroproyecto=macroproyecto,
            IPC_Historico=ipc_historico,
            Factor_IPC=factor_ipc,
            Presup_Insumo_VP=calcular_vp(datos["Presup_Insumo"], ipc_historico, ipc_data["ipc_actual"]),
            Presup_Item_VP=calcular_vp(datos["Presup_Item"], ipc_historico, ipc_data["ipc_actual"]),
            Presup_Capitulo_VP=calcular_vp(datos["Presup_Capitulo"], ipc_historico, ipc_data["ipc_actual"]),
            Proy_Insumo_VP=calcular_vp(datos["Proy_Insumo"], ipc_historico, ipc_data["ipc_actual"]),
            Proy_Item_VP=calcular_vp(datos["Proy_Item"], ipc_historico, ipc_data["ipc_actual"]),
            Proy_Capitulo_VP=calcular_vp(datos["Proy_Capitulo"], ipc_historico, ipc_data["ipc_actual"]),
        )
        print("✅ Conversión a VP completada")
    else:
        print("\n⚠️ No se aplicó conversión a VP (usando valores originales)")
        datos = datos.assign(
            Presup_Insumo_VP=datos["Presup_Insumo"],
            Presup_Item_VP=datos["Presup_Item"],
            Presup_Capitulo_VP=datos["Presup_Capitulo"],
            Proy_Insumo_VP=datos["Proy_Insumo"],
            Proy_Item_VP=datos["Proy_Item"],
            Proy_Capitulo_VP=datos["Proy_Capitulo"],
        )

    # --- Identificar capítulos e ítems ---
    print("\n>>> Identificando capítulos e items...")

    
    datos["Tipo_Fila"] = datos.apply(clasificar_tipo_fila, axis=1)
    print("[DEBUG] Conteo por Tipo_Fila:")
    print(datos["Tipo_Fila"].value_counts(dropna=False))

    filas_capitulo = datos[datos["Tipo_Fila"] == "CAPITULO"]
    filas_item = datos[datos["Tipo_Fila"] == "ITEM"]

    print(f"Capítulos: {len(filas_capitulo)}")
    print(f"Items: {len(filas_item)}")

    ##Separando código y nombre de la columna Descripcion
    print("[DEBUG] Separando código y nombre de la columna Descripcion...")

    datos[["Codigo_Estructura", "Nombre_Estructura"]] = datos["Descripcion"].apply(
        lambda valor: pd.Series(separar_codigo_y_nombre(valor))
    )

    print("[DEBUG] Ejemplo separación:")
    print(datos[["Descripcion", "Codigo_Estructura", "Nombre_Estructura"]].head(10))

    # ---------------------------------------------------
    # ... Código de jerarquía y metadatos ...
    # ---------------------------------------------------

    print("[DEBUG] Construyendo jerarquía Capítulo / Item...")

    # 1) Capítulos: marcar en las filas CAPITULO y luego propagar hacia abajo
    datos["Codigo_Capitulo"] = datos.apply(
        lambda fila: fila["Codigo_Estructura"] if fila["Tipo_Fila"] == "CAPITULO" else pd.NA,
        axis=1,
    )
    datos["Nombre_Capitulo"] = datos.apply(
        lambda fila: fila["Nombre_Estructura"] if fila["Tipo_Fila"] == "CAPITULO" else pd.NA,
        axis=1,
    )

    datos["Codigo_Capitulo"] = datos["Codigo_Capitulo"].ffill()
    datos["Nombre_Capitulo"] = datos["Nombre_Capitulo"].ffill()

    # 2) Items: marcar en las filas ITEM y propagar hacia abajo
    datos["Codigo_Item"] = datos.apply(
        lambda fila: fila["Codigo_Estructura"] if fila["Tipo_Fila"] == "ITEM" else pd.NA,
        axis=1,
    )
    datos["Nombre_Item"] = datos.apply(
        lambda fila: fila["Nombre_Estructura"] if fila["Tipo_Fila"] == "ITEM" else pd.NA,
        axis=1,
    )

    datos["Codigo_Item"] = datos["Codigo_Item"].ffill()
    datos["Nombre_Item"] = datos["Nombre_Item"].ffill()

    print("[DEBUG] Jerarquía construida (Capítulo / Item asignados a cada fila)")

    print("[DEBUG] Asignando metadatos de proyecto a cada fila...")

    datos = datos.assign(
        Nombre_Proyecto=nombre_proyecto,
        Codigo_Proyecto=codigo_proyecto,
        Macroproyecto=macroproyecto,
        Estado_Proyecto="" if pd.isna(estado) else str(estado),
        Fecha_De_Elaboracion=fecha_elaboracion,
        Fecha_De_Inicio=fecha_inicio,
        Fecha_De_Finalizacion=fecha_finalizacion,
    )

    print("[DEBUG] Metadatos de proyecto replicados en todas las filas")


    # --- Calcular totales en VP ---
    print("\n>>> Calculando totales en Valor Presente...")
    total_presupuestado_vp = float(filas_capitulo["Presup_Capitulo_VP"].fillna(0).sum())
    total_proyectado_vp = float(filas_capitulo["Proy_Capitulo_VP"].fillna(0).sum())

    print(f"[DEBUG] Total Presupuestado VP (capítulos): {total_presupuestado_vp}")
    print(f"[DEBUG] Total Proyectado VP (capítulos): {total_proyectado_vp}")

    print(f"Total Presupuestado VP: {total_presupuestado_vp:,.2f}")
    print(f"Total Proyectado VP:   {total_proyectado_vp:,.2f}")

    # --- Construir DataFrame resumen ---

    def fecha_a_texto(valor):
        if isinstance(valor, pd.Timestamp):
            return valor.date().isoformat()
        if isinstance(valor, date):
            return valor.isoformat()
        if pd.isna(valor):
            return ""
        return str(valor)

    print("[DEBUG] Construyendo DataFrame resumen...")
    resumen = pd.DataFrame(
        [{
            "Nombre_Proyecto": nombre_proyecto,
            "Codigo_Proyecto": codigo_proyecto,
            "Total_Proyecto_Presupuestado_VP": round(total_presupuestado_vp, 2),
            "Total_Proyecto_Proyectado_VP": round(total_proyectado_vp, 2),
            "Fecha_De_Elaboracion": fecha_a_texto(fecha_elaboracion),
            "Fecha_De_Inicio": fecha_a_texto(fecha_inicio),
            "Fecha_De_Finalizacion": fecha_a_texto(fecha_finalizacion),
            "Estado": "" if pd.isna(estado) else str(estado),
            "Macroproyecto": macroproyecto,
            "IPC_Historico": float(ipc_historico) if not pd.isna(ipc_historico) else pd.NA,
            "Factor_IPC": float(factor_ipc) if not pd.isna(factor_ipc) else pd.NA,
        }]
    )
    
    
    
    
    print("\n✅ Proyecto procesado exitosamente")
    return {
        "resumen": resumen,
        "detalle": datos,
    }


######## FUNCIÓN PARA GUARDAR EXCEL CONSOLIDADO ########
def guardar_excel_consolidado(consolidado: pd.DataFrame, ruta_salida: str) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Consolidado VP"

    # Escribir encabezados y datos
    for fila_idx, fila in enumerate(consolidado.itertuples(index=False), start=2):
        if fila_idx == 2:
            # encabezados
            for col_idx, nombre_columna in enumerate(consolidado.columns, start=1):
                ws.cell(row=1, column=col_idx, value=nombre_columna)
        for col_idx, valor in enumerate(fila, start=1):
            ws.cell(row=fila_idx, column=col_idx, value=valor)

    # Estilos de encabezado
    encabezado_font = Font(bold=True, color="FFFFFF", size=11)
    encabezado_fill = PatternFill("solid", fgColor="2E75B6")
    borde_fino = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    for celda in ws[1]:
        celda.font = encabezado_font
        celda.fill = encabezado_fill
        celda.alignment = Alignment(horizontal="center", wrap_text=True)
        celda.border = borde_fino

    # Formato numérico columnas 3–6 y 12–13
    for fila in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=3, max_col=6):
        for celda in fila:
            celda.number_format = "#,##0.00"
            celda.alignment = Alignment(horizontal="right")

    for fila in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=12, max_col=13):
        for celda in fila:
            celda.number_format = "#,##0.00"
            celda.alignment = Alignment(horizontal="right")

    # Formato fechas columnas 7–9
    for fila in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=7, max_col=9):
        for celda in fila:
            celda.number_format = "DD/MM/YYYY"
            celda.alignment = Alignment(horizontal="center")

    # Ancho de columnas
    anchos = [30, 12, 22, 22, 25, 25, 18, 18, 18, 15, 30, 15, 15]
    for indice, ancho in enumerate(anchos, start=1):
        columna = get_column_letter(indice)
        ws.column_dimensions[columna].width = ancho

    # Congelar primera fila
    ws.freeze_panes = "A2"

    wb.save(ruta_salida)


######## FUNCIÓN PARA PROCESAR MÚLTIPLES PROYECTOS ########
from typing import Dict, Any, List

import traceback
from collections import Counter
from typing import Dict, Any, List



import os
import re
import io
from contextlib import redirect_stdout
from collections import Counter
from typing import Dict, Any, List
from datetime import date

import pandas as pd


def procesar_todos_presupuestos(modo_mensajes: str = "debug") -> Dict[str, Any]:
    """
    modo_mensajes:
        - "debug"     -> imprime detalles y cada error individual
        - "resumen"   -> imprime solo estadísticas de errores al final
        - "capitulos" -> no muestra el proceso interno; solo cuántos capítulos/items detecta por presupuesto
    """
    print("\n" + "=" * 80)
    print("AUTOMATIZADOR VARIACIÓN PROMEDIO CON VALOR PRESENTE")
    print("=" * 80)

    imprimir_debug_detallado = (modo_mensajes == "debug")
    acumular_errores_para_resumen = (modo_mensajes == "resumen")
    mostrar_solo_capitulos = (modo_mensajes == "capitulos")

    errores_en_archivos: List[Dict[str, Any]] = []

    ipc_data = cargar_ipc_historicos()

    print("\n>>> Cargando Proyecto_fechas.xlsx...")
    datos_fechas = pd.read_excel(project_dates_file_path, sheet_name=0)
    print(f"Proyecto_fechas cargado: {len(datos_fechas)} proyectos")

    print("\n>>> Buscando archivos de presupuesto en carpeta input...")

    archivos = [
        nombre for nombre in os.listdir(input_budgets_directory)
        if re.match(r"^\d+.*\.(xlsx|xls)$", nombre, flags=re.IGNORECASE)
    ]

    if not archivos:
        print("❌ No se encontraron archivos de presupuesto")
        return {}

    if imprimir_debug_detallado:
        print(f"[DEBUG] Archivos encontrados: {len(archivos)}")
        for indice, nombre in enumerate(archivos, start=1):
            print(f"  {indice}. {nombre}")
    else:
        print(f"Archivos de presupuesto encontrados: {len(archivos)}")

    lista_consolidados: List[pd.DataFrame] = []
    exitosos = 0
    fallidos = 0

    for nombre_archivo in archivos:
        try:
            if imprimir_debug_detallado:
                print(f"\n[DEBUG] Procesando archivo: {nombre_archivo}")

            # En modo "capitulos" silenciamo el output de procesar_presupuesto
            if mostrar_solo_capitulos:
                buffer_salida = io.StringIO()
                with redirect_stdout(buffer_salida):
                    resultado = procesar_presupuesto(nombre_archivo, ipc_data, datos_fechas)
            else:
                resultado = procesar_presupuesto(nombre_archivo, ipc_data, datos_fechas)

            # Usamos el DataFrame completo de detalle para el consolidado
            lista_consolidados.append(resultado["detalle"])
            exitosos += 1

            if mostrar_solo_capitulos:
                conteos = resultado["detalle"]["Tipo_Fila"].value_counts()
                numero_capitulos = int(conteos.get("CAPITULO", 0))
                numero_items     = int(conteos.get("ITEM", 0))
                numero_insumos   = int(conteos.get("INSUMO", 0))
                numero_totales   = int(conteos.get("TOTAL", 0))

                print(
                    f"Presupuesto '{nombre_archivo}': "
                    f"CAP={numero_capitulos}, ITEM={numero_items}, "
                    f"INSUMO={numero_insumos}, TOTAL={numero_totales}"
                )


        except Exception as error:
            fallidos += 1

            if acumular_errores_para_resumen:
                errores_en_archivos.append(
                    {
                        "nombre_archivo": nombre_archivo,
                        "tipo_error": type(error),
                        "mensaje_error": str(error),
                    }
                )
            else:
                print(f"\n❌ ERROR: {nombre_archivo} - {error}")

    print("\n" + "=" * 80)
    print("RESUMEN DE PROCESAMIENTO")
    print("=" * 80)
    print(f"Archivos encontrados:      {len(archivos)}")
    print(f"Procesados exitosamente:   {exitosos}")
    print(f"Fallidos:                  {fallidos}")
    print("=" * 80)

    # Modo resumen → estadísticas de errores
    if acumular_errores_para_resumen and errores_en_archivos:
        from collections import Counter

        print("\n📊 ESTADÍSTICAS DE ERRORES (MODO RESUMEN)")
        contador_tipos = Counter(error["tipo_error"] for error in errores_en_archivos)
        for tipo_error, cantidad in contador_tipos.items():
            print(f"  - {tipo_error.__name__}: {cantidad} archivo(s)")

        print("\nEjemplos de errores por tipo:")
        ejemplos_por_tipo: Dict[type, Dict[str, Any]] = {}
        for error in errores_en_archivos:
            tipo_error = error["tipo_error"]
            if tipo_error not in ejemplos_por_tipo:
                ejemplos_por_tipo[tipo_error] = error

        for tipo_error, ejemplo in ejemplos_por_tipo.items():
            print(f"\n  {tipo_error.__name__}:")
            print(f"    Archivo: {ejemplo['nombre_archivo']}")
            print(f"    Mensaje: {ejemplo['mensaje_error']}")

    if not lista_consolidados:
        print("\n⚠️ No se procesaron archivos exitosamente")
        return {}

    print("\n>>> Generando DataFrame consolidado...")

    consolidado = pd.concat(lista_consolidados, ignore_index=True)

    print("\n>>> Enriqueciendo consolidado con candidatos_grupo.csv...")

    ruta_candidatos = os.path.join(output_reports_directory, "candidatos_grupo.csv")

    if os.path.exists(ruta_candidatos):
        candidatos = pd.read_csv(ruta_candidatos)

        # Normalizar textos
        candidatos["codigo_candidato"] = candidatos["codigo_candidato"].astype(str).str.strip()
        candidatos["descripcion_candidato"] = candidatos["descripcion_candidato"].astype(str).str.strip()

        # Columna concatenada
        candidatos["capitulo_homologado"] = (
            candidatos["codigo_candidato"] + " - " + candidatos["descripcion_candidato"]
        )

        # Nos quedamos con código + nombre concatenado (sin duplicados)
        candidatos_unicos = candidatos[["codigo_candidato", "capitulo_homologado"]].drop_duplicates()

        # Normalizar clave en consolidado
        consolidado["Codigo_Estructura"] = consolidado["Codigo_Estructura"].astype(str).str.strip()

        # Merge
        consolidado = consolidado.merge(
            candidatos_unicos,
            how="left",
            left_on="Codigo_Estructura",
            right_on="codigo_candidato",
        )

        # Ya no necesitamos la columna de merge de candidatos
        consolidado.drop(columns=["codigo_candidato"], inplace=True)

        print("[DEBUG] Columna 'capitulo_homologado' añadida desde candidatos_grupo.csv")
    else:
        print(f"[DEBUG] No se encontró archivo de candidatos: {ruta_candidatos}. Se omite merge.")


    if not os.path.exists(output_reports_directory):
        os.makedirs(output_reports_directory, exist_ok=True)

    fecha_actual = date.today().strftime("%Y%m%d")
    nombre_consolidado = f"CONSOLIDADO_VARIACION_PROMEDIO_VP_{fecha_actual}.xlsx"
    ruta_consolidado = os.path.join(output_reports_directory, nombre_consolidado)

    # guardar_excel_consolidado(consolidado, ruta_consolidado)

    print("\n✅ Excel consolidado generado")
    print(f"Archivo: {ruta_consolidado}")
    print(f"Filas en el DataFrame consolidado (detalle completo): {len(consolidado)}")
    print(
        f"\n📊 NOTA: Todos los valores están en VALOR PRESENTE "
        f"(pesos de {ipc_data['fecha_actual'].strftime('%B %Y')})"
    )
    print("=" * 80)

    return {
        "consolidado": consolidado,
        "archivo": ruta_consolidado,
    }


import tkinter as tk
from tkinter import ttk

def mostrar_dataframe_en_ventana(data_frame, window_title="Vista de datos"):
    print("[DEBUG] Abriendo ventana de visualización de DataFrame...")

    main_window = tk.Tk()
    main_window.title(window_title)

    main_window.geometry("1200x600")  # ancho x alto (puedes cambiarlo)

    frame = ttk.Frame(main_window)
    frame.pack(fill="both", expand=True)

    column_names = list(data_frame.columns)

    tree_view = ttk.Treeview(
        frame,
        columns=column_names,
        show="headings"
    )

    # Encabezados
    for column_name in column_names:
        tree_view.heading(column_name, text=column_name)
        tree_view.column(column_name, width=150, anchor="w")

    # Filas
    for _, row in data_frame.iterrows():
        tree_view.insert("", "end", values=list(row))

    # Barras de desplazamiento
    vertical_scrollbar = ttk.Scrollbar(
        frame,
        orient="vertical",
        command=tree_view.yview
    )
    horizontal_scrollbar = ttk.Scrollbar(
        frame,
        orient="horizontal",
        command=tree_view.xview
    )

    tree_view.configure(
        yscrollcommand=vertical_scrollbar.set,
        xscrollcommand=horizontal_scrollbar.set
    )

    vertical_scrollbar.pack(side="right", fill="y")
    horizontal_scrollbar.pack(side="bottom", fill="x")
    tree_view.pack(side="left", fill="both", expand=True)

    main_window.mainloop()


def separar_codigo_y_nombre(descripcion: str) -> tuple[str, str]:
    """
    Recibe la celda de 'Descripcion' y devuelve (codigo, nombre_sin_codigo).

    Casos:
    - '1.001-Localización y replanteo'  -> ('1.001', 'Localización y replanteo')
    - '1-PRELIMINARES'                  -> ('1', 'PRELIMINARES')
    - 'COSTOS DIRECTOS'                 -> ('', 'COSTOS DIRECTOS')
    - 'comisión de topografía'         -> ('', 'comisión de topografía')
    """
    if descripcion is None:
        return "", ""

    texto = str(descripcion).strip()

    # ITEM: 1.001-Texto / 2.3-Texto / 10.12-Texto
    patron_item = re.match(r"^\s*(\d+(?:\.\d+)+)\s*-\s*(.+)\s*$", texto)
    if patron_item:
        codigo = patron_item.group(1).strip()
        nombre = patron_item.group(2).strip()
        return codigo, nombre

    # CAPITULO numérico simple: 1-PRELIMINARES, 2-OTRO
    patron_capitulo = re.match(r"^\s*(\d+)\s*-\s*(.+)\s*$", texto)
    if patron_capitulo:
        codigo = patron_capitulo.group(1).strip()
        nombre = patron_capitulo.group(2).strip()
        return codigo, nombre

    # RESTO: no tiene código delante
    return "", texto

######## MENÚ PRINCIPAL ########
def menu_principal():
    print("\n" + "=" * 80)
    print("   AUTOMATIZADOR VARIACIÓN PROMEDIO CON VALOR PRESENTE")
    print("   PROYECTOS ARPRO - IPC BANCO DE LA REPÚBLICA")
    print("=" * 80)
    print("\n1. Procesar un presupuesto específico")
    print("2. Procesar todos los presupuestos (recomendado)")
    print("9. Salir")
    opcion = input("\nSeleccione una opción (1-9): ").strip()

    if opcion == "1":
        try:
            resultado = procesar_presupuesto("184 - Seguimiento Insumos.xlsx", cargar_ipc_historicos(), pd.read_excel(project_dates_file_path))
            if resultado:
                resultado = procesar_presupuesto(
                    "184 - Seguimiento Insumos.xlsx",
                    ipc_data=cargar_ipc_historicos(),
                    datos_fechas=pd.read_excel(project_dates_file_path),
                )

                if not os.path.exists(output_reports_directory):
                    os.makedirs(output_reports_directory, exist_ok=True)

                resultado["resumen"].to_csv(
                    os.path.join(output_reports_directory, "resumen.csv"),
                    index=False,
                    encoding="utf-8-sig",
                )
                resultado["detalle"].to_csv(
                    os.path.join(output_reports_directory, "detalle.csv"),
                    index=False,
                    encoding="utf-8-sig",
                )
                print("\n✅ PROCESO COMPLETADO EXITOSAMENTE")
                            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
    
    elif opcion == "2":
        
        resultado = procesar_todos_presupuestos(modo_mensajes="capitulos")


        if "consolidado" in resultado:
            df = resultado["consolidado"]
            df.to_csv(os.path.join(output_reports_directory, "salida_capitulos_homologados.csv"), index=False)

            mostrar_dataframe_en_ventana(df, "Consolidado Valor Presente")
            

        else:
            print("⚠️ No hay DataFrame consolidado para mostrar.")

    elif opcion == "9":
        print("\nHasta luego!")
    else:
        print("\nOpción inválida")


if __name__ == "__main__":
    menu_principal()
