
import mysql.connector
import os

db_config = {
    'host': 'bj6praqdpuirvzoqna22-mysql.services.clever-cloud.com',
    'database': 'bj6praqdpuirvzoqna22',
    'user': 'uefcnqzqensby1sf',
    'password': 'OvHa0yP4p1XVa4aUCEXt',
    'port': 3306
}

def verify():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM materiales WHERE categoria_hoja = 'Agujetas'")
        count = cursor.fetchone()[0]
        print(f"📊 Registros encontrados con categoría 'Agujetas': {count}")
        
        cursor.execute("SELECT descripcion, cantidad_actual, precio_unitario FROM materiales WHERE categoria_hoja = 'Agujetas' LIMIT 5")
        rows = cursor.fetchall()
        print("\n--- Muestra de datos ---")
        for row in rows:
            print(f"Desc: {row[0]}, Cant: {row[1]}, Precio: {row[2]}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    verify()
