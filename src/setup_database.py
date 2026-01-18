"""
Script para crear la base de datos y las tablas del sistema de liquidación
Ejecuta el archivo database_schema.sql en el servidor MySQL
"""

import mysql.connector
from mysql.connector import Error
import streamlit as st
import os


def crear_base_datos():
    """
    Crea la base de datos y todas las tablas necesarias
    """
    try:
        # Leer credenciales desde secrets.toml
        config = {
            'host': st.secrets["mysql"]["host"],
            'port': st.secrets["mysql"]["port"],
            'user': st.secrets["mysql"]["user"],
            'password': st.secrets["mysql"]["password"]
        }
        
        print(f"🔌 Conectando a MySQL en {config['host']}:{config['port']}...")
        
        # Conectar sin especificar base de datos (para crearla)
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():
            cursor = connection.cursor()
            print("✅ Conexión exitosa al servidor MySQL")
            
            # Leer el archivo SQL
            sql_file_path = os.path.join(
                os.path.dirname(__file__), 
                '..', 
                'database_schema.sql'
            )
            
            print(f"📄 Leyendo archivo SQL: {sql_file_path}")
            
            with open(sql_file_path, 'r', encoding='utf-8') as file:
                sql_script = file.read()
            
            # Dividir el script en comandos individuales
            # Nota: Esto es una simplificación, los procedimientos almacenados
            # requieren manejo especial del delimitador
            comandos = []
            comando_actual = []
            en_procedimiento = False
            
            for linea in sql_script.split('\n'):
                linea_limpia = linea.strip()
                
                # Detectar inicio de procedimiento
                if 'DELIMITER //' in linea_limpia:
                    en_procedimiento = True
                    continue
                
                # Detectar fin de procedimiento
                if 'DELIMITER ;' in linea_limpia:
                    en_procedimiento = False
                    if comando_actual:
                        comandos.append('\n'.join(comando_actual))
                        comando_actual = []
                    continue
                
                # Saltar comentarios y líneas vacías
                if linea_limpia.startswith('--') or not linea_limpia:
                    continue
                
                comando_actual.append(linea)
                
                # Si no estamos en un procedimiento, dividir por punto y coma
                if not en_procedimiento and linea_limpia.endswith(';'):
                    comandos.append('\n'.join(comando_actual))
                    comando_actual = []
            
            # Agregar el último comando si existe
            if comando_actual:
                comandos.append('\n'.join(comando_actual))
            
            print(f"📋 Ejecutando {len(comandos)} comandos SQL...")
            
            # Ejecutar cada comando
            errores = 0
            for i, comando in enumerate(comandos, 1):
                comando = comando.strip()
                if comando:
                    try:
                        # Ejecutar el comando
                        cursor.execute(comando)
                        
                        # Intentar obtener resultados si los hay
                        try:
                            if cursor.with_rows:
                                rows = cursor.fetchall()
                                for row in rows:
                                    print(f"   {row}")
                        except:
                            pass  # No hay resultados, está bien
                        
                        if i % 5 == 0:
                            print(f"   ✓ Ejecutados {i}/{len(comandos)} comandos")
                    
                    except Error as e:
                        # Algunos errores son esperados (como tablas que ya existen)
                        error_msg = str(e)
                        if "already exists" not in error_msg and "Unknown database" not in error_msg:
                            print(f"   ⚠️  Error en comando {i}: {e}")
                            # No contar como error si es algo esperado
                            if "Duplicate" not in error_msg:
                                errores += 1
            
            connection.commit()
            
            if errores == 0:
                print("\n" + "="*60)
                print("✅ BASE DE DATOS CREADA EXITOSAMENTE")
                print("="*60)
                print("\n📊 Tablas creadas:")
                print("   • usuarios")
                print("   • materiales")
                print("   • ventas")
                print("   • log_actividad")
                print("\n👁️  Vistas creadas:")
                print("   • v_inventario_disponible")
                print("   • v_ventas_por_vendedor")
                print("   • v_progreso_liquidacion")
                print("\n⚙️  Procedimientos almacenados:")
                print("   • sp_registrar_venta")
                print("\n👤 Usuarios por defecto:")
                print("   • admin / admin123 (ROL: ADMIN)")
                print("   • vendedor1 / vendedor123 (ROL: VENDEDOR)")
                print("\n⚠️  IMPORTANTE: Cambia las contraseñas después del primer login")
                print("="*60)
            else:
                print(f"\n⚠️  Completado con {errores} errores")
            
            return True
            
    except Error as e:
        print(f"\n❌ Error de MySQL: {e}")
        return False
    
    except FileNotFoundError:
        print(f"\n❌ No se encontró el archivo database_schema.sql")
        return False
    
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        return False
    
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("\n🔌 Conexión cerrada")


def verificar_base_datos():
    """
    Verifica que la base de datos y las tablas existan
    """
    try:
        config = {
            'host': st.secrets["mysql"]["host"],
            'port': st.secrets["mysql"]["port"],
            'user': st.secrets["mysql"]["user"],
            'password': st.secrets["mysql"]["password"],
            'database': st.secrets["mysql"]["database"]
        }
        
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Verificar tablas
            cursor.execute("SHOW TABLES")
            tablas = [tabla[0] for tabla in cursor.fetchall()]
            
            print("\n📊 Tablas encontradas:")
            for tabla in tablas:
                cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                count = cursor.fetchone()[0]
                print(f"   • {tabla}: {count} registros")
            
            cursor.close()
            connection.close()
            
            return True
    
    except Error as e:
        print(f"❌ Error al verificar base de datos: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🗄️  CONFIGURACIÓN DE BASE DE DATOS")
    print("    Sistema de Liquidación de Inventario")
    print("="*60 + "\n")
    
    # Crear la base de datos
    if crear_base_datos():
        print("\n🔍 Verificando instalación...")
        verificar_base_datos()
    else:
        print("\n❌ La creación de la base de datos falló")
        print("   Verifica las credenciales en .streamlit/secrets.toml")
