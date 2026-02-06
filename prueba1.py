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
# SECCIÓN 3 → CHEKLIST DE COMPRAS
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
# SECCIÓN 4 → COSTO TOTAL POR PLATO
# ===============================
st.divider()
st.header("Costo total por índice")

if indices:

    # ---------- CARGAR TABLA DE CONVERSIÓN (HOJA 3) ----------
    url_conversion = "https://docs.google.com/spreadsheets/d/1hfUF27WMtRIFtnqqgbZX3NU5FSlApzhnw2x3ALUDaVo/export?format=csv&gid=280645324"
    conversion = cargar_datos(url_conversion)

    # limpiar nombres
    conversion.columns = ["Producto", "und_por_kg"]

    # ---------- LIMPIAR PRECIOS (HOJA 2) ----------
    precios_largos = precios.melt(
        id_vars="Producto",
        var_name="Fecha",
        value_name="Precio"
    )

    precios_largos["Precio"] = (
        precios_largos["Precio"]
        .astype(str)
        .str.replace("S/", "", regex=False)
        .str.replace(" ", "", regex=False)
    )

    precios_largos["Precio"] = pd.to_numeric(precios_largos["Precio"], errors="coerce")
    precios_largos["Fecha"] = pd.to_datetime(precios_largos["Fecha"], dayfirst=True, errors="coerce")
    precios_largos = precios_largos.dropna()

    # ---------- ÚLTIMO PRECIO POR PRODUCTO ----------
    ultimo_precio = (
        precios_largos
        .sort_values("Fecha")
        .groupby("Producto")
        .tail(1)[["Producto", "Precio"]]
    )

    # ---------- UNIR TODO ----------
    datos = (
        df[df["Índice"].isin(indices)]
        .merge(ultimo_precio, on="Producto", how="left")
        .merge(conversion, on="Producto", how="left")
    )

    # ---------- CONVERSIÓN und → kg ----------
    # si unidad es "und", convertir cantidad a kg usando und_por_kg
    datos["Cantidad_kg"] = datos.apply(
        lambda fila: fila["Cantidad"] / fila["und_por_kg"]
        if fila["Unidad"] == "und" and pd.notna(fila["und_por_kg"])
        else fila["Cantidad"],
        axis=1
    )

    # ---------- COSTO ----------
    datos["Costo"] = datos["Cantidad_kg"] * datos["Precio"]

    # ---------- TABLA FINAL ----------
    costo_por_indice = (
        datos.groupby("Índice")["Costo"]
        .sum()
        .reset_index()
        .rename(columns={"Índice": "Indice", "Costo": "Precio"})
        .sort_values("Indice")
    )

    st.dataframe(costo_por_indice)

    # ---------- TOTAL GENERAL ----------
    total_general = costo_por_indice["Precio"].sum()
    st.subheader(f"Total general: S/ {total_general:.2f}")

                                             
# ===============================
# SECCIÓN 5 → GRÁFICO DE COSTOS
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



