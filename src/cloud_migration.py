
import pandas as pd
import mysql.connector
from mysql.connector import Error
import os
import uuid

# Credenciales Clever Cloud proporcionadas por el usuario
db_config = {
    'host': 'bj6praqdpuirvzoqna22-mysql.services.clever-cloud.com',
    'database': 'bj6praqdpuirvzoqna22',
    'user': 'uefcnqzqensby1sf',
    'password': 'OvHa0yP4p1XVa4aUCEXt',
    'port': 3306
}

def clean_val(val):
    if pd.isna(val): return None
    return val

def subu_migracion():
    excel_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'Inv_Dic_2025.xlsx')
    sql_path = os.path.join(os.path.dirname(__file__), 'cloud_setup.sql')
    
    try:
        print("🔗 Conectando a Clever Cloud...")
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        print("📝 Aplicando esquema...")
        if os.path.exists(sql_path):
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
                for statement in sql_content.split(';'):
                    if statement.strip():
                        cursor.execute(statement)
            conn.commit()
            print("✅ Esquema aplicado.")

        print("📂 Leyendo Excel...")
        excel_file = pd.ExcelFile(excel_path)
        total = 0

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

        for sheet in excel_file.sheet_names:
            print(f"⌛ {sheet}...")
            try:
                if sheet == "Inv_TelaVirgenMov":
                    df = pd.read_excel(excel_file, sheet)
                    for _, row in df.iterrows():
                        if pd.isna(row.get('DESCRIPCIÓN')): continue
                        cursor.execute(
                            "INSERT INTO materiales (codigo_interno, descripcion, categoria_hoja, cantidad_actual, unidad_medida, precio_unitario) VALUES (%s, %s, %s, %s, %s, %s)",
                            (get_clean_str(row.get('CÓDIGO'), uuid.uuid4().hex[:6]), get_clean_str(row.get('DESCRIPCIÓN')), sheet, get_clean_float(row.get('METROS')), 'Metros', get_clean_float(row.get('PRECIO\nX\nMETRO')))
                        )
                        total += 1
                elif sheet == "Hulera":
                    df = pd.read_excel(excel_file, sheet, skiprows=1)
                    for _, row in df.iterrows():
                        desc = row.iloc[0]
                        if pd.isna(desc) or str(desc).strip() in ["Materiales", ""]: continue
                        cursor.execute(
                            "INSERT INTO materiales (codigo_interno, descripcion, categoria_hoja, cantidad_actual, unidad_medida, precio_unitario) VALUES (%s, %s, %s, %s, %s, %s)",
                            (f"HUL-{uuid.uuid4().hex[:6]}", get_clean_str(desc), sheet, get_clean_float(row.iloc[2]), 'Kg', get_clean_float(row.iloc[3]))
                        )
                        total += 1
                elif sheet == "Caja Individual":
                    df = pd.read_excel(excel_file, sheet)
                    for _, row in df.iterrows():
                        if pd.isna(row.get('MARCA')): continue
                        cursor.execute(
                            "INSERT INTO materiales (codigo_interno, descripcion, categoria_hoja, cantidad_actual, unidad_medida, precio_unitario) VALUES (%s, %s, %s, %s, %s, %s)",
                            (get_clean_str(row.get('CODIGO'), f"CJ-{uuid.uuid4().hex[:6]}"), f"Caja {row.get('MARCA')}", sheet, get_clean_float(row.get('INV\nREAL')), 'Piezas', get_clean_float(row.get('Costo \nUnitario')))
                        )
                        total += 1
                elif sheet == "Inv_TelaVirgen_SinMov":
                    df = pd.read_excel(excel_file, sheet, skiprows=1)
                    for _, row in df.iterrows():
                        if pd.isna(row.get('DESCRIPCIÓN')): continue
                        cursor.execute(
                            "INSERT INTO materiales (codigo_interno, descripcion, categoria_hoja, propiedad, cantidad_actual, unidad_medida, precio_unitario) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (get_clean_str(row.get('CÓDIGO'), uuid.uuid4().hex[:6]), get_clean_str(row.get('DESCRIPCIÓN')), sheet, 'Sin Movimiento', get_clean_float(row.get('METROS\nFISCAL')), 'Metros', get_clean_float(row.get('PRECIO\nX\nMETROS')))
                        )
                        total += 1
                elif sheet == "TelaNoUtilizable":
                    df = pd.read_excel(excel_file, sheet)
                    for _, row in df.iterrows():
                        if pd.isna(row.get('DESCRIPCIÓN')): continue
                        cursor.execute(
                            "INSERT INTO materiales (codigo_interno, descripcion, categoria_hoja, propiedad, cantidad_actual, unidad_medida, precio_unitario) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (get_clean_str(row.get('CÓDIGO'), uuid.uuid4().hex[:6]), get_clean_str(row.get('DESCRIPCIÓN')), sheet, 'No Utilizable', get_clean_float(row.get('METROS')), 'Metros', get_clean_float(row.get('PRECIO\nX\nMETROS')))
                        )
                        total += 1
                elif sheet == "Agujeta":
                    df = pd.read_excel(excel_file, sheet)
                    for _, row in df.iterrows():
                        if pd.isna(row.get('MATERIAL')): continue
                        cursor.execute(
                            "INSERT INTO materiales (codigo_interno, descripcion, categoria_hoja, cantidad_actual, unidad_medida, precio_unitario) VALUES (%s, %s, %s, %s, %s, %s)",
                            (get_clean_str(row.get('CODIGO'), uuid.uuid4().hex[:6]), get_clean_str(row.get('MATERIAL')), sheet, get_clean_float(row.get('CANTIDAD\nREAL')), 'Pares', get_clean_float(row.get('Costo')))
                        )
                        total += 1
                elif sheet == "Suela Mov":
                    df = pd.read_excel(excel_file, sheet, skiprows=1)
                    for _, row in df.iterrows():
                        estilo = row.iloc[0]
                        if pd.isna(estilo) or str(estilo).strip() in ["ESTILO", ""]: continue
                        cursor.execute(
                            "INSERT INTO materiales (codigo_interno, descripcion, categoria_hoja, cantidad_actual, unidad_medida, color, medida) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (f"SUE-{uuid.uuid4().hex[:6]}", f"Suela {estilo}", sheet, get_clean_float(row.iloc[3]), 'Pares', get_clean_str(row.iloc[1]), get_clean_str(row.iloc[2]))
                        )
                        total += 1
                # ... Etiquetas ya está abajo ...
                elif sheet == "carga hule":
                    df = pd.read_excel(excel_file, sheet)
                    for _, row in df.iterrows():
                        mat = row.get('MATERIAL')
                        if pd.isna(mat) or str(mat).strip() in ["", "MATERIAL"]: continue
                        cursor.execute(
                            "INSERT INTO materiales (codigo_interno, descripcion, categoria_hoja, cantidad_actual, unidad_medida, color) VALUES (%s, %s, %s, %s, %s, %s)",
                            (f"CH-{uuid.uuid4().hex[:6]}", f"{mat}", sheet, get_clean_float(row.iloc[2]), 'Kg', get_clean_str(row.get('COLOR')))
                        )
                        total += 1
                elif sheet == "Almacén_MateriaPrima":
                    df = pd.read_excel(excel_file, sheet, skiprows=1)
                    for _, row in df.iterrows():
                        inv = row.iloc[0]
                        if pd.isna(inv) or str(inv).strip() in ["", "INVENTARIO"]: continue
                        cursor.execute(
                            "INSERT INTO materiales (codigo_interno, descripcion, categoria_hoja, cantidad_actual, unidad_medida, precio_unitario) VALUES (%s, %s, %s, %s, %s, %s)",
                            (f"AMP-{uuid.uuid4().hex[:6]}", str(inv), sheet, get_clean_float(row.iloc[1]), get_clean_str(row.iloc[3], "Pzas", max_len=20), get_clean_float(row.iloc[2]))
                        )
                        total += 1
                elif sheet == "Caja_Embarque":
                    df = pd.read_excel(excel_file, sheet, skiprows=2)
                    for _, row in df.iterrows():
                        caja = row.iloc[2]
                        if pd.isna(caja) or str(caja).strip() in ["", "CAJA"]: continue
                        cursor.execute(
                            "INSERT INTO materiales (codigo_interno, descripcion, categoria_hoja, cantidad_actual, unidad_medida, precio_unitario) VALUES (%s, %s, %s, %s, %s, %s)",
                            (get_clean_str(row.iloc[0], f"CJE-{uuid.uuid4().hex[:6]}"), f"Caja {caja}", sheet, get_clean_float(row.iloc[6]), 'Piezas', get_clean_float(row.iloc[4]))
                        )
                        total += 1
            except Exception as e_sheet:
                print(f"❌ Error en {sheet}: {e_sheet}")
        
        conn.commit()
        print(f"🚀 MIGRACIÓN EXITOSA: {total} registros en la nube.")
    except Exception as e:
        print(f"❌ Error critico: {e}")
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    subu_migracion()
