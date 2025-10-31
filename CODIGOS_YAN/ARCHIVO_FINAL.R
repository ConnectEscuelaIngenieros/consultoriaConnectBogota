library(readr)
library(readxl)
library(dplyr)
library(lubridate)
### TABLA FINAL QUE USARE
tabla_looker_final <- read_csv("input/tabla_looker_final.csv")
View(tabla_looker_final)
names(tabla_looker_final)

##### IPC QUE NECESITO
IPC_HISTORICOS <- read_excel("IPC_HISTORICOS.xlsx")
View(IPC_HISTORICOS)

sum(is.na(tabla_looker_final$`Insumo_Fecha Modificacion`))
sum(is.na(tabla_looker_final$`Fecha De Elaboracion`))

############ EDA #########

########## ANALISIS EXPLORATORIO - TABLA LOOKER Y IPC HISTORICOS ##########

cat("="*70, "\n")
cat("ANALISIS EXPLORATORIO DE DATOS\n")
cat("="*70, "\n\n")

##### 1. CARGAR DATOS
cat(">>> CARGANDO DATOS...\n\n")

tabla_looker_final <- read_csv("tabla_looker_final.csv")
IPC_HISTORICOS <- read_excel("IPC_HISTORICOS.xlsx")

##### 2. ANALISIS TABLA LOOKER FINAL
cat("="*70, "\n")
cat("ANALISIS: tabla_looker_final.csv\n")
cat("="*70, "\n\n")

cat("--- DIMENSIONES ---\n")
cat("Filas:", nrow(tabla_looker_final), "\n")
cat("Columnas:", ncol(tabla_looker_final), "\n\n")

cat("--- NOMBRES DE COLUMNAS ---\n")
print(names(tabla_looker_final))
cat("\n")

cat("--- ESTRUCTURA DE DATOS ---\n")
str(tabla_looker_final)
cat("\n")

cat("--- PRIMERAS 10 FILAS ---\n")
print(head(tabla_looker_final, 10))
cat("\n")

cat("--- ANALISIS DE COLUMNAS MONETARIAS ---\n")
columnas_monetarias <- c("Valor Unitario", "Valor Total", 
                         "Insumo_Valor Unitario", "Insumo_Valor Neto")

for (col in columnas_monetarias) {
  if (col %in% names(tabla_looker_final)) {
    cat("\nColumna:", col, "\n")
    cat("  Clase:", class(tabla_looker_final[[col]]), "\n")
    cat("  NAs:", sum(is.na(tabla_looker_final[[col]])), "\n")
    cat("  Valores unicos:", length(unique(tabla_looker_final[[col]])), "\n")
    cat("  Rango:", min(tabla_looker_final[[col]], na.rm = TRUE), "-", 
        max(tabla_looker_final[[col]], na.rm = TRUE), "\n")
    cat("  Primeros 5 valores:\n")
    print(head(tabla_looker_final[[col]], 5))
  }
}

cat("\n--- ANALISIS DE FECHA DE ELABORACION ---\n")
cat("Clase:", class(tabla_looker_final$`Fecha De Elaboracion`), "\n")
cat("NAs:", sum(is.na(tabla_looker_final$`Fecha De Elaboracion`)), "\n")
cat("Fechas unicas:", length(unique(tabla_looker_final$`Fecha De Elaboracion`)), "\n")
cat("\nPrimeras 20 fechas:\n")
print(head(tabla_looker_final$`Fecha De Elaboracion`, 20))
cat("\nUltimas 20 fechas:\n")
print(tail(tabla_looker_final$`Fecha De Elaboracion`, 20))

cat("\n--- RANGO DE FECHAS DE ELABORACION ---\n")
fechas_elaboracion <- tabla_looker_final$`Fecha De Elaboracion`
if (is.character(fechas_elaboracion)) {
  cat("FORMATO: Texto/Character\n")
  cat("Ejemplos de valores unicos:\n")
  print(unique(fechas_elaboracion)[1:min(10, length(unique(fechas_elaboracion)))])
} else {
  cat("Fecha minima:", min(fechas_elaboracion, na.rm = TRUE), "\n")
  cat("Fecha maxima:", max(fechas_elaboracion, na.rm = TRUE), "\n")
}

cat("\n--- PROYECTOS UNICOS ---\n")
cat("Total proyectos:", length(unique(tabla_looker_final$SkIdProyecto)), "\n")
cat("Nombres de proyectos:\n")
print(unique(tabla_looker_final$`Nombre Proyecto`))

cat("\n--- DISTRIBUCION DE REGISTROS POR PROYECTO ---\n")
conteo_proyectos <- tabla_looker_final %>%
  group_by(`Nombre Proyecto`) %>%
  summarise(
    Registros = n(),
    Capitulos = n_distinct(SkIdCapitulo),
    Items = n_distinct(SkIdItems),
    Insumos = n_distinct(SkIdInsumo)
  ) %>%
  arrange(desc(Registros))

