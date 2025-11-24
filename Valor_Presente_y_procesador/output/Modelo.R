
# Librerías ---------------------------------------------------------------
library(readr)
library(dlookr)
library(dplyr)
library(stringr)

# Importar Tabla Final ----------------------------------------------------


archivo = "base_insumos3.csv"
df <- read_delim(
  archivo,
  delim = ",",
  locale = locale(
    decimal_mark = ".",
    grouping_mark = ",",   # muy importante para tu caso
    encoding = "UTF-8"
  ),
  quote = "\"",
  trim_ws = TRUE
)
options(digits = 15)   # más dígitos al imprimir


#View(df)

#View(diagnose(df))


# Capitulos homologados ---------------------------------------------------
colnames(df)[1:6]

lista<-unique(df$descripcion_candidato
)
length(unique(df$descripcion_candidato
))
df %>% 
  select(last_col(3):last_col()) %>% 
  distinct() %>% 
  dim()

print(lista)




# EDA ---------------------------------------------------------------------

names(df)

# Tipos unicos de variables
unique(df$Tipo_Fila)
length(unique(df$Nombre_Proyecto)) 
unique(df$Tipo_Edificacion)

df %>% 
  filter(Tipo_Fila == "TOTAL" & Nombre_Estructura == "TOTAL") %>% 
  select(Nombre_Estructura, Nombre_Proyecto, ends_with("_VP")) %>% 
  View()


# Tabla Modelo ------------------------------------------------------------
df %>% 
  filter(Tipo_Fila == "TOTAL" & Nombre_Estructura == "TOTAL") %>% 
  select(Nombre_Estructura, Nombre_Proyecto, ends_with("_VP")) %>% 
  names()


modelo =
  df %>% 
    filter(Tipo_Fila == "TOTAL" & Nombre_Estructura == "TOTAL") %>% 
    select(
      Codigo_Proyecto,
      Nombre_Proyecto,
      Fecha_De_Elaboracion,
      Tipo_Edificacion,
      Presup_Valor_VP,
      Comprado_Valor_VP,
      Consumido_Valor_VP
    );View(modelo)

modelo <- modelo %>%
  mutate(VIS_ind = if_else(str_starts(Tipo_Edificacion, "VIS"), 1, 0))

names(modelo)
cor(modelo[,c('Presup_Valor_VP', 'Comprado_Valor_VP', 'Consumido_Valor_VP')])


modelo1 <- lm(
  Consumido_Valor_VP ~ Presup_Valor_VP + Tipo_Edificacion,
  data = modelo
)

summary(modelo1)
