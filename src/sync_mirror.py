
import pandas as pd
import mysql.connector
from sqlalchemy import create_engine
import streamlit as st
from urllib.parse import quote_plus

class MirrorSync:
    def __init__(self, cloud_config, local_config):
        self.cloud_config = cloud_config
        self.local_config = local_config
        
    def run_sync(self):
        """Ejecuta la sincronización de Nube a Local"""
        try:
            # 1. Crear motores de SQLAlchemy para facilitar el paso de DataFrames
            # Cloud
            user_c = quote_plus(str(self.cloud_config['user']))
            pass_c = quote_plus(str(self.cloud_config['password']))
            cloud_url = f"mysql+mysqlconnector://{user_c}:{pass_c}@{self.cloud_config['host']}:{self.cloud_config['port']}/{self.cloud_config['database']}"
            cloud_engine = create_engine(cloud_url)
            
            # Local
            user_l = quote_plus(str(self.local_config['user']))
            pass_l = quote_plus(str(self.local_config['password']))
            local_url = f"mysql+mysqlconnector://{user_l}:{pass_l}@{self.local_config['host']}:{self.local_config['port']}/{self.local_config['database']}"
            local_engine = create_engine(local_url)
            
            tables = ["usuarios", "materiales", "ventas", "ventas_detalle", "log_actividad"]
            results = {}
            
            # 2. Conexión para comandos directos (Truncate)
            local_conn_raw = mysql.connector.connect(**self.local_config)
            cursor_local = local_conn_raw.cursor()
            
            cursor_local.execute("SET FOREIGN_KEY_CHECKS = 0;")
            
            for table in tables:
                print(f"Sincronizando tabla: {table}...")
                # Leer de Nube
                df = pd.read_sql(f"SELECT * FROM {table}", cloud_engine)
                
                # Limpiar Local
                cursor_local.execute(f"TRUNCATE TABLE {table}")
                
                # Insertar en Local
                if not df.empty:
                    df.to_sql(table, local_engine, if_exists='append', index=False)
                
                results[table] = len(df)
            
            cursor_local.execute("SET FOREIGN_KEY_CHECKS = 1;")
            local_conn_raw.commit()
            local_conn_raw.close()
            
            return True, results
            
        except Exception as e:
            return False, str(e)

if __name__ == "__main__":
    # Prueba rápida si se ejecuta solo (usando un entorno simulado o manual)
    print("Este script está diseñado para ser llamado desde la App o ejecutado con credenciales cargadas.")
