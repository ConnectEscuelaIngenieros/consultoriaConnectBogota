# 🧱 Exploración de la Base de Datos ARPRO

Este repositorio contiene los scripts, conexiones y notebooks utilizados para analizar la estructura y las relaciones de la **base de datos ARPRO** de proyectos de construcción.

---

## 📂 Estructura del proyecto

```
Base de Datos ARPRO/
│
├── 20251003/              # Último respaldo de datos (CSV, XLS, XLSX)
├── anteriores/            # Versiones anteriores de la base de datos
├── scripts/               # Scripts de Python y Jupyter
├── outputs/               # Reportes o resultados procesados
├── .venv/                 # Entorno virtual local (ignorado por Git)
├── requirements.txt       # Dependencias de Python
├── setup.ps1              # Instalador automático para Windows
└── README.md
```

---

## 🧰 Instalación y configuración (Windows)

### 1️⃣ Permitir ejecución de scripts en PowerShell
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

### 2️⃣ Ejecutar el instalador
```powershell
.\setup.ps1
```

Este script:
- Crea un entorno virtual `.venv`
- Instala dependencias desde `requirements.txt`
- Verifica la presencia del **ODBC Driver 18** para SQL Server

---

## 🗄️ Archivos de datos (excluidos del repositorio)

Los datos originales de ARPRO **no se versionan en GitHub** por su tamaño y confidencialidad.

Ruta local de ejemplo:

```
C:\Users\aleja\Documents\Ingenieria Estadistica\
Asignaturas2025B\arpro1\Base de Datos ARPRO\20251003\
```

Archivos principales:
- `ADP_DTM_DIM.Items.csv`
- `ADP_DTM_FACT.Proyeccion.csv`
- `ADP_DTM_DIM.Proyecto.csv`
- `ADP_DTM_DIM.Insumo.csv`
- `ADP_DTM_FACT.Acta.csv`

---

## 📊 Objetivo del análisis

1. Comprender cómo se relacionan los **ítems e insumos**  
2. Reconstruir la jerarquía de **proyectos y macroproyectos**
3. Explorar **ítems comunes entre proyectos**
4. Generar **matrices de adyacencia e intersección**
5. Preparar los datos para **modelado SQL o grafos**

### Flujo típico en Python:

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
- `pandas`, `numpy` — manejo de datos  
- `SQLAlchemy`, `pyodbc` — conexión a bases SQL  
- `matplotlib` — visualización opcional  
- `jupyter` — notebooks interactivos  

---

## 📓 Notebooks principales

### `Codigo Tabla final.ipynb`
Notebook principal para la construcción de la tabla final consolidada. Realiza:
- Carga de datos desde los CSV en `20251003/` (Proyección, Items, Proyecto, Capítulo Presupuesto, Insumo)
- Merges secuenciales mediante llaves (`SkIdProyecto`, `SkIdCapitulo`, `SkIdItems`, `SkIdInsumo`)
- Limpieza de duplicados y prefijado de columnas para evitar colisiones
- Selección de columnas relevantes para análisis
- Exportación de resultados a `tabla_looker.csv` y `tabla_looker_final.csv`
- **Exportación por proyecto**: genera un CSV individual por cada "Nombre Proyecto" en la carpeta `tablasProyect/`, con nombres de archivo saneados (sin acentos, espacios o caracteres especiales)

### `consultas.ipynb`
Notebook de consultas exploratorias y análisis ad-hoc sobre la base de datos ARPRO. Incluye:
- Consultas SQL directas (si se conecta a la base)
- Exploraciones de datos (EDA) sobre los CSV exportados
- Cálculos de métricas, conteos y agregaciones
- Prototipos de análisis que luego se integran en el flujo principal

---

## 🧹 Política de exclusión (.gitignore)

El archivo `.gitignore` excluye:
- Todos los `.csv`, `.xls`, `.xlsx`, `.zip`
- Carpetas locales (`20251003/`, `anteriores/`)
- Notebooks pesados, logs y archivos temporales

---

## 📁 Buenas prácticas

- Mantener las rutas de datos **locales y configurables**
- No subir datos ni exportaciones de Excel
- Usar `.env` para credenciales o cadenas de conexión
- Asegurar que cada notebook sea reproducible

---

## 👤 Autor

**Rafael A. Baracaldo D.**  
📚 Ingeniería Estadística — Escuela Colombiana de Ingeniería  
🧩 Proyecto 2025: *Estructura relacional de bases ARPRO*

---

## 🪪 Licencia

Uso académico y de investigación privada únicamente.
