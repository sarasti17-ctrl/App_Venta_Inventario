import streamlit as st
import mysql.connector

def verificar_migracion():
    try:
        config = st.secrets['mysql']
        conn = mysql.connector.connect(
            host=config['host'], 
            port=config['port'], 
            user=config['user'], 
            password=config['password'], 
            database=config['database']
        )
        cursor = conn.cursor()
        
        print("Resumen de materiales por categoría:")
        cursor.execute("SELECT categoria_hoja, COUNT(*) FROM materiales GROUP BY categoria_hoja")
        for row in cursor.fetchall():
            print(f" - {row[0]}: {row[1]}")
            
        print("\nPrimeros 5 registros:")
        cursor.execute("SELECT codigo_interno, descripcion, cantidad_actual, unidad_medida FROM materiales LIMIT 5")
        for row in cursor.fetchall():
            print(f" - [{row[0]}] {row[1]} | {row[2]} {row[3]}")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verificar_migracion()
