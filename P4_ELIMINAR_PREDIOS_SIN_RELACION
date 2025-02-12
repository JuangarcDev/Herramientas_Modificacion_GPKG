import sqlite3
import pandas as pd

def analizar_gpkg(db_path, output_report):
    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    reporte_lines = []  # Lista para almacenar los mensajes del reporte

    # Contar total de registros en cca_predio
    cursor.execute("SELECT COUNT(*) FROM cca_predio")
    total_predios = cursor.fetchone()[0]
    reporte_lines.append(f"Total registros en cca_predio: {total_predios}\n")

    # Identificar registros con id_operacion duplicado
    query_duplicados = '''
    SELECT id_operacion, COUNT(*) as count
    FROM cca_predio
    GROUP BY id_operacion
    HAVING COUNT(*) > 1
    ORDER BY COUNT(*) DESC
    '''
    df_duplicados = pd.read_sql(query_duplicados, conn)
    total_duplicados = df_duplicados.shape[0]
    reporte_lines.append(f"Registros con id_operacion duplicado: {total_duplicados}\n")

    # Imprimir lista detallada de id_operacion duplicados
    if not df_duplicados.empty:
        reporte_lines.append("\nLista de id_operacion duplicados con su cantidad:\n")
        for _, row in df_duplicados.iterrows():
            reporte_lines.append(f"id_operacion: {row['id_operacion']} - Cantidad: {row['count']}\n")

    # Identificar relaciones de la tabla cca_predio
    tabla_objetivo = "cca_predio"
    clave_primaria = "T_Id"

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = [row[0] for row in cursor.fetchall()]

    tablas_relacionadas = []
    columnas_foreign_key = {}

    for tabla in tablas:
        cursor.execute(f"PRAGMA foreign_key_list({tabla})")
        foreign_keys = cursor.fetchall()
        for fk in foreign_keys:
            if fk[2] == tabla_objetivo:
                tablas_relacionadas.append(tabla)
                columnas_foreign_key[tabla] = fk[3]

    if not tablas_relacionadas:
        reporte_lines.append(f"No hay tablas relacionadas con {tabla_objetivo}.\n")
        conn.close()
        return

    # Identificar registros huérfanos
    query_huerfanos = f"SELECT cp.T_Id, cp.id_operacion, cp.Ruta FROM {tabla_objetivo} cp"
    joins = []
    conditions = []
    tablas_agregadas = set()

    for tabla in tablas_relacionadas:
        if tabla not in tablas_agregadas:
            columna_fk = columnas_foreign_key[tabla]
            alias = f"t_{tabla}"
            joins.append(f"LEFT JOIN {tabla} {alias} ON cp.{clave_primaria} = {alias}.{columna_fk}")
            conditions.append(f"{alias}.{columna_fk} IS NULL")
            tablas_agregadas.add(tabla)

    query_huerfanos += " " + " ".join(joins)
    query_huerfanos += " WHERE " + " AND ".join(conditions)

    df_huerfanos = pd.read_sql(query_huerfanos, conn)
    total_huerfanos = df_huerfanos.shape[0]
    reporte_lines.append(f"Total registros huérfanos en {tabla_objetivo}: {total_huerfanos}\n")

    # Imprimir lista detallada de registros huérfanos
    if not df_huerfanos.empty:
        reporte_lines.append("\nLista de registros huérfanos:\n")
        reporte_lines.append("T_Id | id_operacion | Ruta\n")
        for _, row in df_huerfanos.iterrows():
            reporte_lines.append(f"{row['T_Id']} | {row['id_operacion']} | {row['Ruta']}\n")

    if total_huerfanos > 0:
        reporte_lines.append(f"Se encontraron {total_huerfanos} registros huérfanos en {tabla_objetivo}.\n")
    else:
        reporte_lines.append(f"Todos los registros de {tabla_objetivo} tienen relación en otras tablas.\n")

    # Eliminar registros huérfanos
    if total_huerfanos > 0:
        ids_huerfanos = [(row['T_Id'],) for _, row in df_huerfanos.iterrows()]
        
        cursor.executemany(f"DELETE FROM {tabla_objetivo} WHERE {clave_primaria} = ?", ids_huerfanos)
        conn.commit()
        
        reporte_lines.append(f"Se eliminaron {total_huerfanos} registros huérfanos en {tabla_objetivo}.\n")
    else:
        reporte_lines.append(f"Todos los registros de {tabla_objetivo} tienen relación en otras tablas.\n")


    # Identificar registros con id_operacion duplicado pero con relaciones
    query_con_relaciones = f"""
    SELECT cp.T_Id, cp.id_operacion, cp.Ruta, 
        COUNT(DISTINCT r.table_name) AS num_tablas_relacionadas,
        GROUP_CONCAT(DISTINCT r.table_name) AS tablas_relacionadas
    FROM cca_predio cp
    LEFT JOIN (
        {" UNION ALL ".join(
            [f"SELECT '{tabla}' AS table_name, {tabla}.{columnas_foreign_key[tabla]} AS T_Id FROM {tabla}"
            for tabla in tablas_relacionadas]
        )}
    ) r ON cp.T_Id = r.T_Id
    WHERE cp.id_operacion IN (SELECT id_operacion FROM cca_predio GROUP BY id_operacion HAVING COUNT(*) > 1)
    GROUP BY cp.T_Id, cp.id_operacion
    HAVING num_tablas_relacionadas > 0
    ORDER BY cp.id_operacion, num_tablas_relacionadas DESC
    """

    df_con_relaciones = pd.read_sql(query_con_relaciones, conn)

    if not df_con_relaciones.empty:
        total_registros = len(df_con_relaciones)
        reporte_lines.append("\nRegistros con id_operacion duplicado pero con relaciones:\n")
        reporte_lines.append("T_Id | id_operacion | Cantidad_Tablas_Relacionadas | Tablas_Relacionadas | Ruta\n")
        
        for _, row in df_con_relaciones.iterrows():
            reporte_lines.append(f"{row['T_Id']} | {row['id_operacion']} | {row['num_tablas_relacionadas']} | {row['tablas_relacionadas']} | {row['Ruta']}\n")
        
        reporte_lines.append(f"\nTotal de registros que cumplen la condición DE REGISTROS CON ID_DUPLICADO PERO CON RELACIONES: {total_registros}\n")

    # Guardar el reporte
    with open(output_report, "w") as f:
        f.writelines(reporte_lines)

    # Cerrar conexión
    conn.close()
    print(f"Reporte generado: {output_report}")

# Ejecutar análisis
analizar_gpkg(r"C:\ACC\CONSOLIDACION_MANZANAS\LIMPIEZA_GPKG_RURAL_10022025\consolidado_captura_campo_20250206.gpkg", "reporte.txt")
