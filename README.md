# 🧱 Exploración de la Base de Datos ARPRO

Este repositorio contiene los scripts, conexiones y notebooks utilizados para analizar la estructura y las relaciones de la **base de datos ARPRO** de proyectos de construcción.
# cambio de prueba
---

## 📂 Estructura del proyecto

```

Base de Datos ARPRO/
│
├── CODIGOS_YAN/                     # Scripts de Yan para procesamiento o integración
│
├── Codigo Tabla final.ipynb         # Notebook principal para generación de tablas del dashboard
├── conexionDB.ipynb                 # Conexión a la base de datos (versión notebook)
├── conexionDB.py                    # Conexión a la base de datos (versión script Python)
├── consultas.ipynb                  # Análisis de tasas de valores nulos y consultas exploratorias
├── Concatenador_..._.ipynb          # Herramienta para tener descripción jerárquica concatenada - útil para el homologador
│
├── Modelo APPY SINCO-2025-10-16-160041.svg   # Diagrama SVG del modelo APPY SINCO
├── Modelo APPY SINCO-2025-10-16-169000.png   # Imagen PNG del modelo APPY SINCO
│
├── instalaciones.txt                # Guía de instalación de dependencias o librerías locales
├── requirements.txt                 # Dependencias principales del proyecto
├── requirements_PC_ARPRO.txt        # Dependencias específicas del entorno PC_ARPRO
│
├── tableDescriptions.csv            # Descripciones y metadatos de las tablas de la base de datos
│
├── .gitattributes                   # Configuración de atributos de Git (normalización de EOL, etc.)
├── .gitignore                       # Archivos y carpetas ignoradas por Git (como .venv, __pycache__, etc.)
│
└── README.md                        # Documentación principal del proyecto (actualizada)
```

---

## 👤 Autores

**Rafael A. Baracaldo D.**  
📚 Ingeniería Estadística — Escuela Colombiana de Ingeniería  
🧩 Proyecto 2025: *Estructura relacional de bases ARPRO*

**Juan Sebastián Ramírez Ayala**  
📚 Ingeniería Estadística — Escuela Colombiana de Ingeniería  
🧩 Proyecto 2025: *Estructura relacional de bases ARPRO*

**Diana Catalina Hernandez Rojas**  
📚 Ingeniería Estadística — Escuela Colombiana de Ingeniería  
🧩 Proyecto 2025: *Estructura relacional de bases ARPRO*

**Yan Carlos Guerra Moreno**  
📚 Ingeniería Estadística — Escuela Colombiana de Ingeniería  
🧩 Proyecto 2025: *Estructura relacional de bases ARPRO*

---

## 🗄️ Archivos de datos (excluidos del repositorio)

Los datos originales de ARPRO **no se versionan en GitHub** por su tamaño y confidencialidad.

---

## 🧹 Política de exclusión (.gitignore)

El archivo `.gitignore` excluye:
- Todos los `.csv`, `.xls`, `.xlsx`, `.zip`
- Carpetas locales (`20251003/`, `anteriores/`)
- Notebooks pesados, logs y archivos temporales

---

## 📊 Objetivo del análisis

1. Comprender cómo se relacionan los **ítems e insumos**  
2. Reconstruir la jerarquía de **proyectos y macroproyectos**
3. Explorar **ítems comunes entre proyectos**
4. Generar **matrices de adyacencia e intersección**
5. Preparar los datos para **modelado SQL o grafos**


---

### Flujo típico en Python:

Ruta local de ejemplo:

```
C:\Users\aleja\Documents\Ingenieria Estadistica\
Asignaturas2025B\arpro1\Base de Datos ARPRO\20251003\
```

Archivos principales:
- Tablas dimensión `ADP_DTM_DIM`
- Tablas dimensión `ADP_DTM_FACT`

```python
# 1. Cargar tablas (Items, Proyección, Proyecto, Insumo)
# 2. Unir mediante llaves comunes (SkIdItems, SkIdProyecto)
# 3. Calcular intersecciones de ítems entre proyectos
# 4. Resumir conteos por proyecto y macroproyecto
```

---

## ⚙️ Dependencias

Ver [`requirements.txt`](./requirements.txt).  
Principales librerías:

```bash
pip install -r requirements.txt
```

También estan las dependencias implementadas en la extracción de datos mediante la conexión remota al PC de la empresa
`./requirements_PC_ARPRO.txt`
---

## 📓 Notebooks principales

### `consultas.ipynb`

- *Exploración inicial de datos*
    
    - Carga los CSV base.
        
    - Muestra columnas, conteos y valores nulos por tabla.
        
    - Detecta llaves SkId* y relaciones entre tablas.
- *Matriz de adyacencias (relaciones entre tablas)*
	
	- Detecta llaves SkId* y construye grafo de dependencias.
    
- *Exporta:*
    
    - __edges_detectados.csv (aristas: origen, destino, columna_origen)
        
    - __adyacencia_dirigida.csv
        
    - __adyacencia_no_dirigida.csv
        
- *Dimensiones por tabla*
    
    - Calcula número de filas y columnas de cada CSV.
        
    - Exporta __table_dimensions.csv.
        
