# -*- coding: utf-8 -*-
# Auto-generated from conexionDB.ipynb
# Markdown cells are preserved as comments.



# ==== Cell Separator =====================================================


# [Code Cell 1]
import os
import urllib.parse
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
import pyodbc, sys, platform
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)


# ==== Cell Separator =====================================================


# [Code Cell 2]
# requerimientos
print("Python:", sys.version)
print("Arquitectura:", platform.architecture())
print("Drivers ODBC disponibles:", pyodbc.drivers())


# ==== Cell Separator =====================================================


# [Markdown Cell 3]
# # Conexion API


# ==== Cell Separator =====================================================


# [Code Cell 4]
# === 1) Parámetros  ===
SERVER   = os.getenv("SINCO_SERVER")
DATABASE = os.getenv("SINCO_DB")
USER     = os.getenv("SINCO_USER")
PASSWORD = os.getenv("SINCO_PW")
DRIVER   = "ODBC Driver 18 for SQL Server"

# vars = [SERVER, DATABASE, USER, PASSWORD]

# for var in vars:
#     print(var)


# ==== Cell Separator =====================================================


# [Code Cell 5]
# === 2) Crear SQLAlchemy engine (evita el warning de pandas) ===
odbc_params = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"UID={USER};PWD={PASSWORD};"
    "Encrypt=yes;TrustServerCertificate=yes;"
)
conn_str = "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(odbc_params)
engine = create_engine(conn_str, fast_executemany=True)


# ==== Cell Separator =====================================================


# [Code Cell 6]
# === 3) Directorio de exportación ===
out_dir = Path("export") / datetime.now().strftime("%Y%m%d")
out_dir.mkdir(parents=True, exist_ok=True)


# ==== Cell Separator =====================================================


# [Markdown Cell 7]
# # Utilidades


# ==== Cell Separator =====================================================


# [Code Cell 8]
# === 4) Utilidades ===
def listar_tablas(esquemas=None):
    """
    Retorna DataFrame con tablas BASE (no vistas). Filtra por lista de esquemas opcional.
    """
    q = """
    SELECT TABLE_SCHEMA, TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_SCHEMA, TABLE_NAME;
    """
    df = pd.read_sql(text(q), engine)
    if esquemas:
        df = df[df["TABLE_SCHEMA"].isin(esquemas)]
    return df.reset_index(drop=True)

def exportar_tabla(schema, table, chunksize=200_000, to_parquet=False):
    """
    Exporta una tabla completa en chunks a CSV (y opcional Parquet).
    Archivo: export/YYYYMMDD/schema.table.csv
    """
    dest_csv = out_dir / f"{schema}.{table}.csv"
    dest_parq = out_dir / f"{schema}.{table}.parquet"

    sql = text(f'SELECT * FROM "{schema}"."{table}"')  # comillas dobles por seguridad
    first = True
    rows = 0

    with engine.connect() as conn:
        for chunk in pd.read_sql(sql, conn, chunksize=chunksize):
            mode = "w" if first else "a"
            header = first
            chunk.to_csv(dest_csv, index=False, mode=mode, header=header)
            rows += len(chunk)
            first = False

    if to_parquet:
        # Si quieres Parquet, lo armamos leyendo de nuevo el CSV (o podrías acumular en memoria si cabe)
        df = pd.read_csv(dest_csv)
        df.to_parquet(dest_parq, index=False)

    return dest_csv, rows

def exportar_todas(esquemas=None, to_parquet=False):
    tablas = listar_tablas(esquemas)
    print(f"Encontradas {len(tablas)} tablas.")
    resumen = []
    for _, r in tablas.iterrows():
        s, t = r.TABLE_SCHEMA, r.TABLE_NAME
        print(f"→ Exportando {s}.{t} ...", end="", flush=True)
        try:
            path, n = exportar_tabla(s, t, to_parquet=to_parquet)
            print(f" OK ({n:,} filas) → {path.name}")
            resumen.append({"schema": s, "table": t, "rows": n, "file": path.name})
        except Exception as e:
            print(f" ERROR: {e}")
            resumen.append({"schema": s, "table": t, "rows": None, "file": None, "error": str(e)})
    pd.DataFrame(resumen).to_csv(out_dir / "_resumen_export.csv", index=False)
    print(f"\nResumen guardado en: {out_dir / '_resumen_export.csv'}")


# ==== Cell Separator =====================================================


# [Markdown Cell 9]
# ## diccionario de datos funciones


# ==== Cell Separator =====================================================