print(conteo_proyectos)

##### 3. ANALISIS IPC HISTORICOS
cat("\n")
cat("="*70, "\n")
cat("ANALISIS: IPC_HISTORICOS.xlsx\n")
cat("="*70, "\n\n")

cat("--- DIMENSIONES ---\n")
cat("Filas:", nrow(IPC_HISTORICOS), "\n")
cat("Columnas:", ncol(IPC_HISTORICOS), "\n\n")

cat("--- NOMBRES DE COLUMNAS ---\n")
print(names(IPC_HISTORICOS))
cat("\n")

cat("--- ESTRUCTURA DE DATOS ---\n")
str(IPC_HISTORICOS)
cat("\n")

cat("--- PRIMERAS 20 FILAS ---\n")
print(head(IPC_HISTORICOS, 20))
cat("\n")

cat("--- ULTIMAS 20 FILAS ---\n")
print(tail(IPC_HISTORICOS, 20))
cat("\n")

cat("--- RESUMEN ESTADISTICO ---\n")
print(summary(IPC_HISTORICOS))
cat("\n")

cat("--- VERIFICAR SI HAY COLUMNA DE FECHA ---\n")
posibles_columnas_fecha <- names(IPC_HISTORICOS)[grepl("fecha|date|mes|año|year", 
                                                       names(IPC_HISTORICOS), 
                                                       ignore.case = TRUE)]
cat("Columnas que parecen fechas:", posibles_columnas_fecha, "\n\n")

if (length(posibles_columnas_fecha) > 0) {
  for (col in posibles_columnas_fecha) {
    cat("Analizando columna:", col, "\n")
    cat("  Clase:", class(IPC_HISTORICOS[[col]]), "\n")
    cat("  Primeros 10 valores:\n")
    print(head(IPC_HISTORICOS[[col]], 10))
    cat("\n")
  }
}

cat("--- VERIFICAR SI HAY COLUMNA DE IPC ---\n")
posibles_columnas_ipc <- names(IPC_HISTORICOS)[grepl("ipc|indice|index", 
                                                     names(IPC_HISTORICOS), 
                                                     ignore.case = TRUE)]
cat("Columnas que parecen IPC:", posibles_columnas_ipc, "\n\n")

if (length(posibles_columnas_ipc) > 0) {
  for (col in posibles_columnas_ipc) {
    cat("Analizando columna:", col, "\n")
    cat("  Clase:", class(IPC_HISTORICOS[[col]]), "\n")
    cat("  Rango:", min(IPC_HISTORICOS[[col]], na.rm = TRUE), "-", 
        max(IPC_HISTORICOS[[col]], na.rm = TRUE), "\n")
    cat("  Primeros 10 valores:\n")
    print(head(IPC_HISTORICOS[[col]], 10))
    cat("\n")
  }
}

##### 4. VERIFICACION DE COMPATIBILIDAD
cat("="*70, "\n")
cat("VERIFICACION DE COMPATIBILIDAD ENTRE ARCHIVOS\n")
cat("="*70, "\n\n")

cat("--- RESUMEN PARA MATCHING ---\n")
cat("1. Fechas de Elaboracion en tabla_looker_final:\n")
cat("   - Formato detectado:", class(tabla_looker_final$`Fecha De Elaboracion`), "\n")
cat("   - Rango temporal: Ver arriba\n\n")

cat("2. Estructura del IPC_HISTORICOS:\n")
cat("   - Total registros:", nrow(IPC_HISTORICOS), "\n")
cat("   - Columnas disponibles:", paste(names(IPC_HISTORICOS), collapse = ", "), "\n\n")

cat("="*70, "\n")
cat("ANALISIS COMPLETADO\n")
cat("="*70, "\n")


################# ARREGLAR FECHAS ######

####### LIMPIAR Y PREPARAR IPC_HISTORICOS #######

cat(">>> LIMPIANDO ARCHIVO IPC_HISTORICOS.xlsx...\n\n")

# Leer saltando las primeras 3 filas (encabezados)
IPC_RAW <- read_excel("IPC_HISTORICOS.xlsx", skip = 3, col_names = FALSE)

# Asignar nombres correctos
names(IPC_RAW) <- c("Fecha_Serial", "IPC")

# Ver cómo se ve
cat("--- DATOS CRUDOS ---\n")
print(head(IPC_RAW, 20))

# Limpiar: eliminar filas con NA o texto no numérico
IPC_LIMPIO <- IPC_RAW %>%
  filter(!is.na(Fecha_Serial)) %>%
  filter(!is.na(IPC)) %>%
  # Convertir a numérico (esto eliminará filas con texto)
  mutate(
    Fecha_Serial = as.numeric(Fecha_Serial),
    IPC = as.numeric(IPC)
  ) %>%
  # Eliminar NAs resultantes de la conversión
  filter(!is.na(Fecha_Serial), !is.na(IPC))

