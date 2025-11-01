########### CODIGO AUTOMATIZADO PARA TODOS LOS EXCELES #################
library(readxl)
library(dplyr)
library(openxlsx)
library(stringr)

######## FUNCION PRINCIPAL - mi codigo base
procesar_presupuesto <- function(nombre_archivo) {
  
  cat(" INICIANDO PROCESAMIENTO PARA:", nombre_archivo, "\n")
  
  ####### 1 CONFIGURAR RUTAS
  ruta_completa <- file.path("input", nombre_archivo)
  nombre_base <- tools::file_path_sans_ext(nombre_archivo)
  archivo_salida <- file.path("output", paste0(nombre_base, "_IPC_BANREP_FINAL.xlsx"))
  
  ###### Verificar que el archivo existe
  if (!file.exists(ruta_completa)) {
    stop("No se encontro el archivo: ", ruta_completa)
  }
  
  cat("Archivo de entrada:", ruta_completa, "\n")
  cat("Archivo de salida:", archivo_salida, "\n")
  
  ######### 2 LEER DATOS (MISMA LOGICA QUE TU CODIGO ORIGINAL)
  fila_4 <- read_excel(ruta_completa, sheet = 1, skip = 3, n_max = 1, col_names = FALSE)
  fecha_referencia <- as.Date(fila_4[[1, 7]])
  
  ####### Leer con skip = 4 (igual que tu codigo)
  datos_completos <- read_excel(ruta_completa, sheet = 1, skip = 4, col_names = FALSE)
  
  ####### ASIGNACION DE NOMBRES (LOS QUE NECESITO)
  names(datos_completos) <- c(
    "Descripcion",        # ...1
    "Codigo_Extra1",      # ...2 (NA en la mayoria)
    "Codigo",             # ...3 (2832, 8606, etc)
    "UM",                 # ...4 (m3, un, etc)
    "Cantidad_Presup",    # ...5 (428.20, 57.76)  CANTIDAD, NO USAR
    "Insumo_Presup",      # ...6 (15.5, 13.87) VALOR MONETARIO - DEBO USAR
    "Item_Presup",        # ...7
    "Capitulo_Presup",    # ...8
    "Cantidad_Proy",      # ...9 (321.10, 57.76) CANTIDAD, NO USAR
    "Insumo_Proy",        # ...10 (13.8, 13.87) VALOR MONETARIO - DEBO USAR
    "Item_Proy",          # ...11
    "Capitulo_Proy"       # ...12
  )
  
  cat("Filas totales leidas:", nrow(datos_completos), "\n")
  
  ###### 3 CONFIGURAR IPC 
  fecha_pasado <- as.Date("2023-02-10")
  ipc_feb_2023 <- 130.40
  ipc_sep_2025 <- 151.48
  
  cat(" IPC CONFIGURADO (BANCO DE LA REPUBLICA - FIN MES):\n")
  cat("- IPC Febrero 2023:", ipc_feb_2023, "\n")
  cat("- IPC Septiembre 2025:", ipc_sep_2025, "\n")
  cat("- Factor de conversion:", round(ipc_sep_2025 / ipc_feb_2023, 8), "\n")
  cat("- Incremento inflacionario:", round((ipc_sep_2025 / ipc_feb_2023 - 1) * 100, 4), "%\n")
  
  ########## 4 FUNCIONES 
  limpiar_valor_mejorada <- function(x) {
    if (is.character(x)) {
      valor_limpio <- gsub("[\\(\\)$, ]", "", x)
      as.numeric(valor_limpio)
    } else {
      as.numeric(x)
    }
  }
  
  ##### FORMULA VP 
  
  calcular_valor_presente_vector <- function(vector_pasado, ipc_pasado, ipc_presente) {
    factor <- ipc_presente / ipc_pasado
    sapply(vector_pasado, function(valor) {
      if (is.na(valor)) return(NA_real_)
      valor_presente <- valor * factor
      return(round(valor_presente, 2))
    })
  }
  
  ##### 5. APLICAR LIMPIEZA Y CALCULOS 
  datos_final <- datos_completos
  
  ######### Limpiar las columnas CORRECTAS QUE NECESUTI(Insumo, columnas 6 y 10)
  datos_final$Insumo_Presup_Num <- limpiar_valor_mejorada(datos_final$Insumo_Presup)
  datos_final$Insumo_Proy_Num <- limpiar_valor_mejorada(datos_final$Insumo_Proy)
  
  ############ Aplicar valor presente
  datos_final$Insumo_Presup_VP <- calcular_valor_presente_vector(
    datos_final$Insumo_Presup_Num, ipc_feb_2023, ipc_sep_2025
  )
  
  datos_final$Insumo_Proy_VP <- calcular_valor_presente_vector(
    datos_final$Insumo_Proy_Num, ipc_feb_2023, ipc_sep_2025
  )
  ####### Calcular diferencias
  datos_final$Diferencia_Presup <- datos_final$Insumo_Presup_VP - datos_final$Insumo_Presup_Num
  datos_final$Diferencia_Proy <- datos_final$Insumo_Proy_VP - datos_final$Insumo_Proy_Num
  
  ####### 6. IDENTIFICAR CAPITULOS (MISMO CODIGO)
  datos_final <- datos_final %>%
    mutate(
      Numero_Capitulo = case_when(
        str_detect(Descripcion, "^CAPITULO \\d") ~ str_extract(Descripcion, "CAPITULO \\d+"),
        str_detect(Descripcion, "^\\d\\.\\d{3}") ~ str_extract(Descripcion, "^\\d\\.\\d{3}"),
        TRUE ~ NA_character_
      ),
      Tipo_Fila = case_when(
        str_detect(Descripcion, "^CAPITULO") ~ "CAPITULO",
        str_detect(Descripcion, "^\\d\\.\\d{3}") & 
          !str_detect(Descripcion, "^\\d\\.\\d{3} [a-z]") ~ "SUBCAPITULO",
        !is.na(Insumo_Presup_Num) | !is.na(Insumo_Proy_Num) ~ "INSUMO",
        TRUE ~ "OTRO"
      )
    )
  
  ###### 7 CREAR EXCEL (MISMA ESTRUCTURA)
  wb <- createWorkbook()
  
  # Hoja 1: Presupuesto Completo VP
  addWorksheet(wb, "Presupuesto Completo VP")
  
  datos_organizados <- datos_final %>%
    select(
      "Numero Capitulo" = Numero_Capitulo,
      "Descripcion" = Descripcion,
      "Cantidad Presupuestada" = Cantidad_Presup,
      "Insumo Presupuestado ($)" = Insumo_Presup_Num,
      "Insumo Presupuestado VP ($)" = Insumo_Presup_VP,
      "Diferencia Inflacion ($)" = Diferencia_Presup,
      "Cantidad Proyectada" = Cantidad_Proy,
      "Insumo Proyectado ($)" = Insumo_Proy_Num,
      "Insumo Proyectado VP ($)" = Insumo_Proy_VP,
      "Diferencia Inflacion Proy ($)" = Diferencia_Proy
    )
  
  writeData(wb, "Presupuesto Completo VP", datos_organizados)
  
  ##### Formatos (iGUAL A MI CODIGO)
  addStyle(wb, "Presupuesto Completo VP", 
           style = createStyle(numFmt = "#,##0.00", halign = "right"),
           rows = 2:(nrow(datos_organizados)+1), 
           cols = 4:10, gridExpand = TRUE)
  
  addStyle(wb, "Presupuesto Completo VP",
           style = createStyle(halign = "left"),
           rows = 2:(nrow(datos_organizados)+1),
           cols = 1:2, gridExpand = TRUE)
  
  headerStyle <- createStyle(
    textDecoration = "bold",
    fgFill = "#2E75B6",
    fontColour = "white",
    halign = "center",
    border = "TopBottomLeftRight"
  )
  
  addStyle(wb, "Presupuesto Completo VP", headerStyle, rows = 1, cols = 1:10)
  
  # Hoja 2: Resumen Ejecutivo
  addWorksheet(wb, "Resumen Ejecutivo")
  
  datos_con_valores <- datos_final %>%
    filter(!is.na(Insumo_Presup_Num) | !is.na(Insumo_Proy_Num))
  
  resumen_ejecutivo <- data.frame(
    "Concepto" = c(
      "Proyecto",
      "Total filas en el documento",
      "Filas con valores de insumo",
      "Capitulos identificados",
      "Fecha de referencia (pasado)",
      "Fecha de valor presente", 
      "IPC Febrero 2023 (BANREP - fin mes)",
      "IPC Septiembre 2025 (BANREP - fin mes)",
      "Factor de conversion",
      "Incremento porcentual"
    ),
    "Valor" = c(
      nombre_base,
      nrow(datos_final),
      nrow(datos_con_valores),
      sum(datos_final$Tipo_Fila == "CAPITULO", na.rm = TRUE),
      format(fecha_pasado, "%d/%m/%Y"),
      format(fecha_referencia, "%d/%m/%Y"),
      ipc_feb_2023,
      ipc_sep_2025,
      round(ipc_sep_2025 / ipc_feb_2023, 8),
      paste0(round((ipc_sep_2025 / ipc_feb_2023 - 1) * 100, 4), "%")
    )
  )
  
  writeData(wb, "Resumen Ejecutivo", resumen_ejecutivo)
  addStyle(wb, "Resumen Ejecutivo", headerStyle, rows = 1, cols = 1:2)
  
  ###### Guardar
  saveWorkbook(wb, archivo_salida, overwrite = TRUE)
  
  ###### 8 VERIFICACION FINAL
  cat("\nVERIFICACION AVANZADA PARA", nombre_base, ":\n")
  
  conteo_por_tipo <- datos_final %>%
    group_by(Tipo_Fila) %>%
    summarise(
      Cantidad = n(),
      Con_Insumo_Presup = sum(!is.na(Insumo_Presup_Num)),
      Con_Insumo_Proy = sum(!is.na(Insumo_Proy_Num))
    )
  
  print(conteo_por_tipo)
  
  cat("\nEXCEL CREADO EXITOSAMENTE\n")
  cat("Archivo:", archivo_salida, "\n")
  
  # Retornar estadisticas para reporte consolidado
  return(list(
    proyecto = nombre_base,
    filas_totales = nrow(datos_final),
    filas_con_valores = nrow(datos_con_valores),
    capitulos = sum(datos_final$Tipo_Fila == "CAPITULO", na.rm = TRUE),
    archivo_salida = archivo_salida
  ))
}

