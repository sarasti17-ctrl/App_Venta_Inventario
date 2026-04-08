import pandas as pd
import pyarrow as pa
from streamlit.dataframe_util import convert_anything_to_df
import streamlit.type_util as type_util
import numpy as np

# Create test DataFrame
df = pd.DataFrame({'col': ['a', 'b', 'c']})

# Check original behavior
t1 = pa.Table.from_pandas(df)
print("Original Pyarrow:", t1.schema)

# Patching Pyarrow to replace LargeUtf8 with Utf8
_original_from_pandas = pa.Table.from_pandas
def _patched_from_pandas(*args, **kwargs):
    table = _original_from_pandas(*args, **kwargs)
    schema = table.schema
    new_schema = []
    for field in schema:
        if field.type == pa.large_string():
            new_schema.append(pa.field(field.name, pa.string(), nullable=field.nullable))
        else:
            new_schema.append(field)
    return table.cast(pa.schema(new_schema))

pa.Table.from_pandas = _patched_from_pandas

t2 = pa.Table.from_pandas(df)
print("Patched Pyarrow:", t2.schema)