cat("\n--- DESPUÉS DE LIMPIAR ---\n")
cat("Filas:", nrow(IPC_LIMPIO), "\n")
print(head(IPC_LIMPIO, 20))

# CONVERTIR LOS SERIALES DE EXCEL A FECHAS REALES
# Excel cuenta los días desde 1900-01-01 (pero con un error: considera 1900 bisiesto)
# En R, usamos as.Date con origin correcto

IPC_LIMPIO <- IPC_LIMPIO %>%
  mutate(
    Fecha = as.Date(Fecha_Serial, origin = "1899-12-30"),  # Origin correcto para Excel
    Año = year(Fecha),
    Mes = month(Fecha),
    Mes_Año = format(Fecha, "%Y-%m")  # Formato YYYY-MM para matching
  )

cat("\n--- CON FECHAS CONVERTIDAS ---\n")
print(head(IPC_LIMPIO, 20))
cat("\n")
print(tail(IPC_LIMPIO, 20))

# Verificar rango temporal
cat("\n--- RANGO TEMPORAL DEL IPC ---\n")
cat("Fecha mínima:", as.character(min(IPC_LIMPIO$Fecha)), "\n")
cat("Fecha máxima:", as.character(max(IPC_LIMPIO$Fecha)), "\n")
cat("Total de meses:", nrow(IPC_LIMPIO), "\n")

# Guardar versión limpia
IPC_HISTORICOS <- IPC_LIMPIO %>%
  select(Fecha, Año, Mes, Mes_Año, IPC)

cat("\n--- ESTRUCTURA FINAL ---\n")
str(IPC_HISTORICOS)
print(head(IPC_HISTORICOS, 20))

####### ANALIZAR FECHAS DE ELABORACION #######

cat("\n\n>>> ANALIZANDO FECHAS DE ELABORACION...\n\n")

# Cargar tabla looker
tabla_looker_final <- read_csv("tabla_looker_final.csv", show_col_types = FALSE)

# Convertir fechas de elaboración (están en formato dd/mm/yyyy)
tabla_looker_final <- tabla_looker_final %>%
  mutate(
    Fecha_Elaboracion_Date = dmy(`Fecha De Elaboracion`),  # dmy = day-month-year
    Año_Elab = year(Fecha_Elaboracion_Date),
    Mes_Elab = month(Fecha_Elaboracion_Date),
    Mes_Año_Elab = format(Fecha_Elaboracion_Date, "%Y-%m")
  )

cat("--- FECHAS DE ELABORACION CONVERTIDAS ---\n")
cat("Primeras 10:\n")
print(head(tabla_looker_final %>% 
             select(`Fecha De Elaboracion`, Fecha_Elaboracion_Date, Mes_Año_Elab), 10))

# Fechas únicas
fechas_unicas <- tabla_looker_final %>%
  select(Fecha_Elaboracion_Date, Mes_Año_Elab) %>%
  distinct() %>%
  arrange(Fecha_Elaboracion_Date)

cat("\n--- FECHAS UNICAS DE ELABORACION (", nrow(fechas_unicas), "total) ---\n")
print(fechas_unicas)

####### VERIFICAR MATCHING CON IPC #######

cat("\n\n>>> VERIFICANDO MATCHING ENTRE FECHAS Y IPC...\n\n")

# Intentar hacer join
matching_test <- fechas_unicas %>%
  left_join(IPC_HISTORICOS, by = c("Mes_Año_Elab" = "Mes_Año"))

cat("--- RESULTADO DEL MATCHING ---\n")
print(matching_test %>% select(Fecha_Elaboracion_Date, Mes_Año_Elab, IPC))

# Contar cuántas tienen IPC
cat("\nFechas con IPC encontrado:", sum(!is.na(matching_test$IPC)), "/", nrow(matching_test), "\n")
cat("Fechas SIN IPC:", sum(is.na(matching_test$IPC)), "\n")

# Mostrar las que NO tienen IPC
fechas_sin_ipc <- matching_test %>%
  filter(is.na(IPC))

if (nrow(fechas_sin_ipc) > 0) {
  cat("\n FECHAS SIN IPC ENCONTRADO:\n")
  print(fechas_sin_ipc %>% select(Fecha_Elaboracion_Date, Mes_Año_Elab))
}

cat("\n✓ LIMPIEZA COMPLETADA\n")

##################
####### MIRAR NEGATIVOS
tabla_looker_final %>%
  filter(`Valor Total` < 0) %>%
  select(`Nombre Proyecto`, `Valor Total`, `Item Descripcion`) %>%
  head(20)