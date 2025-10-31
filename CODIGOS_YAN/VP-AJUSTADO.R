########### AUTOMATIZADOR VALOR PRESENTE - TABLA LOOKER FINAL #################
library(readr)
library(readxl)
library(dplyr)
library(openxlsx)
library(lubridate)

######## FUNCION PARA LIMPIAR IPC HISTORICOS (AUTOMATICA) ########
cargar_ipc_historicos <- function() {
  cat("\n>>> Cargando y limpiando IPC_HISTORICOS.xlsx...\n")
  
###### Leer saltando encabezados
  IPC_RAW <- read_excel("IPC_HISTORICOS.xlsx", skip = 3, col_names = FALSE)
  names(IPC_RAW) <- c("Fecha_Serial", "IPC")
  
########## Limpiar y convertir
  IPC_LIMPIO <- IPC_RAW %>%
    filter(!is.na(Fecha_Serial), !is.na(IPC)) %>%
    mutate(
      Fecha_Serial = as.numeric(Fecha_Serial),
      IPC = as.numeric(IPC)
    ) %>%
    filter(!is.na(Fecha_Serial), !is.na(IPC)) %>%
    mutate(
      Fecha = as.Date(Fecha_Serial, origin = "1899-12-30"),
      Año = year(Fecha),
      Mes = month(Fecha),
      Mes_Año = format(Fecha, "%Y-%m")
    ) %>%
    select(Fecha, Año, Mes, Mes_Año, IPC)
  
  cat("IPC historicos cargados:", nrow(IPC_LIMPIO), "registros\n")
  cat("  Rango:", as.character(min(IPC_LIMPIO$Fecha)), "a", 
      as.character(max(IPC_LIMPIO$Fecha)), "\n")
  
  return(IPC_LIMPIO)
}

