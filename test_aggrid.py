import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import pandas as pd
import numpy as np
import pyarrow as pa

# Generate dummy data
df = pd.DataFrame({
    'col_str': ['a', 'b', 'c', 'd', 'e'],
    'col_num': [1, 2, 3, 4, 5]
})

st.write("Using standard object type (causes LargeUtf8 on PyArrow >=15)")
try:
    AgGrid(df, key="ag1")
except Exception as e:
    st.error(f"Error: {e}")

st.write("Using Category workaround:")
df2 = df.copy()
for col in df2.select_dtypes(include=['object']).columns:
    df2[col] = df2[col].astype('category')

try:
    AgGrid(df2, key="ag2")
except Exception as e:
    st.error(f"Error: {e}")

st.write("Current pyarrow version:", pa.__version__)
