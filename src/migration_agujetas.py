
import pandas as pd
import mysql.connector
from mysql.connector import Error
import os
import uuid

# Credenciales Clever Cloud (tomadas de cloud_migration.py / CREDENCIALES_ACCESO.md)
db_config = {
    'host': 'bj6praqdpuirvzoqna22-mysql.services.clever-cloud.com',
    'database': 'bj6praqdpuirvzoqna22',
    'user': 'uefcnqzqensby1sf',
    'password': 'OvHa0yP4p1XVa4aUCEXt',
    'port': 3306
}

def get_clean_float(val):
    try:
        if pd.isna(val): return 0.0
        return float(val)
    except: return 0.0

def get_clean_str(val, default="", max_len=None):
    if pd.isna(val): res = default
    else: res = str(val).strip()
    if max_len: return res[:max_len]
    return res

def migrate_agujetas():
    excel_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'Agujetas.xlsx')
    
    try:
        print("🔗 Conectando a Clever Cloud...")
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        print(f"📂 Leyendo Excel: {excel_path}...")
        # Basado en la inspección: Hoja1
        df = pd.read_excel(excel_path, sheet_name='Hoja1')
        
        # Limpiar nombres de columnas (quitar espacios al final)
        df.columns = [c.strip() for c in df.columns]
        
        total = 0
        sheet_name = "Agujetas" # El usuario pidió este nombre exacto
        
        print(f"⌛ Procesando {len(df)} registros...")
        
        for _, row in df.iterrows():
            material = row.get('MATERIAL')
            if pd.isna(material) or str(material).strip() == "":
                continue
                
            marca = get_clean_str(row.get('MARCA'))
            descripcion = f"{get_clean_str(material)} {marca}".strip()
            
            # Mapeo según el esquema detectado
            # 'MATERIAL', 'MARCA', 'CODIGO', 'MEDIDA', 'COLOR', 'CANTIDAD', 'Costo ', ' Importe '
            
            codigo = get_clean_str(row.get('CODIGO'), uuid.uuid4().hex[:6])
            medida = get_clean_str(row.get('MEDIDA'))
            color = get_clean_str(row.get('COLOR'))
            cantidad = get_clean_float(row.get('CANTIDAD'))
            costo = get_clean_float(row.get('Costo'))
            
            cursor.execute(
                """INSERT INTO materiales 
                   (codigo_interno, descripcion, categoria_hoja, cantidad_actual, unidad_medida, precio_unitario, color, medida, marca) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (codigo, descripcion, sheet_name, cantidad, 'Pares', costo, color, medida, marca)
            )
            total += 1

        conn.commit()
        print(f"✅ MIGRACIÓN EXITOSA: {total} registros subidos a 'materiales' con categoría '{sheet_name}'.")
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            print("🔌 Conexión cerrada.")

if __name__ == "__main__":
    migrate_agujetas()
