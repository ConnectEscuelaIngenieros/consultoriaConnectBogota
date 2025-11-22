
# Importar informe --------------------------------------------------------

library(rvest)
library(xml2)
library(dplyr)

file_path <- "201 - Seguimiento Insumos.xls"

# Leer el archivo como HTML
html_doc <- read_html(file_path)

# Extraer la primera tabla
df_raw <- html_doc %>%
  html_element("table") %>%
  html_table(fill = TRUE)

# Mostrar primeras filas
head(df_raw)