# [Code Cell 10]
from sqlalchemy import text
import pandas as pd

def columnas_y_llaves(esquemas=None):
    """
    Devuelve un DataFrame por columna con:
      esquema, nombre_tabla, nombre_columna, tipo_llave (PK/UK/FK/NINGUNA), relacion_aTabla (solo FK)
    Si 'esquemas' es una lista, filtra por esos schemas.
    """
    params = {}
    filtro_cols = ""
    filtro_pkuk = ""
    filtro_fk   = ""

    if esquemas:
        ph = ", ".join([f":s{i}" for i in range(len(esquemas))])
        params.update({f"s{i}": s for i, s in enumerate(esquemas)})
        filtro_cols = f"WHERE c.TABLE_SCHEMA IN ({ph})"
        filtro_pkuk = f" AND tc.TABLE_SCHEMA IN ({ph})"
        filtro_fk   = f" AND tc.TABLE_SCHEMA IN ({ph})"

    sql = text(f"""
    WITH cols AS (
        SELECT c.TABLE_SCHEMA, c.TABLE_NAME, c.COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS c
        {filtro_cols}
    ),
    pkuk AS (
        SELECT
            tc.TABLE_SCHEMA, tc.TABLE_NAME, kcu.COLUMN_NAME,
            CASE WHEN tc.CONSTRAINT_TYPE='PRIMARY KEY' THEN 'PK' ELSE 'UK' END AS tipo_llave
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
          ON kcu.CONSTRAINT_NAME   = tc.CONSTRAINT_NAME
         AND kcu.CONSTRAINT_SCHEMA = tc.CONSTRAINT_SCHEMA
         AND kcu.TABLE_NAME        = tc.TABLE_NAME
        WHERE tc.CONSTRAINT_TYPE IN ('PRIMARY KEY','UNIQUE')
        {filtro_pkuk}
    ),
    fks AS (
        SELECT
            tc.TABLE_SCHEMA, tc.TABLE_NAME, kcu.COLUMN_NAME,
            'FK' AS tipo_llave,
            rtab.TABLE_SCHEMA + '.' + rtab.TABLE_NAME AS relacion_aTabla
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc              -- FK de la tabla "hija"
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
          ON kcu.CONSTRAINT_NAME   = tc.CONSTRAINT_NAME
         AND kcu.CONSTRAINT_SCHEMA = tc.CONSTRAINT_SCHEMA
         AND kcu.TABLE_NAME        = tc.TABLE_NAME
        JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
          ON rc.CONSTRAINT_NAME    = tc.CONSTRAINT_NAME
         AND rc.CONSTRAINT_SCHEMA  = tc.CONSTRAINT_SCHEMA
        JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS rtab            -- PK/UK de la tabla "padre"
          ON rtab.CONSTRAINT_NAME   = rc.UNIQUE_CONSTRAINT_NAME
         AND rtab.CONSTRAINT_SCHEMA = rc.UNIQUE_CONSTRAINT_SCHEMA
        WHERE tc.CONSTRAINT_TYPE = 'FOREIGN KEY'
        {filtro_fk}
    )
    SELECT
        c.TABLE_SCHEMA  AS esquema,
        c.TABLE_NAME    AS nombre_tabla,
        c.COLUMN_NAME   AS nombre_columna,
        COALESCE(pkuk.tipo_llave, fks.tipo_llave, 'NINGUNA') AS tipo_llave,
        fks.relacion_aTabla
    FROM cols c
    LEFT JOIN pkuk ON pkuk.TABLE_SCHEMA = c.TABLE_SCHEMA
                  AND pkuk.TABLE_NAME   = c.TABLE_NAME
                  AND pkuk.COLUMN_NAME  = c.COLUMN_NAME
    LEFT JOIN fks  ON fks.TABLE_SCHEMA  = c.TABLE_SCHEMA
                  AND fks.TABLE_NAME    = c.TABLE_NAME
                  AND fks.COLUMN_NAME   = c.COLUMN_NAME
    ORDER BY esquema, nombre_tabla, nombre_columna;
    """)

    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params=params)


# ==== Cell Separator =====================================================


# [Code Cell 11]
from sqlalchemy import text
import pandas as pd

