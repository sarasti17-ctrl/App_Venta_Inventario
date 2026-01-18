import streamlit as st
import mysql.connector
from mysql.connector import Error

def apply_sp():
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
        
        with open('sp_registrar_venta.sql', 'r', encoding='utf-8') as f:
            sql = f.read()
            
        # Limpiar comentarios y espacios extras
        sql = "\n".join([line for line in sql.splitlines() if not line.strip().startswith('--')])
        
        # Primero el DROP
        cursor.execute("DROP PROCEDURE IF EXISTS sp_registrar_venta")
        
        # Luego el CREATE completo (sin el DROP ni comentarios)
        # Buscamos el inicio del CREATE
        create_start = sql.find("CREATE PROCEDURE")
        if create_start != -1:
            create_sql = sql[create_start:].strip()
            # Quitamos el último punto y coma si existe fuera del END
            if create_sql.endswith(';'):
                # En MariaDB/MySQL a través de conectores, el bloque BEGIN...END no debe terminar con ; extra si no hay DELIMITER
                pass 
            
            print("Executing CREATE PROCEDURE...")
            cursor.execute(create_sql)
        
        conn.commit()
        print("✅ Procedimiento sp_registrar_venta aplicado.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    apply_sp()