- *Valores faltantes*
    
    - Calcula porcentaje de nulos por columna.
        
    - Exporta resultados individuales y globales en __missing_values/.
        
- *EDA automatizado de base de datos relacional multitabla (DataPrep)*- En Construcción
    
    - Genera perfiles HTML para cada tabla.
        
    - Guarda en _profiles_dataprep/.
        
- *Intersecciones de ítems*
    
    - Construye matriz Proyecto × Ítem.
        
    - Calcula intersecciones y similitudes entre proyectos.
        
- *EDA de Empresas y Proyectos*
    
    - Analiza estados, clases, tipos y fechas de proyectos.
        
    - Resume características de empresas.
    
        
- *Instrumentación y depuración*
    
    - Usa mensajes [DEBUG] para seguimiento de proceso.

---
# Flujo de codigos - Funcion valor presente

Conjunto de scripts en R para ajustar valores monetarios históricos de proyectos de construcción a valor presente utilizando el Índice de Precios al Consumidor (IPC) del Banco de la República de Colombia.

**Nota**: Los tres scripts realizan la misma función principal (ajuste por inflación), pero fueron evolucionando para adaptarse a diferentes necesidades de entrada de datos y nivel de detalle requerido.

---

## Estructura de carpetas
```
Valor Presente/
│
├── input/                           # Archivos de entrada
│   ├── *.xlsx                       # Presupuestos de proyectos (múltiples archivos)
│   ├── tabla_looker_final.csv       # Tabla consolidada desde base de datos
│   └── IPC_HISTORICOS.xlsx          # Serie histórica IPC (Banco República)
│
├── output/                          # Resultados procesados
│   └── *_IPC_BANREP_FINAL.xlsx      # Excel con valores ajustados + análisis
│
├── CODIGO.R                         # Versión inicial - Batch Excel simple
├── procesar_presupuesto.R           # Versión mejorada - Excel detallado
└── VP-AJUSTADO.R                    # VERSIÓN FINAL - Tabla Looker con IPC dinámico
```

---

## Evolución de los scripts

### CODIGO.R - Versión inicial

**Propósito**: Primera implementación para procesar archivos individuales de Excel con valores monetarios únicamente.