######## FUNCION PRINCIPAL - PROCESAR TABLA LOOKER ########
procesar_tabla_looker <- function(nombre_archivo = "tabla_looker_final.csv") {
  
  cat("\n", rep("=", 70), "\n", sep = "")
  cat("INICIANDO PROCESAMIENTO: Tabla Looker Final\n")
  cat(rep("=", 70), "\n", sep = "")
  
############ 1. CONFIGURAR RUTAS
  ruta_completa <- file.path("input", nombre_archivo)
  nombre_base <- tools::file_path_sans_ext(nombre_archivo)
  archivo_salida <- file.path("output", paste0(nombre_base, "_IPC_BANREP_FINAL.xlsx"))
  
####### Crear carpeta output si no existe
  if (!dir.exists("output")) {
    dir.create("output")
  }
  
  # Verificar archivo
  if (!file.exists(ruta_completa)) {
    stop("No se encontro el archivo: ", ruta_completa)
  }
  
  cat("\nArchivo de entrada:", ruta_completa, "\n")
  cat("Archivo de salida:", archivo_salida, "\n")
  
############ 2. CARGAR IPC HISTORICOS
  IPC_HISTORICOS <- cargar_ipc_historicos()
  
  # IPC actual (Septiembre 2025)
  ipc_sep_2025 <- 151.48
  fecha_actual <- as.Date("2025-09-30")
  
  cat("\nIPC DE REFERENCIA (Septiembre 2025):", ipc_sep_2025, "\n")
  
########## 3. LEER TABLA LOOKER
  cat("\n>>> Leyendo tabla_looker_final.csv...\n")
  datos_completos <- read_csv(ruta_completa, show_col_types = FALSE)
  
  cat("Registros leidos:", nrow(datos_completos), "\n")
  cat("Proyectos unicos:", length(unique(datos_completos$SkIdProyecto)), "\n")
  
########### 4. CONVERTIR FECHAS Y HACER MATCHING CON IPC
  cat("\n>>> Procesando fechas y obteniendo IPCs historicos...\n")
  
  datos_completos <- datos_completos %>%
    mutate(
      Fecha_Elaboracion_Date = dmy(`Fecha De Elaboracion`),
      Año_Elab = year(Fecha_Elaboracion_Date),
      Mes_Elab = month(Fecha_Elaboracion_Date),
      Mes_Año_Elab = format(Fecha_Elaboracion_Date, "%Y-%m")
    )
  
  # Hacer JOIN con IPC históricos
  datos_completos <- datos_completos %>%
    left_join(IPC_HISTORICOS %>% select(Mes_Año, IPC_Historico = IPC), 
              by = c("Mes_Año_Elab" = "Mes_Año"))
  
  # Verificar matching
  registros_sin_ipc <- sum(is.na(datos_completos$IPC_Historico))
  
  if (registros_sin_ipc > 0) {
    cat("ADVERTENCIA:", registros_sin_ipc, "registros sin IPC historico\n")
    cat("   Estas fechas no tienen IPC disponible:\n")
    fechas_problema <- datos_completos %>%
      filter(is.na(IPC_Historico)) %>%
      select(`Fecha De Elaboracion`) %>%
      distinct()
    print(fechas_problema)
  } else {
    cat("Todos los registros tienen IPC historico\n")
  }
  
  ####### 5. CALCULAR VALOR PRESENTE
  cat("\n>>> Calculando valores presentes...\n")
  
  # Función de cálculo VP
  calcular_vp <- function(valor_original, ipc_historico, ipc_actual) {
    if (is.na(valor_original) | is.na(ipc_historico)) return(NA_real_)
    factor <- ipc_actual / ipc_historico
    return(round(valor_original * factor, 2))
  }
  
  # Aplicar a las 4 columnas monetarias
  datos_completos <- datos_completos %>%
    mutate(
      # Valor Unitario
      `Valor Unitario VP` = mapply(calcular_vp, `Valor Unitario`, 
                                   IPC_Historico, ipc_sep_2025),
      `Diferencia Valor Unitario` = `Valor Unitario VP` - `Valor Unitario`,
      
      # Valor Total
      `Valor Total VP` = mapply(calcular_vp, `Valor Total`, 
                                IPC_Historico, ipc_sep_2025),
      `Diferencia Valor Total` = `Valor Total VP` - `Valor Total`,
      
      # Insumo Valor Unitario
      `Insumo_Valor Unitario VP` = mapply(calcular_vp, `Insumo_Valor Unitario`, 
                                          IPC_Historico, ipc_sep_2025),
      `Diferencia Insumo_Valor Unitario` = `Insumo_Valor Unitario VP` - `Insumo_Valor Unitario`,
      
      # Insumo Valor Neto
      `Insumo_Valor Neto VP` = mapply(calcular_vp, `Insumo_Valor Neto`, 
                                      IPC_Historico, ipc_sep_2025),
      `Diferencia Insumo_Valor Neto` = `Insumo_Valor Neto VP` - `Insumo_Valor Neto`,
      
      # Factor de conversión para referencia
      `Factor IPC` = round(ipc_sep_2025 / IPC_Historico, 6)
    )
  
  cat("Calculos completados\n")
  
  ####### 6. CREAR EXCEL DE SALIDA
  cat("\n>>> Generando archivo Excel...\n")
  
  wb <- createWorkbook()
  
  ##### HOJA 1: DATOS COMPLETOS VP
  addWorksheet(wb, "Datos Completos VP")
  
  datos_organizados <- datos_completos %>%
    select(
      # Identificadores
      "Proyecto ID" = SkIdProyecto,
      "Nombre Proyecto" = `Nombre Proyecto`,
      "Capítulo" = `Capitulo Descripcion`,
      "Item" = `Item Descripcion`,
      "Insumo" = `Insumo_Insumo Descripcion`,
      
      # Cantidad (sin modificar)
      "Cantidad" = Cantidad,
      
      # Valor Unitario
      "Valor Unitario Original" = `Valor Unitario`,
      "Valor Unitario VP" = `Valor Unitario VP`,
      "Diferencia Valor Unitario" = `Diferencia Valor Unitario`,
      
      # Valor Total
      "Valor Total Original" = `Valor Total`,
      "Valor Total VP" = `Valor Total VP`,
      "Diferencia Valor Total" = `Diferencia Valor Total`,
      
      # Insumo Valor Unitario
      "Insumo Valor Unitario Original" = `Insumo_Valor Unitario`,
      "Insumo Valor Unitario VP" = `Insumo_Valor Unitario VP`,
      "Diferencia Insumo V.Unit" = `Diferencia Insumo_Valor Unitario`,
      
      # Insumo Valor Neto
      "Insumo Valor Neto Original" = `Insumo_Valor Neto`,
      "Insumo Valor Neto VP" = `Insumo_Valor Neto VP`,
      "Diferencia Insumo V.Neto" = `Diferencia Insumo_Valor Neto`,
      
      # Metadata
      "Fecha Elaboración" = `Fecha De Elaboracion`,
      "IPC Histórico" = IPC_Historico,
      "Factor IPC" = `Factor IPC`
    )
  
  writeData(wb, "Datos Completos VP", datos_organizados)
  
  # Estilos
  headerStyle <- createStyle(
    textDecoration = "bold",
    fgFill = "#2E75B6",
    fontColour = "white",
    halign = "center",
    border = "TopBottomLeftRight",
    wrapText = TRUE
  )
  
  # Aplicar estilo a encabezados
  addStyle(wb, "Datos Completos VP", headerStyle, rows = 1, 
           cols = 1:ncol(datos_organizados), gridExpand = TRUE)
  
  # Formato numérico para columnas monetarias
  numStyle <- createStyle(numFmt = "#,##0.00", halign = "right")
  addStyle(wb, "Datos Completos VP", numStyle, 
           rows = 2:(nrow(datos_organizados)+1), 
           cols = 7:21, gridExpand = TRUE)
  
  # Ajustar anchos de columna
  setColWidths(wb, "Datos Completos VP", cols = 1:ncol(datos_organizados), 
               widths = c(12, 25, 30, 30, 35, 12, rep(18, 15)))
  
  ##### HOJA 2: RESUMEN EJECUTIVO
  addWorksheet(wb, "Resumen Ejecutivo")
  
  # Calcular estadísticas
  total_registros <- nrow(datos_completos)
  proyectos_unicos <- length(unique(datos_completos$SkIdProyecto))
  fecha_min <- min(datos_completos$Fecha_Elaboracion_Date, na.rm = TRUE)
  fecha_max <- max(datos_completos$Fecha_Elaboracion_Date, na.rm = TRUE)
  ipc_min <- min(datos_completos$IPC_Historico, na.rm = TRUE)
  ipc_max <- max(datos_completos$IPC_Historico, na.rm = TRUE)
  
  resumen <- data.frame(
    "Concepto" = c(
      "Archivo procesado",
      "Fecha de procesamiento",
      "Total de registros",
      "Proyectos únicos procesados",
      "Rango de fechas de elaboración",
      "Fecha mínima",
      "Fecha máxima",
      "IPC de referencia (Septiembre 2025)",
      "Rango IPC histórico usado",
      "IPC mínimo",
      "IPC máximo",
      "Factor de conversión promedio",
      "Incremento inflacionario promedio",
      "Columnas actualizadas a VP",
      "Registros sin IPC histórico"
    ),
    "Valor" = c(
      nombre_archivo,
      format(Sys.Date(), "%d/%m/%Y"),
      format(total_registros, big.mark = ","),
      proyectos_unicos,
      paste(format(fecha_min, "%d/%m/%Y"), "a", format(fecha_max, "%d/%m/%Y")),
      format(fecha_min, "%d/%m/%Y"),
      format(fecha_max, "%d/%m/%Y"),
      ipc_sep_2025,
      paste(round(ipc_min, 2), "a", round(ipc_max, 2)),
      round(ipc_min, 2),
      round(ipc_max, 2),
      round(mean(datos_completos$`Factor IPC`, na.rm = TRUE), 6),
      paste0(round((mean(datos_completos$`Factor IPC`, na.rm = TRUE) - 1) * 100, 2), "%"),
      "Valor Unitario, Valor Total, Insumo V.Unit, Insumo V.Neto",
      registros_sin_ipc
    )
  )
  
  writeData(wb, "Resumen Ejecutivo", resumen)
  addStyle(wb, "Resumen Ejecutivo", headerStyle, rows = 1, cols = 1:2)
  setColWidths(wb, "Resumen Ejecutivo", cols = 1:2, widths = c(40, 50))
  
  ##### HOJA 3: RESUMEN POR PROYECTO
  addWorksheet(wb, "Resumen Por Proyecto")
  
  resumen_proyectos <- datos_completos %>%
    group_by(`Nombre Proyecto`, Fecha_Elaboracion_Date, IPC_Historico) %>%
    summarise(
      Registros = n(),
      `Total Valor Original` = sum(`Valor Total`, na.rm = TRUE),
      `Total Valor VP` = sum(`Valor Total VP`, na.rm = TRUE),
      `Diferencia Total` = sum(`Diferencia Valor Total`, na.rm = TRUE),
      `Factor IPC Promedio` = mean(`Factor IPC`, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    arrange(`Nombre Proyecto`)
  
  writeData(wb, "Resumen Por Proyecto", resumen_proyectos)
  addStyle(wb, "Resumen Por Proyecto", headerStyle, rows = 1, 
           cols = 1:ncol(resumen_proyectos), gridExpand = TRUE)
  addStyle(wb, "Resumen Por Proyecto", numStyle, 
           rows = 2:(nrow(resumen_proyectos)+1), 
           cols = 4:8, gridExpand = TRUE)
  setColWidths(wb, "Resumen Por Proyecto", cols = 1:ncol(resumen_proyectos), 
               widths = c(30, 18, 15, 12, 18, 18, 18, 15))
  
  ####### 7. GUARDAR EXCEL
  saveWorkbook(wb, archivo_salida, overwrite = TRUE)
  
  cat("Excel generado exitosamente\n")
  cat("\n", rep("=", 70), "\n", sep = "")
  cat("RESUMEN FINAL\n")
  cat(rep("=", 70), "\n", sep = "")
  cat("Registros procesados:", format(total_registros, big.mark = ","), "\n")
  cat("Proyectos:", proyectos_unicos, "\n")
  cat("Archivo guardado en:", archivo_salida, "\n")
  cat(rep("=", 70), "\n", sep = "")
  
  return(list(
    archivo = archivo_salida,
    registros = total_registros,
    proyectos = proyectos_unicos
  ))
}

######## MENU PRINCIPAL ########
menu_principal <- function() {
  cat("\n")
  cat(rep("=", 70), "\n", sep = "")
  cat("   AUTOMATIZADOR VALOR PRESENTE - TABLA LOOKER FINAL\n")
  cat("   IPC BANCO DE LA REPUBLICA\n")
  cat(rep("=", 70), "\n", sep = "")
  cat("\n1. Procesar tabla_looker_final.csv\n")
  cat("2. Salir\n")
  cat("\nSeleccione una opcion (1-2): ")
  
  opcion <- readline()
  
  if (opcion == "1") {
    tryCatch({
      resultado <- procesar_tabla_looker()
      cat("\nPROCESO COMPLETADO EXITOSAMENTE\n")
    }, error = function(e) {
      cat("\nERROR:", e$message, "\n")
    })
  } else if (opcion == "2") {
    cat("\nHasta luego!\n")
  } else {
    cat("\nOpcion invalida\n")
  }
}

# EJECUTAR
menu_principal()



