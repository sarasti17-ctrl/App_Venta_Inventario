"""
Script de migración de datos para el Sistema de Liquidación
Carga datos desde Inv_Dic_2025.xlsx hacia la base de datos MySQL
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error
import streamlit as st
import os
import uuid

def conectar_db():
    """Establece conexión con la base de datos usando secrets de Streamlit"""
    try:
        config = {
            'host': st.secrets["mysql"]["host"],
            'port': st.secrets["mysql"]["port"],
            'user': st.secrets["mysql"]["user"],
            'password': st.secrets["mysql"]["password"],
            'database': st.secrets["mysql"]["database"]
        }
        conn = mysql.connector.connect(**config)
        return conn
    except Error as e:
        print(f"Error conectando a MySQL: {e}")
        return None

def estandarizar_unidad(unidad):
    """Normaliza las unidades de medida"""
    if pd.isna(unidad) or str(unidad).strip() == "":
        return "Piezas"
    
    u = str(unidad).lower().strip()
    if u in ['kg', 'kgs', 'kilogramos', 'kilo']:
        return "Kg"
    if u in ['metros', 'm', 'mts', 'metro']:
        return "Metros"
    if u in ['pares', 'par', 'prs']:
        return "Pares"
    if u in ['piezas', 'pza', 'pzas', 'pz', 'unidades', 'millar']:
        return "Piezas"
    if u in ['litros', 'l', 'lts']:
        return "Litros"
    if u in ['rollos', 'rollo']:
        return "Rollos"
    if u in ['cajas', 'caja']:
        return "Cajas"
    
    return unidad.capitalize()

def clean_val(val):
    """Convierte NaN de pandas a None para MySQL (NULL)"""
    if pd.isna(val):
        return None
    return val

def migrar_datos():
    """Función principal de migración"""
    excel_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'Inv_Dic_2025.xlsx')
    
    if not os.path.exists(excel_path):
        print(f"Error: No se encuentra el archivo {excel_path}")
        return

    conn = conectar_db()
    if not conn:
        return
    
    cursor = conn.cursor()

    try:
        excel_file = pd.ExcelFile(excel_path)
        total_migrados = 0
        
        # 1. Hoja: Inv_TelaVirgenMov
        if "Inv_TelaVirgenMov" in excel_file.sheet_names:
            print("Procesando Inv_TelaVirgenMov...")
            df = pd.read_excel(excel_file, "Inv_TelaVirgenMov")
            for _, row in df.iterrows():
                if pd.isna(row.get('DESCRIPCIÓN')): continue
                
                codigo = str(row.get('CÓDIGO')) if not pd.isna(row.get('CÓDIGO')) else f"TEL-{uuid.uuid4().hex[:6]}"
                
                sql = "INSERT IGNORE INTO materiales (codigo_interno, descripcion, categoria_hoja, propiedad, cantidad_actual, unidad_medida, precio_unitario) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                values = (
                    codigo,
                    clean_val(row.get('DESCRIPCIÓN')),
                    'Inv_TelaVirgenMov',
                    'Virgen',
                    float(row.get('METROS', 0)) if not pd.isna(row.get('METROS')) else 0,
                    'Metros',
                    float(row.get('PRECIO\nX\nMETRO', 0)) if not pd.isna(row.get('PRECIO\nX\nMETRO')) else 0
                )
                cursor.execute(sql, values)
                total_migrados += cursor.rowcount

        # 2. Hoja: Inv_TelaVirgen_SinMov
        if "Inv_TelaVirgen_SinMov" in excel_file.sheet_names:
            print("Procesando Inv_TelaVirgen_SinMov...")
            df = pd.read_excel(excel_file, "Inv_TelaVirgen_SinMov") # Eliminar skiprows=1
            for _, row in df.iterrows():
                if pd.isna(row.get('DESCRIPCIÓN')): continue
                
                codigo = str(row.get('CÓDIGO')) if not pd.isna(row.get('CÓDIGO')) else f"TEL-SM-{uuid.uuid4().hex[:6]}"
                
                sql = "INSERT IGNORE INTO materiales (codigo_interno, descripcion, categoria_hoja, propiedad, cantidad_actual, unidad_medida, precio_unitario, observaciones) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                values = (
                    codigo,
                    clean_val(row.get('DESCRIPCIÓN')),
                    'Inv_TelaVirgen_SinMov',
                    'Sin Movimiento',
                    float(row.get('METROS\nFISCAL', 0)) if not pd.isna(row.get('METROS\nFISCAL')) else 0,
                    'Metros',
                    float(row.get('PRECIO\nX\nMETROS', 0)) if not pd.isna(row.get('PRECIO\nX\nMETROS')) else 0,
                    clean_val(row.get('OBS'))
                )
                cursor.execute(sql, values)
                total_migrados += cursor.rowcount

        # 3. Hoja: TelaNoUtilizable
        if "TelaNoUtilizable" in excel_file.sheet_names:
            print("Procesando TelaNoUtilizable...")
            df = pd.read_excel(excel_file, "TelaNoUtilizable")
            for _, row in df.iterrows():
                if pd.isna(row.get('DESCRIPCIÓN')): continue
                
                codigo = str(row.get('CÓDIGO'))
                if codigo == '*' or pd.isna(codigo) or codigo == 'nan':
                    codigo = f"TNU-{uuid.uuid4().hex[:6]}"
                
                sql = "INSERT IGNORE INTO materiales (codigo_interno, descripcion, categoria_hoja, propiedad, cantidad_actual, unidad_medida, precio_unitario, observaciones) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                values = (
                    codigo,
                    clean_val(row.get('DESCRIPCIÓN')),
                    'TelaNoUtilizable',
                    'No Utilizable',
                    float(row.get('METROS', 0)) if not pd.isna(row.get('METROS')) else 0,
                    'Metros',
                    float(row.get('PRECIO\nX\nMETROS', 0)) if not pd.isna(row.get('PRECIO\nX\nMETROS')) else 0,
                    clean_val(row.get('Obervaciones'))
                )
                cursor.execute(sql, values)
                total_migrados += cursor.rowcount

        # 4. Hoja: Hulera
        if "Hulera" in excel_file.sheet_names:
            print("Procesando Hulera...")
            df = pd.read_excel(excel_file, "Hulera", skiprows=1)
            for _, row in df.iterrows():
                # El análisis mostró que Hulera usa Unnamed cols después del skip
                desc = row.iloc[0] # Materiales
                if pd.isna(desc) or str(desc).strip() == "Materiales" or str(desc).strip() == "": continue
                
                prop = row.iloc[1] # Nombre simple
                cant = row.iloc[2] # Cantidad
                prec = row.iloc[3] # Costo
                unid = row.iloc[4] # Unidad
                obs = row.iloc[6]  # Observaciones
                prov = row.iloc[8] # Proveedor
                
                codigo = f"HUL-{uuid.uuid4().hex[:6]}"
                
                sql = "INSERT IGNORE INTO materiales (codigo_interno, descripcion, categoria_hoja, propiedad, cantidad_actual, unidad_medida, precio_unitario, observaciones, proveedor) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                values = (
                    codigo,
                    clean_val(desc),
                    'Hulera',
                    clean_val(prop),
                    float(cant) if not pd.isna(cant) else 0,
                    estandarizar_unidad(unid),
                    float(prec) if not pd.isna(prec) else 0,
                    clean_val(obs),
                    clean_val(prov)
                )
                cursor.execute(sql, values)
                total_migrados += cursor.rowcount

        # 5. Hoja: Caja Individual
        if "Caja Individual" in excel_file.sheet_names:
            print("Procesando Caja Individual...")
            df = pd.read_excel(excel_file, "Caja Individual")
            for _, row in df.iterrows():
                if pd.isna(row.get('MARCA')): continue
                
                codigo = str(row.get('CODIGO')) if not pd.isna(row.get('CODIGO')) else f"CJ-{uuid.uuid4().hex[:6]}"
                if codigo == 'nan': codigo = f"CJ-{uuid.uuid4().hex[:6]}"
                
                sql = "INSERT IGNORE INTO materiales (codigo_interno, descripcion, categoria_hoja, cantidad_actual, unidad_medida, precio_unitario, marca, medida, observaciones) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                values = (
                    codigo,
                    f"Caja Individual {clean_val(row.get('MARCA'))}",
                    'Caja Individual',
                    float(row.get('CANTIDAD', 0)) if not pd.isna(row.get('CANTIDAD')) else 0,
                    'Piezas',
                    float(row.get('Costo \nUnitario', 0)) if not pd.isna(row.get('Costo \nUnitario')) else 0,
                    clean_val(row.get('MARCA')),
                    clean_val(row.get('MEDIDA')),
                    clean_val(row.get('OBS'))
                )
                cursor.execute(sql, values)
                total_migrados += cursor.rowcount

        # 6. Hoja: Agujeta
        if "Agujeta" in excel_file.sheet_names:
            print("Procesando Agujeta...")
            df = pd.read_excel(excel_file, "Agujeta")
            for _, row in df.iterrows():
                if pd.isna(row.get('MATERIAL')): continue
                
                codigo = str(row.get('CODIGO')) if not pd.isna(row.get('CODIGO')) else f"AGU-{uuid.uuid4().hex[:6]}"
                if codigo == 'nan': codigo = f"AGU-{uuid.uuid4().hex[:6]}"
                
                sql = "INSERT IGNORE INTO materiales (codigo_interno, descripcion, categoria_hoja, cantidad_actual, unidad_medida, precio_unitario, marca, medida, color, observaciones) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                values = (
                    codigo,
                    clean_val(row.get('MATERIAL')),
                    'Agujeta',
                    float(row.get('CANTIDAD', 0)) if not pd.isna(row.get('CANTIDAD')) else 0,
                    'Pares',
                    float(row.get('Costo', 0)) if not pd.isna(row.get('Costo')) else 0,
                    clean_val(row.get('MARCA')),
                    clean_val(row.get('MEDIDA')),
                    clean_val(row.get('COLOR')),
                    clean_val(row.get('OBS'))
                )
                cursor.execute(sql, values)
                total_migrados += cursor.rowcount

        # 7. Hoja: carga hule
        if "carga hule" in excel_file.sheet_names:
            print("Procesando carga hule...")
            df = pd.read_excel(excel_file, "carga hule")
            for _, row in df.iterrows():
                mat = row.get('MATERIAL')
                if pd.isna(mat) or str(mat).strip() == "" or str(mat).strip() == "MATERIAL": continue
                
                codigo = f"CH-{uuid.uuid4().hex[:6]}"
                color = clean_val(row.get('COLOR'))
                desc = f"{mat}" + (f" - {color}" if color else "")
                
                sql = "INSERT INTO materiales (codigo_interno, descripcion, categoria_hoja, cantidad_actual, unidad_medida, color, observaciones) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                values = (
                    codigo,
                    desc,
                    'carga hule',
                    float(row.iloc[2]) if not pd.isna(row.iloc[2]) else 0,
                    'Kg',
                    color,
                    clean_val(row.get('Comentarios'))
                )
                cursor.execute(sql, values)
                total_migrados += cursor.rowcount

        # 8. Hoja: Suela Mov
        if "Suela Mov" in excel_file.sheet_names:
            print("Procesando Suela Mov...")
            df = pd.read_excel(excel_file, "Suela Mov", skiprows=1)
            for _, row in df.iterrows():
                estilo = row.iloc[0] # ESTILO
                if pd.isna(estilo) or str(estilo).strip() == "" or str(estilo).strip() == "ESTILO": continue
                
                codigo = f"SUE-{uuid.uuid4().hex[:6]}"
                color = clean_val(row.iloc[1])
                talla = clean_val(row.iloc[2])
                cant = row.iloc[3]
                
                sql = "INSERT INTO materiales (codigo_interno, descripcion, categoria_hoja, cantidad_actual, unidad_medida, color, medida) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                values = (
                    codigo,
                    f"Suela {estilo}",
                    'Suela Mov',
                    float(cant) if not pd.isna(cant) else 0,
                    'Pares',
                    color,
                    talla
                )
                cursor.execute(sql, values)
                total_migrados += cursor.rowcount

        # 9. Hoja: suela sin mov
        if "suela sin  mov" in excel_file.sheet_names:
            print("Procesando suela sin mov...")
            df = pd.read_excel(excel_file, "suela sin  mov", skiprows=2)
            for _, row in df.iterrows():
                estilo = row.iloc[1] # ESTILO (Unnamed: 1 por el skip)
                if pd.isna(estilo) or str(estilo).strip() == "" or str(estilo).strip() == "ESTILO": continue
                
                codigo = f"SUE-SM-{uuid.uuid4().hex[:6]}"
                color = clean_val(row.iloc[2])
                talla = clean_val(row.iloc[3])
                cant = row.iloc[4]
                prec = row.iloc[7]
                obs = row.iloc[9]
                
                sql = "INSERT INTO materiales (codigo_interno, descripcion, categoria_hoja, propiedad, cantidad_actual, unidad_medida, precio_unitario, color, medida, observaciones) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                values = (
                    codigo,
                    f"Suela {estilo}",
                    'suela sin mov',
                    'Sin Movimiento',
                    float(cant) if not pd.isna(cant) else 0,
                    'Pares',
                    float(prec) if not pd.isna(prec) else 0,
                    color,
                    talla,
                    clean_val(obs)
                )
                cursor.execute(sql, values)
                total_migrados += cursor.rowcount

        # 10. Hoja: Almacén_MateriaPrima
        if "Almacén_MateriaPrima" in excel_file.sheet_names:
            print("Procesando Almacén_MateriaPrima...")
            df = pd.read_excel(excel_file, "Almacén_MateriaPrima", skiprows=1)
            for _, row in df.iterrows():
                inv = row.iloc[0] # INVENTARIO
                if pd.isna(inv) or str(inv).strip() in ["", "INVENTARIO"]: continue
                
                # Mapeo Explícito según estructura confirmada:
                # [0] INVENTARIO, [1] CANTIDAD, [2] PRECIO, [3] UNIDAD, [5] OBSERVACIONES
                codigo = f"AMP-{uuid.uuid4().hex[:6]}"
                cant = row.iloc[1] 
                prec = row.iloc[2]
                unid = row.iloc[3]
                obs = row.iloc[5]
                
                sql = "INSERT INTO materiales (codigo_interno, descripcion, categoria_hoja, cantidad_actual, unidad_medida, precio_unitario, observaciones) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                values = (
                    codigo,
                    str(inv),
                    'Almacén_MateriaPrima',
                    float(cant) if not pd.isna(cant) else 0,
                    estandarizar_unidad(unid),
                    float(prec) if not pd.isna(prec) else 0,
                    clean_val(obs)
                )
                cursor.execute(sql, values)
                total_migrados += cursor.rowcount

        # 11. Hoja: Caja_Embarque
        if "Caja_Embarque" in excel_file.sheet_names:
            print("Procesando Caja_Embarque...")
            df = pd.read_excel(excel_file, "Caja_Embarque", skiprows=1)
            for _, row in df.iterrows():
                prov = row.iloc[1] # Proveedor
                caja = row.iloc[2] # CAJA
                if pd.isna(caja) or str(caja).strip() == "" or str(caja).strip() == "CAJA": continue
                
                codigo = str(row.iloc[0]) if not pd.isna(row.iloc[0]) else f"CJE-{uuid.uuid4().hex[:6]}"
                med = row.iloc[3]  # MEDIDAS
                prec = row.iloc[4] # COSTO 
                cant = row.iloc[6] # CANTIDAD
                obs = row.iloc[10] # OBS
                
                sql = "INSERT INTO materiales (codigo_interno, descripcion, categoria_hoja, cantidad_actual, unidad_medida, precio_unitario, proveedor, medida, observaciones) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                values = (
                    codigo,
                    f"Caja Embarque {caja}",
                    'Caja_Embarque',
                    float(cant) if not pd.isna(cant) else 0,
                    'Piezas',
                    float(prec) if not pd.isna(prec) else 0,
                    clean_val(prov),
                    clean_val(med),
                    clean_val(obs)
                )
                cursor.execute(sql, values)
                total_migrados += cursor.rowcount

        # 12. Hoja: Etiquetas
        if "Etiquetas" in excel_file.sheet_names:
            print("Procesando Etiquetas...")
            df = pd.read_excel(excel_file, "Etiquetas")
            for _, row in df.iterrows():
                desc = row.get('Descripción')
                if pd.isna(desc) or str(desc).strip() == "" or str(desc).strip() == "Descripción": continue
                
                codigo = str(row.get('No. Ref')) if not pd.isna(row.get('No. Ref')) else f"ETI-{uuid.uuid4().hex[:6]}"
                cant = row.get('Inventario\n19.12.25\n(pzs)')
                prec = row.get('Costo x pieza')
                obs = row.get('OBS')
                
                sql = "INSERT INTO materiales (codigo_interno, descripcion, categoria_hoja, cantidad_actual, unidad_medida, precio_unitario, observaciones) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                values = (
                    codigo,
                    str(desc),
                    'Etiquetas',
                    float(cant) if not pd.isna(cant) else 0,
                    'Piezas',
                    float(prec) if not pd.isna(prec) else 0,
                    clean_val(obs)
                )
                cursor.execute(sql, values)
                total_migrados += cursor.rowcount

        conn.commit()
        print(f"\n✅ MIGRACIÓN COMPLETADA. Total registros insertados: {total_migrados}")
        
    except Exception as e:
        print(f"Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("="*60)
    print("🚀 INICIANDO MIGRACIÓN DE DATOS")
    print("="*60)
    migrar_datos()