**Entrada**:
- input/*.xlsx - Presupuestos individuales en formato específico

**Proceso**:
1. Lee estructura jerárquica: CAPÍTULO → SUBCAPÍTULO → ÍTEM → INSUMO
2. Extrae fecha de referencia de la fila 4 del Excel
3. Aplica IPC fijo (Febrero 2023: 130.40 → Septiembre 2025: 151.48)
4. Calcula VP para:
   - Insumo Presupuestado
   - Insumo Proyectado

**Salida**: Excel con 2 hojas
- Presupuesto Completo VP: Solo valores monetarios ajustados (sin cantidades)
- Resumen Ejecutivo: Metadatos del proyecto y factores IPC

**Interfaz**: Menú interactivo para procesar archivo específico o todos los de input

**Características**:
- Ajuste inflacionario funcional
- Procesamiento batch
- Sin columnas de cantidad
- IPC fijo (no considera fecha real de elaboración)

---

### procesar_presupuesto.R - Versión mejorada

**Propósito**: Mejora de CODIGO.R agregando columnas de cantidad para análisis más completo.

**Entrada**:
- input/*.xlsx - Presupuestos individuales en formato específico

**Proceso**:
1. Lee estructura jerárquica: CAPÍTULO → SUBCAPÍTULO → ÍTEM → INSUMO
2. Extrae fecha de referencia de la fila 4 del Excel
3. Aplica IPC fijo (Febrero 2023: 130.40 → Septiembre 2025: 151.48)
4. Calcula VP para:
   - Insumo Presupuestado
   - Insumo Proyectado

**Salida**: Excel con 2 hojas
- Presupuesto Completo VP: Incluye cantidades presupuestadas y proyectadas + valores ajustados
- Resumen Ejecutivo: Metadatos del proyecto y factores IPC

**Interfaz**: Menú interactivo para procesar archivo específico o todos los de input

---

### VP-AJUSTADO.R - VERSIÓN FINAL

**Propósito**: Versión definitiva para procesar tabla_looker_final.csv extraída de la base de datos ARPRO

**Entrada**:
- tabla_looker_final.csv - Tabla consolidada con múltiples proyectos
- IPC_HISTORICOS.xlsx - Serie completa de IPC historicos

**Proceso**:
1. Carga IPC históricos y limpia fechas seriales de Excel
2. Lee tabla Looker con información de proyectos, ítems e insumos
3. Extrae fecha de elaboración de cada registro y hace matching automático con IPC correspondiente
4. Calcula valor presente para 4 columnas monetarias:
   - Valor Unitario
   - Valor Total
   - Insumo Valor Unitario
   - Insumo Valor Neto
5. Aplica fórmula: VP = Valor Original × (IPC Actual / IPC Histórico)

**Salida**: Excel con 3 hojas
- Datos Completos VP: Tabla con valores originales, ajustados y diferencias
- Resumen Ejecutivo: Estadísticas generales (registros, proyectos, rangos IPC)
- Resumen Por Proyecto: Totales agregados por proyecto

---

## Fórmula de Valor Presente
```
VP = Valor_Original × (IPC_Actual / IPC_Histórico)
Diferencia = VP - Valor_Original
Factor_IPC = IPC_Actual / IPC_Histórico
```


### ⚙️ conexionDB.ipynb — Conectividad y exportación SINCO

1. **Configuración de conexión**
   - Lee credenciales (`SINCO_SERVER`, `SINCO_DB`, `SINCO_USER`, `SINCO_PW`) desde variables de entorno.
   - Define `DRIVER = "ODBC Driver 18 for SQL Server"`.
   - Crea `engine` con SQLAlchemy usando conexión ODBC codificada.
   - Imprime información de entorno: versión de Python, arquitectura y drivers ODBC disponibles.

2. **Gestión de exportaciones**
   - Crea carpeta automática `export/YYYYMMDD/` según la fecha actual.

3. **Listado de tablas**
   - `listar_tablas(esquemas=None)` obtiene nombres de tablas desde `INFORMATION_SCHEMA.TABLES`.
   - Filtra por esquema opcional.

4. **Exportación de datos**
   - `exportar_tabla(schema, table, chunksize=200_000, to_parquet=False)` guarda cada tabla completa en CSV (o Parquet opcional).
   - `exportar_todas(esquemas=None, to_parquet=False)` exporta todas las tablas y genera `_resumen_export.csv`.

5. **Llaves y relaciones**
   - `columnas_y_llaves(esquemas=None)` obtiene tipo de llave (`PK`, `UK`, `FK`) y tabla relacionada.
   - `columnas_pk_fk(esquemas=None)` resume llaves primarias y foráneas por columna.
   - `listar_foreign_keys(engine)` usa `sys.*` para listar relaciones hijo–padre.

6. **Descripción de columnas**
   - `describe_table(engine, schema, table)` devuelve tipo de dato, longitud, nulos y valores por defecto.
   - `tables_describe(schemas:list)` genera `tableDescriptions.csv` con metadatos completos.

7. **Pruebas y validación**
   - Carga CSV de ejemplo (`ADP_DTM_DIM.Empresa.csv`, `ADP_DTM_FACT.Programacion.csv`).
   - Realiza merge de prueba y muestra columnas para verificación.

---

### 📋 Diccionario de datos API

 El archivo `tableDescriptions.csv` es un diccionario de datos consolidado que documenta la información disponible de estructura  de las tablas ARPRO. Generado automáticamente mediante la función `tables_describe()`

- **schema_name**: Esquema de la tabla (`ADP_DTM_DIM` o `ADP_DTM_FACT`)
- **table_name**: Nombre de la tabla
- **COLUMN_NAME**: Nombre de cada columna
- **DATA_TYPE**: Tipo de dato SQL (varchar, int, bigint, money, etc.)
- **CHARACTER_MAXIMUM_LENGTH**: Longitud máxima para campos de texto
- **IS_NULLABLE**: Indica si la columna acepta valores nulos
- **COLUMN_DEFAULT**: Valor por defecto de la columna

**Cobertura**: 26 tablas dimensionales (DIM) + 24 tablas de hechos (FACT) = 50 tablas documentadas.

---

### `Codigo Tabla final.ipynb` 
Notebook principal para la construcción de la Tabla vizualización tablero looker. Realiza:
- Carga de datos desde los CSV en `20251003/` (Proyección, Items, Proyecto, Capítulo Presupuesto, Insumo)
- Merges secuenciales mediante llaves (`SkIdProyecto`, `SkIdCapitulo`, `SkIdItems`, `SkIdInsumo`)
- Limpieza de duplicados y prefijado de columnas para evitar colisiones
- Selección de columnas relevantes para análisis
- Exportación de resultados a `tabla_looker.csv` y `tabla_looker_final.csv`
- **Exportación por proyecto**: genera un CSV individual por cada "Nombre Proyecto" en la carpeta `tablasProyect/`, con nombres de archivo saneados (sin acentos, espacios o caracteres especiales)

---

### CODIGOS_YAN

Codigos de yan.

## 📁 Buenas prácticas

- Mantener las rutas de datos **locales y configurables**
- No subir datos ni exportaciones de Excel
- Usar `.env` para credenciales o cadenas de conexión
- Asegurar que cada notebook sea reproducible

---

### TABLERO EN LOOKER

El tablero en looker en su versión inicial estaba compacto todo en una única pestaña, se evidenció que esto no era óptimo y se desarrollo una versión 2.0 con nuevas pestañas y de una vez se dejo el espacio para la pestaña de regresión. A este tablero falta hacer unos análisis previos de los datos que alimentan el tablero.

V 0.1: https://lookerstudio.google.com/reporting/350a485d-72e9-49f9-9829-c16847ad895b
V 0.2: https://lookerstudio.google.com/reporting/b86b2ce7-7553-4816-b3bf-11f9ea4a7c14

---

## 🪪 Licencia

Uso académico y de investigación privada únicamente.
