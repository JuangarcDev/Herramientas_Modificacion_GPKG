import sqlite3
import os
import sys

def conectar_gpkg(db_path):
    """
    Establece una conexión con la base de datos GeoPackage.
    :param db_path: Ruta del archivo .gpkg
    :return: Objeto de conexión a la base de datos
    """
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        sys.exit(1)

def leer_t_ids(txt_path):
    """
    Lee los identificadores T_Id desde un archivo de texto.
    :param txt_path: Ruta del archivo .txt con los identificadores
    :return: Conjunto de identificadores únicos
    """
    if not os.path.exists(txt_path):
        print(f"Error: El archivo {txt_path} no existe.")
        sys.exit(1)
    
    try:
        with open(txt_path, 'r') as f:
            t_ids = {line.strip() for line in f if line.strip().isdigit()}
        return t_ids
    except Exception as e:
        print(f"Error al leer el archivo {txt_path}: {e}")
        sys.exit(1)

def obtener_tablas_relacionadas(conn, tabla_objetivo, clave_primaria):
    """
    Obtiene las tablas que tienen claves foráneas referenciando la tabla objetivo.
    :param conn: Conexión a la base de datos
    :param tabla_objetivo: Nombre de la tabla principal
    :param clave_primaria: Nombre del campo clave primaria en la tabla principal
    :return: Diccionario con tablas relacionadas y su respectiva clave foránea
    """
    try:
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
    except sqlite3.Error as e:
        print(f"Error al obtener relaciones de claves foráneas: {e}")
        sys.exit(1)

def eliminar_registros(conn, tabla_objetivo, t_ids, relaciones):
    """
    Elimina los registros especificados de la tabla objetivo y sus referencias en tablas relacionadas.
    :param conn: Conexión a la base de datos
    :param tabla_objetivo: Nombre de la tabla principal
    :param t_ids: Conjunto de identificadores a eliminar
    :param relaciones: Diccionario con tablas relacionadas y su clave foránea
    :return: Conjuntos de registros inexistentes y eliminados
    """
    cursor = conn.cursor()
    registros_inexistentes = set()
    registros_eliminados = set()
    
    for t_id in t_ids:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tabla_objetivo} WHERE T_Id = ?", (t_id,))
            if cursor.fetchone()[0] == 0:
                registros_inexistentes.add(t_id)
                continue
            
            for tabla, columna in relaciones.items():
                cursor.execute(f"DELETE FROM {tabla} WHERE {columna} = ?", (t_id,))
            
            cursor.execute(f"DELETE FROM {tabla_objetivo} WHERE T_Id = ?", (t_id,))
            registros_eliminados.add(t_id)
        except sqlite3.Error as e:
            print(f"Error al eliminar el registro {t_id}: {e}")
    
    conn.commit()
    return registros_inexistentes, registros_eliminados

def escribir_reporte(reporte_path, total_inicial, registros_inexistentes, registros_eliminados, total_final):
    """
    Escribe un reporte con los resultados del proceso de eliminación.
    :param reporte_path: Ruta del archivo de reporte
    :param total_inicial: Número total de registros antes de la eliminación
    :param registros_inexistentes: Conjunto de registros no encontrados
    :param registros_eliminados: Conjunto de registros eliminados
    :param total_final: Número total de registros después de la eliminación
    """
    try:
        with open(reporte_path, 'w') as f:
            f.write(f"Total de registros en la tabla antes de la eliminación: {total_inicial}\n")
            f.write(f"Total de registros eliminados: {len(registros_eliminados)}\n")
            f.write(f"Total de registros inexistentes en el .txt: {len(registros_inexistentes)}\n")
            f.write(f"Registros inexistentes: {', '.join(registros_inexistentes) if registros_inexistentes else 'Ninguno'}\n")
            f.write(f"Total de registros en la tabla después de la eliminación: {total_final}\n")
    except Exception as e:
        print(f"Error al escribir el reporte: {e}")

def obtener_ruta_reporte(reporte_path):
    """
    Verifica si el reporte_path es un directorio y genera el nombre del archivo de reporte.
    :param reporte_path: Ruta del directorio o archivo
    :return: Ruta del archivo de reporte
    """
    if os.path.isdir(reporte_path):
        return os.path.join(reporte_path, "reporte_eliminacion.txt")
    elif reporte_path.lower().endswith(".txt"):
        return reporte_path
    else:
        print("Error: La ruta del reporte debe ser un directorio o un archivo .txt válido.")
        sys.exit(1)

def main(db_path, txt_path, reporte_path):
    """
    Función principal que coordina la eliminación de registros.
    :param db_path: Ruta del archivo de la base de datos
    :param txt_path: Ruta del archivo de identificadores a eliminar
    :param reporte_path: Ruta donde se generará el reporte
    """
    conn = conectar_gpkg(db_path)
    t_ids = leer_t_ids(txt_path)
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cca_predio")
        total_inicial = cursor.fetchone()[0]
        
        relaciones = obtener_tablas_relacionadas(conn, "cca_predio", "T_Id")
        registros_inexistentes, registros_eliminados = eliminar_registros(conn, "cca_predio", t_ids, relaciones)
        
        cursor.execute("SELECT COUNT(*) FROM cca_predio")
        total_final = cursor.fetchone()[0]
    except sqlite3.Error as e:
        print(f"Error durante el proceso: {e}")
        conn.close()
        sys.exit(1)
    
    reporte_archivo = obtener_ruta_reporte(reporte_path)
    escribir_reporte(reporte_archivo, total_inicial, registros_inexistentes, registros_eliminados, total_final)
    
    conn.close()
    print(f"Proceso completado. Reporte generado en {reporte_archivo}")

if __name__ == "__main__":
    """
    Variables a modificar, para el óptimo funcionamiento de la herramienta
    Direcciones a cada uno de los archivos
    1: ubicación completa del .gpkg
    2: ubicación completa de la lista de registros de  predio junto con sus relacionados a eliminar .txt
    3: ubicación de carpeta dónde se generará el reporte de la ejecución del script.
    """
    db_path = r"C:\ACC\CONSOLIDACION_MANZANAS\LIMPIEZA_GPKG_RURAL_10022025\consolidado_captura_campo_20250206.gpkg"
    txt_path = r"C:\ACC\CONSOLIDACION_MANZANAS\LIMPIEZA_GPKG_RURAL_10022025\predios_eliminar.txt"
    reporte_path = r"C:\ACC\CONSOLIDACION_MANZANAS\LIMPIEZA_GPKG_RURAL_10022025"  # Carpeta donde se guardará el reporte

    main(db_path, txt_path, reporte_path)