def columnas_pk_fk(esquemas=None):
    """
    Devuelve por COLUMNA:
      esquema, nombre_tabla, nombre_columna, tipo_llave (PK/FK/None), relacion_aTabla (solo para FK)

    - Usa INFORMATION_SCHEMA
    - Filtra por lista de esquemas si se pasa `esquemas=[...]`
    """
    params = {}
    filtro_cols = ""
    filtro_pk   = ""
    filtro_fk   = ""

    if esquemas:
        ph = ", ".join([f":s{i}" for i in range(len(esquemas))])
        params.update({f"s{i}": s for i, s in enumerate(esquemas)})
        filtro_cols = f"WHERE c.TABLE_SCHEMA IN ({ph})"
        filtro_pk   = f" AND tc.TABLE_SCHEMA IN ({ph})"
        filtro_fk   = f" AND tc.TABLE_SCHEMA IN ({ph})"

    sql = text(f"""
    WITH cols AS (
        SELECT c.TABLE_SCHEMA, c.TABLE_NAME, c.COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS c
        {filtro_cols}
    ),
    pk AS (
        SELECT
            tc.TABLE_SCHEMA, tc.TABLE_NAME, kcu.COLUMN_NAME
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
          ON kcu.CONSTRAINT_NAME   = tc.CONSTRAINT_NAME
         AND kcu.CONSTRAINT_SCHEMA = tc.CONSTRAINT_SCHEMA
         AND kcu.TABLE_NAME        = tc.TABLE_NAME
        WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
        {filtro_pk}
    ),
    fk AS (
        SELECT
            tc.TABLE_SCHEMA, tc.TABLE_NAME, kcu.COLUMN_NAME,
            rtab.TABLE_SCHEMA + '.' + rtab.TABLE_NAME AS relacion_aTabla
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc          -- constraint hija
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
          ON kcu.CONSTRAINT_NAME   = tc.CONSTRAINT_NAME
         AND kcu.CONSTRAINT_SCHEMA = tc.CONSTRAINT_SCHEMA
         AND kcu.TABLE_NAME        = tc.TABLE_NAME
        JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
          ON rc.CONSTRAINT_NAME    = tc.CONSTRAINT_NAME
         AND rc.CONSTRAINT_SCHEMA  = tc.CONSTRAINT_SCHEMA
        JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS rtab        -- constraint padre (PK/UK)
          ON rtab.CONSTRAINT_NAME   = rc.UNIQUE_CONSTRAINT_NAME
         AND rtab.CONSTRAINT_SCHEMA = rc.UNIQUE_CONSTRAINT_SCHEMA
        WHERE tc.CONSTRAINT_TYPE = 'FOREIGN KEY'
        {filtro_fk}
    )
    SELECT
        c.TABLE_SCHEMA  AS esquema,
        c.TABLE_NAME    AS nombre_tabla,
        c.COLUMN_NAME   AS nombre_columna,
        CASE
          WHEN pk.COLUMN_NAME IS NOT NULL THEN 'PK'
          WHEN fk.COLUMN_NAME IS NOT NULL THEN 'FK'
          ELSE NULL
        END AS tipo_llave,
        CASE
          WHEN fk.COLUMN_NAME IS NOT NULL THEN fk.relacion_aTabla
          ELSE NULL
        END AS relacion_aTabla
    FROM cols c
    LEFT JOIN pk ON pk.TABLE_SCHEMA = c.TABLE_SCHEMA
                AND pk.TABLE_NAME   = c.TABLE_NAME
                AND pk.COLUMN_NAME  = c.COLUMN_NAME
    LEFT JOIN fk ON fk.TABLE_SCHEMA = c.TABLE_SCHEMA
                AND fk.TABLE_NAME   = c.TABLE_NAME
                AND fk.COLUMN_NAME  = c.COLUMN_NAME
    ORDER BY esquema, nombre_tabla, nombre_columna;
    """)

    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params=params)


# ==== Cell Separator =====================================================


# [Markdown Cell 12]
# # Revisión 


# ==== Cell Separator =====================================================


# [Code Cell 13]
tablas = listar_tablas()


# ==== Cell Separator =====================================================


# [Code Cell 14]
tablas


# ==== Cell Separator =====================================================


# [Code Cell 15]
tablas.shape


# ==== Cell Separator =====================================================


# [Code Cell 16]
tablas['TABLE_SCHEMA'].unique()


# ==== Cell Separator =====================================================


# [Code Cell 17]
tablas[tablas['TABLE_SCHEMA'].isin( ['ADP_DTM_DIM',
       'ADP_DTM_FACT'])].shape


# ==== Cell Separator =====================================================


# [Code Cell 18]
tablasUsar = tablas[tablas['TABLE_SCHEMA'].isin( ['ADP_DTM_DIM','ADP_DTM_FACT'])]


