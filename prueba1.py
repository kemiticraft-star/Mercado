import streamlit as st
import pandas as pd

st.title("Mercado", text_alignment="center")

# Leer Excel directamente desde el disco
url = "https://docs.google.com/spreadsheets/d/1hfUF27WMtRIFtnqqgbZX3NU5FSlApzhnw2x3ALUDaVo/export?format=csv"

df = pd.read_csv(url)

st.subheader("Tabla original")
st.dataframe(df)

# Selección múltiple de índices
indices = st.multiselect(
    "Selecciona los índices",
    sorted(df["Índice"].unique())
)

if indices:
    filtrado = df[df["Índice"].isin(indices)]

    resultado = (
        filtrado
        .groupby(["Unidad", "Producto"], as_index=False)["Cantidad"]
        .sum()
    )

    st.subheader("Ingredientes totales")
    st.dataframe(resultado)

    st.subheader("Lista de compras")
    for _, fila in resultado.iterrows():
        st.write(f'{fila["Cantidad"]} {fila["Unidad"]} {fila["Producto"]}')


