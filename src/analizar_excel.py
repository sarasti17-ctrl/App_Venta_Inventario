import pandas as pd
import os
import sys

def analizar_excel():
    """
    Analiza el archivo Excel y muestra su estructura y guarda en un archivo
    """
    excel_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'data',
        'Inv_Dic_2025.xlsx'
    )
    
    output_path = os.path.join(
        os.path.dirname(__file__),
        'analisis_excel_completo.txt'
    )
    
    try:
        # Abrir archivo para escribir el reporte
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("ANALISIS DEL ARCHIVO DE INVENTARIO\n")
            f.write("="*70 + "\n")
            f.write(f"\nArchivo: {excel_path}\n\n")
            
            # Leer el archivo Excel
            excel_file = pd.ExcelFile(excel_path)
            
            f.write(f"Total de hojas: {len(excel_file.sheet_names)}\n\n")
            
            # Analizar cada hoja
            for i, sheet_name in enumerate(excel_file.sheet_names, 1):
                try:
                    f.write("\n" + "="*70 + "\n")
                    f.write(f"Hoja {i}: {sheet_name}\n")
                    f.write("="*70 + "\n")
                    
                    # Leer la hoja
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    
                    f.write(f"Dimensiones: {df.shape[0]} filas x {df.shape[1]} columnas\n")
                    f.write(f"\nColumnas encontradas:\n")
                    
                    for j, col in enumerate(df.columns, 1):
                        # Contar valores no nulos
                        non_null = df[col].notna().sum()
                        null_count = df[col].isna().sum()
                        
                        # Tipo de datos
                        dtype = df[col].dtype
                        
                        # Muestra de valores únicos (primeros 3)
                        sample_values = df[col].dropna().unique()[:3]
                        sample_str = ", ".join([str(v)[:30] for v in sample_values])
                        
                        # Convertir col a string
                        col_str = str(col)
                        
                        f.write(f"   {j:2d}. {col_str:30s} | Tipo: {str(dtype):10s} | "
                              f"Llenos: {non_null:5d} | Vacios: {null_count:5d}\n")
                        
                        if len(sample_str) > 0:
                            f.write(f"       Ejemplos: {sample_str}\n")
                    
                    # Mostrar primeras 3 filas como ejemplo
                    f.write(f"\nPrimeras 3 filas de ejemplo:\n")
                    f.write("-" * 70 + "\n")
                    f.write(df.head(3).to_string() + "\n")
                        
                except Exception as sheet_err:
                    f.write(f"Error procesando hoja {sheet_name}: {sheet_err}\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("Analisis completado\n")
            f.write("="*70 + "\n")
            
        print(f"Análisis completado. Resultados guardados en: {output_path}")
        
    except Exception as e:
        print(f"\nError al abrir el archivo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analizar_excel()