# ==== Cell Separator =====================================================


# [Markdown Cell 19]
# ## Exportacion tablas


# ==== Cell Separator =====================================================


# [Code Cell 20]
# tabla = 0
# for index, row in tablasUsar.iterrows():
#     tabla+=1
#     print(f"{tabla}. {row["TABLE_SCHEMA"]}, {row["TABLE_NAME"]}")
#     exportar_tabla(row["TABLE_SCHEMA"], row["TABLE_NAME"])
#     print(f"La tabla {row["TABLE_SCHEMA"]}.{row["TABLE_NAME"]} fue exportada \n")


# ==== Cell Separator =====================================================


# [Code Cell 21]
schema = "ADI_DTM"
table =	"Proyectos"
exportar_tabla(schema, table)


# ==== Cell Separator =====================================================


# [Code Cell 22]
proyectos = pd.read_csv(r"C:\Users\Administrador\Desktop\reto\export\20251001\ADI_DTM.Proyectos.csv")


# ==== Cell Separator =====================================================


# [Code Cell 23]
proyectos.shape


# ==== Cell Separator =====================================================


# [Code Cell 24]
proyectos.head(5)


# ==== Cell Separator =====================================================


# [Markdown Cell 25]
# # diccionario de varibles


# ==== Cell Separator =====================================================


# [Code Cell 26]
df_dic = columnas_y_llaves(esquemas=["ADP_DTM_DIM", "ADP_DTM_FACT"])


# ==== Cell Separator =====================================================


# [Code Cell 27]
# # Todo
# df_dic = columnas_pk_fk()

# print(df_dic["tipo_llave"].value_counts(dropna=False))


# ==== Cell Separator =====================================================


# [Code Cell 28]
df_dic.columns


# ==== Cell Separator =====================================================


# [Code Cell 29]
len(df_dic['nombre_tabla'].unique())


# ==== Cell Separator =====================================================


# [Code Cell 30]
# df_dic.to_csv(r"C:\Users\Administrador\Desktop\reto\export\20251003\dicVars.csv", index=False)


# ==== Cell Separator =====================================================


# [Code Cell 31]
df_dic['tipo_llave'].value_counts()


# ==== Cell Separator =====================================================


# [Code Cell 32]
def listar_foreign_keys(engine):
    sql = text("""
    SELECT 
        fk.name                     AS nombre_fk,
        schp.name + '.' + tp.name   AS tabla_hija,
        cp.name                     AS columna_hija,
        schr.name + '.' + tr.name   AS tabla_padre,
        cr.name                     AS columna_padre
    FROM sys.foreign_keys fk
    JOIN sys.foreign_key_columns fkc
        ON fkc.constraint_object_id = fk.object_id
    JOIN sys.tables tp
        ON tp.object_id = fk.parent_object_id
    JOIN sys.schemas schp
        ON schp.schema_id = tp.schema_id
    JOIN sys.columns cp
        ON cp.object_id = tp.object_id
       AND cp.column_id = fkc.parent_column_id
    JOIN sys.tables tr
        ON tr.object_id = fk.referenced_object_id
    JOIN sys.schemas schr
        ON schr.schema_id = tr.schema_id
    JOIN sys.columns cr
        ON cr.object_id = tr.object_id
       AND cr.column_id = fkc.referenced_column_id
    ORDER BY tabla_hija, columna_hija;
    """)

    with engine.connect() as conn:
        df = pd.read_sql(sql, conn)

    return df


# ==== Cell Separator =====================================================


# [Code Cell 33]
listar_foreign_keys(engine)


# ==== Cell Separator =====================================================


# [Markdown Cell 34]
# # Revisión Tablas exportadas


# ==== Cell Separator =====================================================


# [Code Cell 35]
len(os.listdir('export/20251003'))


# ==== Cell Separator =====================================================


# [Code Cell 36]
empresa = pd.read_csv(r"C:\Users\Administrador\Desktop\reto\export\20251003\ADP_DTM_DIM.Empresa.csv")
programacion = pd.read_csv(r"C:\Users\Administrador\Desktop\reto\export\20251003\ADP_DTM_FACT.Programacion.csv")


# ==== Cell Separator =====================================================


# [Code Cell 37]
empresa.columns


# ==== Cell Separator =====================================================


# [Code Cell 38]
df_merge = pd.merge(empresa, programacion, on="SkIdEmpresa", how="inner")


# ==== Cell Separator =====================================================


# [Code Cell 39]
df_merge.head()