import pandas as pd
import os

try:
    file_path = os.path.join('data', 'Agujetas.xlsx')
    excel = pd.ExcelFile(file_path)
    print(f"Sheets: {excel.sheet_names}")
    for sheet in excel.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet)
        print(f"\n--- Sheet: {sheet} ---")
        print(df.columns.tolist())
        print(df.head(3))
except Exception as e:
    print(f"Error: {e}")