##### INTERFAZ 

# Opcion 1: Procesar un archivo especifico
procesar_archivo_especifico <- function() {
  cat("\nMODO: Procesar archivo especifico\n")
  cat("Archivos disponibles en la carpeta 'input':\n")
  
  # Listar archivos disponibles
  archivos_disponibles <- list.files("input", pattern = "\\.xlsx$")
  
  if (length(archivos_disponibles) == 0) {
    cat("No hay archivos .xlsx en la carpeta 'input'\n")
    return(NULL)
  }
  
  for (i in seq_along(archivos_disponibles)) {
    cat(i, ":", archivos_disponibles[i], "\n")
  }
  
  cat("\nIngrese el numero del archivo a procesar: ")
  seleccion <- as.numeric(readline())
  
  if (seleccion %in% seq_along(archivos_disponibles)) {
    nombre_archivo <- archivos_disponibles[seleccion]
    resultado <- procesar_presupuesto(nombre_archivo)
    return(resultado)
  } else {
    cat("Seleccion invalida\n")
    return(NULL)
  }
}

# Opcion 2: Procesar todos los archivos
procesar_todos_los_archivos <- function() {
  cat("\nMODO: Procesar TODOS los archivos\n")
  
  archivos_disponibles <- list.files("input", pattern = "\\.xlsx$")
  
  if (length(archivos_disponibles) == 0) {
    cat("No hay archivos .xlsx en la carpeta 'input'\n")
    return(NULL)
  }
  
  cat("Se procesaran", length(archivos_disponibles), "archivos:\n")
  print(archivos_disponibles)
  
  resultados <- list()
  
  for (archivo in archivos_disponibles) {
    cat("\n", rep("=", 50), "\n")
    resultado <- procesar_presupuesto(archivo)
    resultados[[length(resultados) + 1]] <- resultado
  }
  
  # Reporte consolidado
  cat("\nREPORTE CONSOLIDADO DE TODOS LOS PROYECTOS\n")
  cat(rep("=", 60), "\n")
  
  for (res in resultados) {
    cat("- Proyecto:", res$proyecto, "\n")
    cat("  Filas totales:", res$filas_totales, "\n")
    cat("  Filas con valores:", res$filas_con_valores, "\n")
    cat("  Capitulos:", res$capitulos, "\n")
    cat("  Archivo:", basename(res$archivo_salida), "\n\n")
  }
  
  return(resultados)
}

######### MENU
menu_principal <- function() {
  cat("AUTOMATIZADOR DE PRESUPUESTOS - IPC BANCO DE LA REPUBLICA\n")
  cat(rep("=", 60), "\n")
  cat("1. Procesar un archivo especifico\n")
  cat("2. Procesar TODOS los archivos de la carpeta 'input'\n")
  cat("3. Salir\n")
  cat("\nSeleccione una opcion (1-3): ")
  
  opcion <- readline()
  
  switch(opcion,
         "1" = procesar_archivo_especifico(),
         "2" = procesar_todos_los_archivos(),
         "3" = cat("Hasta luego!\n"),
         cat("Opcion invalida\n")
  )
}

#
menu_principal()

