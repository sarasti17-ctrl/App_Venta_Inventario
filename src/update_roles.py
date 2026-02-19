import streamlit as st
import mysql.connector
from mysql.connector import Error

def update_database_schema():
    if "mysql" not in st.secrets:
        print("❌ Secrets not found.")
        return

    config = st.secrets["mysql"]
    try:
        conn = mysql.connector.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            database=config["database"]
        )
        cursor = conn.cursor()
        
        print("🔧 Aplicando cambio en la columna 'rol'...")
        alter_query = "ALTER TABLE usuarios MODIFY COLUMN rol ENUM('ADMIN', 'VENDEDOR', 'CLIENTE') NOT NULL DEFAULT 'VENDEDOR';"
        cursor.execute(alter_query)
        conn.commit()
        
        print("✅ Columna 'rol' actualizada exitosamente para incluir 'CLIENTE'.")
        cursor.close()
        conn.close()
    except Error as e:
        print(f"❌ Error actualizando la base de datos: {e}")

if __name__ == "__main__":
    update_database_schema()
