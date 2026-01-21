import pandas as pd
import os

excel_path = os.path.join('s:\\', 'scripts py', 'Utilerias', '+Utilerias', 'App_Venta_Inventario', 'data', 'Inv_Dic_2025.xlsx')

if os.path.exists(excel_path):
    print(f"Leyendo: {excel_path}")
    df = pd.read_excel(excel_path, "suela sin  mov", skiprows=2)
    print("\nColumnas encontradas:")
    print(df.columns.tolist())
    print("\nPrimeras 2 filas (iloc):")
    for i in range(min(2, len(df))):
        row = df.iloc[i]
        print(f"Fila {i}:")
        for j in range(len(row)):
            print(f"  [{j}] {df.columns[j]}: {row.iloc[j]}")
else:
    print("No se encontró el archivo Excel.")
