import sqlite3
import os
import sys

def conectar_gpkg(db_path):
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        sys.exit(1)

def leer_t_ids(txt_path):
    if not os.path.exists(txt_path):
        print(f"Error: El archivo {txt_path} no existe.")
        sys.exit(1)
    
    with open(txt_path, 'r') as f:
        t_ids = {line.strip() for line in f if line.strip().isdigit()}
    return t_ids

def obtener_tablas_relacionadas(conn, tabla_objetivo, clave_primaria):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = [row[0] for row in cursor.fetchall()]
    
    relaciones = {}
    for tabla in tablas:
        cursor.execute(f"PRAGMA foreign_key_list({tabla})")
        for fk in cursor.fetchall():
            if fk[2] == tabla_objetivo:
                relaciones[tabla] = fk[3]
    
    return relaciones

def eliminar_registros(conn, tabla_objetivo, t_ids, relaciones):
    cursor = conn.cursor()
    registros_inexistentes = set()
    registros_eliminados = set()
    
    for t_id in t_ids:
        cursor.execute(f"SELECT COUNT(*) FROM {tabla_objetivo} WHERE T_Id = ?", (t_id,))
        if cursor.fetchone()[0] == 0:
            registros_inexistentes.add(t_id)
            continue
        
        for tabla, columna in relaciones.items():
            cursor.execute(f"DELETE FROM {tabla} WHERE {columna} = ?", (t_id,))
        
        cursor.execute(f"DELETE FROM {tabla_objetivo} WHERE T_Id = ?", (t_id,))
        registros_eliminados.add(t_id)
    
    conn.commit()
    return registros_inexistentes, registros_eliminados

def escribir_reporte(reporte_path, total_inicial, registros_inexistentes, registros_eliminados, total_final):
    with open(reporte_path, 'w') as f:
        f.write(f"Total de registros en la tabla antes de la eliminación: {total_inicial}\n")
        f.write(f"Total de registros eliminados: {len(registros_eliminados)}\n")
        f.write(f"Total de registros inexistentes en el .txt: {len(registros_inexistentes)}\n")
        f.write(f"Registros inexistentes: {', '.join(registros_inexistentes) if registros_inexistentes else 'Ninguno'}\n")
        f.write(f"Total de registros en la tabla después de la eliminación: {total_final}\n")

def obtener_ruta_reporte(reporte_path):
    """Verifica si el reporte_path es un directorio y genera el nombre del archivo de reporte."""
    if os.path.isdir(reporte_path):
        reporte_archivo = os.path.join(reporte_path, "reporte_eliminacion.txt")
    elif reporte_path.lower().endswith(".txt"):
        reporte_archivo = reporte_path
    else:
        print("Error: La ruta del reporte debe ser un directorio o un archivo .txt válido.")
        sys.exit(1)
    
    return reporte_archivo

def main(db_path, txt_path, reporte_path):
    conn = conectar_gpkg(db_path)
    t_ids = leer_t_ids(txt_path)
    
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM cca_predio")
    total_inicial = cursor.fetchone()[0]
    
    relaciones = obtener_tablas_relacionadas(conn, "cca_predio", "T_Id")
    registros_inexistentes, registros_eliminados = eliminar_registros(conn, "cca_predio", t_ids, relaciones)
    
    cursor.execute("SELECT COUNT(*) FROM cca_predio")
    total_final = cursor.fetchone()[0]
    
    # Obtener la ruta válida para el archivo de reporte
    reporte_archivo = obtener_ruta_reporte(reporte_path)

    escribir_reporte(reporte_archivo, total_inicial, registros_inexistentes, registros_eliminados, total_final)
    
    conn.close()
    print(f"Proceso completado. Reporte generado en {reporte_archivo}")

if __name__ == "__main__":
    # DEFINICIÓN DE RUTAS:
    db_path = r"C:\ACC\CONSOLIDACION_MANZANAS\LIMPIEZA_GPKG_RURAL_10022025\consolidado_captura_campo_20250206.gpkg"
    txt_path = r"C:\ACC\CONSOLIDACION_MANZANAS\LIMPIEZA_GPKG_RURAL_10022025\predios_eliminar.txt"
    reporte_path = r"C:\ACC\CONSOLIDACION_MANZANAS\LIMPIEZA_GPKG_RURAL_10022025"  # Carpeta donde se guardará el reporte

    main(db_path, txt_path, reporte_path)