import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Mercado")

# --- URL del Google Sheets (tabla de compras) ---
url_compras = "https://docs.google.com/spreadsheets/d/1hfUF27WMtRIFtnqqgbZX3NU5FSlApzhnw2x3ALUDaVo/export?format=csv"

# --- URL de la tabla de precios (Base 2) ---
url_precios = "https://docs.google.com/spreadsheets/d/1hfUF27WMtRIFtnqqgbZX3NU5FSlApzhnw2x3ALUDaVo/export?format=csv&gid=1970064496"


# Cache para velocidad
@st.cache_data
def cargar_datos(url):
    return pd.read_csv(url)


df = cargar_datos(url_compras)
precios = cargar_datos(url_precios)

# ===============================
# SECCIÓN 1 → LISTA DE COMPRAS
# ===============================
st.subheader("Tabla original", text_alignment="center")
st.dataframe(df)

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


# ===============================
# SECCIÓN 2 → PRECIOS HISTÓRICOS
# ===============================
st.divider()
st.header("Historial de precios")

# Selector de producto
producto = st.selectbox(
    "Elige un ingrediente",
    precios["Producto"].unique()
)

# Filtrar fila del producto
fila_producto = precios[precios["Producto"] == producto]

if not fila_producto.empty:

    # Quitar columna Producto y convertir a formato largo
    serie = fila_producto.drop(columns=["Producto"]).T
    serie.columns = ["Precio"]
    serie.index.name = "Fecha"

    # Convertir fechas
    serie.index = pd.to_datetime(serie.index, dayfirst=True, errors="coerce")

    # Quitar vacíos
    serie = serie.dropna()

    # -------- Gráfico --------
    fig, ax = plt.subplots()
    ax.plot(serie.index, serie["Precio"], marker="o")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Precio (S/)")
    ax.set_title(f"Precio histórico de {producto}")
    ax.grid(True)

    st.pyplot(fig)

    # -------- Último precio --------
    ultimo_precio = serie["Precio"].iloc[-1]
    ultima_fecha = serie.index[-1].strftime("%d/%m/%Y")

    st.metric(
        label=f"Último precio de {producto}",
        value=f"S/ {ultimo_precio:.2f}",
        delta=f"Registrado el {ultima_fecha}"
    )


