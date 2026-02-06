import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Mercado", text_alignment="center")

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
st.subheader("Tabla original")
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

    # Pasar a formato vertical
    serie = fila_producto.drop(columns=["Producto"]).T
    serie.columns = ["Precio"]
    serie.index.name = "Fecha"

    # ---- LIMPIAR PRECIOS ----
    serie["Precio"] = (
        serie["Precio"]
        .astype(str)
        .str.replace("S/", "", regex=False)
        .str.replace(" ", "", regex=False)
    )

    serie["Precio"] = pd.to_numeric(serie["Precio"], errors="coerce")

    # ---- LIMPIAR FECHAS ----
    serie.index = pd.to_datetime(serie.index, dayfirst=True, errors="coerce")

    # quitar vacíos
    serie = serie.dropna()

    if not serie.empty:

        # -------- GRÁFICO --------
        fig, ax = plt.subplots()

        ax.plot(serie.index, serie["Precio"], marker="o")

        # mejorar eje X
        fig.autofmt_xdate(rotation=45)
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Precio (S/)")
        ax.set_title(f"Precio histórico de {producto}")
        ax.grid(True)

        st.pyplot(fig)

        # -------- ÚLTIMO PRECIO --------
        ultimo_precio = serie["Precio"].iloc[-1]
        ultima_fecha = serie.index[-1].strftime("%d/%m/%Y")

        st.metric(
            label=f"Último precio de {producto}",
            value=f"S/ {ultimo_precio:.2f}",
            delta=f"Registrado el {ultima_fecha}"
        )

    else:
        st.warning("Este producto no tiene precios registrados.")

# ===============================
# CHECKLIST DE COMPRAS
# ===============================
st.divider()
st.header("Checklist de compras")

if indices:

    filtrado = df[df["Índice"].isin(indices)]

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
# COSTO TOTAL POR ÍNDICE
# ===============================
st.divider()
st.header("Costo total por índice")

if indices:

    # -------- obtener último precio por producto --------
    precios_limpios = precios.copy()

    # quitar columna Producto y quedarnos con último valor
    precios_largos = (
        precios_limpios
        .set_index("Producto")
        .apply(
            lambda fila: pd.to_numeric(
                fila.astype(str)
                    .str.replace("S/", "", regex=False)
                    .str.replace(" ", "", regex=False),
                errors="coerce"
            ).dropna().iloc[-1] if fila.dropna().size > 0 else None,
            axis=1
        )
        .rename("Precio")
        .reset_index()
    )

    # -------- unir con cantidades --------
    datos = df[df["Índice"].isin(indices)].merge(
        precios_largos,
        on="Producto",
        how="left"
    )

    # -------- calcular costo --------
    datos["Costo"] = datos["Cantidad"] * datos["Precio"]

    # -------- total por índice --------
    costo_por_indice = (
        datos.groupby("Índice")["Costo"]
        .sum()
        .reset_index()
        .sort_values("Índice")
    )

    st.dataframe(costo_por_indice)

    # -------- total general --------
    total_general = costo_por_indice["Costo"].sum()

    st.subheader(f"Total general: S/ {total_general:.2f}")

# ===============================
# GRÁFICO DE COSTOS
# ===============================
import matplotlib.pyplot as plt

st.divider()
st.header("Ingrediente más costoso")

opciones = ["Total"] + sorted(indices)

seleccion = st.selectbox("Ver costos de:", opciones)

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

if not datos_grafico.empty:

    fig, ax = plt.subplots()

    datos_grafico.plot(kind="bar", ax=ax)

    ax.set_ylabel("Cantidad")
    ax.set_xlabel("Producto")
    ax.set_title("Costo por ingrediente")
    plt.xticks(rotation=45)

    st.pyplot(fig)



