import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Mercado", text_alignment="center")

# --- URL del Google Sheets (tabla de compras) ---
url_1 = "https://docs.google.com/spreadsheets/d/1hfUF27WMtRIFtnqqgbZX3NU5FSlApzhnw2x3ALUDaVo/export?format=csv"

# --- URL de la tabla de precios (Base 2) ---
url_2 = "https://docs.google.com/spreadsheets/d/1hfUF27WMtRIFtnqqgbZX3NU5FSlApzhnw2x3ALUDaVo/export?format=csv&gid=1970064496"

@st.cache_data
def cargar_datos(url):
    return pd.read_csv(url)
    
tabla1 = cargar_datos(url_1)
tabla2 = cargar_datos(url_2)


# ===============================
# SECCIÓN 1 → LISTA DE COMPRAS
# ===============================
st.subheader("Tabla original")
st.dataframe(tabla1)

indices = st.multiselect(
    "Selecciona los índices",
    sorted(tabla1["Índice"].unique())
)

if indices:
    filtrado = tabla1[tabla1["Índice"].isin(indices)]

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


# ===============================
# SECCIÓN 2 → PRECIOS HISTÓRICOS
# ===============================
st.divider()
st.header("Historial de precios")

# Selector de producto
producto = st.selectbox(
    "Elige un ingrediente",
    tabla2["Producto"].unique()
)


# ===============================
# SECCIÓN 3 → CHEKLIST DE COMPRAS
# ===============================
st.divider()
st.header("Checklist de compras")

if indices:

    filtrado = tabla1[tabla1["Índice"].isin(indices)]

    resumen = (
        filtrado
        .groupby(["Unidad", "Producto"], as_index=False)["Cantidad"]
        .sum()
        .sort_values("Producto")
    )

    # --- inicializar estado ---
    if "checklist" not in st.session_state:
        st.session_state.checklist = {}

    # eliminar productos que ya no están
    productos_actuales = set(resumen["Producto"])
    st.session_state.checklist = {
        k: v for k, v in st.session_state.checklist.items()
        if k in productos_actuales
    }

    st.subheader("Marca lo que ya compraste")

    for _, fila in resumen.iterrows():
        producto = fila["Producto"]

        checked = st.session_state.checklist.get(producto, False)

        nuevo_valor = st.checkbox(
            f'{fila["Cantidad"]} {fila["Unidad"]} {producto}',
            value=checked,
            key=f"check_{producto}"
        )

        st.session_state.checklist[producto] = nuevo_valor

# ===============================
# SECCIÓN 4 → COSTO TOTAL POR PLATO
# ===============================
st.divider()
st.header("Costo total por plato")
                                             
# ===============================
# SECCIÓN 5 → GRÁFICO DE COSTOS
# ===============================

st.divider()
st.header("Ingrediente más costoso")

opciones = ["Total"] + sorted(indices)

seleccion = st.selectbox("Ver costos de:", opciones)

"""
if seleccion == "Total":
    datos_grafico = (
        df[df["Índice"].isin(indices)]
        .groupby("Producto")["Cantidad"]
        .sum()
        .sort_values(ascending=False)
    )
else:
    datos_grafico = (
        df[df["Índice"] == seleccion]
        .groupby("Producto")["Cantidad"]
        .sum()
        .sort_values(ascending=False)
    )
"""





