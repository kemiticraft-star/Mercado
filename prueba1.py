import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Mercado", text_alignment="center")

# --- URL de Base 1 ---
url_1 = "https://docs.google.com/spreadsheets/d/1hfUF27WMtRIFtnqqgbZX3NU5FSlApzhnw2x3ALUDaVo/export?format=csv"

# --- URL de Base 2---
url_2 = "https://docs.google.com/spreadsheets/d/1hfUF27WMtRIFtnqqgbZX3NU5FSlApzhnw2x3ALUDaVo/export?format=csv&gid=1970064496"

# --- URL de equivalencias ---
url_3 = "https://docs.google.com/spreadsheets/d/1hfUF27WMtRIFtnqqgbZX3NU5FSlApzhnw2x3ALUDaVo/export?format=csv&gid=280645324"


@st.cache_data
def cargar_datos(url):
    return pd.read_csv(url)


tabla1 = cargar_datos(url_1)
tabla2 = cargar_datos(url_2)
equivalencias = cargar_datos(url_3)


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

    # -------------------------------
    # LISTA DE COMPRAS CON CHECKBOXES
    # -------------------------------
    st.subheader("Lista de compras")
    
    
    # Crear estado persistente si no existe
    if "check_estado" not in st.session_state:
    	st.session_state.check_estado = {}
    
    
    # Crear claves únicas por producto (unidad + nombre + cantidad)
    # Si cambia la cantidad, se considera un item nuevo y el checkbox se reinicia
    claves_actuales = set()
    
    
    for _, fila in resultado.iterrows():
    	clave = f"{fila['Unidad']} - {fila['Producto']} - {fila['Cantidad']}"
    	claves_actuales.add(clave)
    
    
    	# Si el producto/cantidad es nuevo, iniciar en False
    	if clave not in st.session_state.check_estado:
    		st.session_state.check_estado[clave] = False
    
    
    	# Mostrar checkbox manteniendo estado previo solo si la cantidad no cambió
    	st.session_state.check_estado[clave] = st.checkbox(
    		f"{fila['Cantidad']} {fila['Unidad']} {fila['Producto']}",
    		value=st.session_state.check_estado[clave],
    		key=f"chk_{clave}"
    	)
    
    
    	# Eliminar del estado productos que ya no están en la lista
    	claves_guardadas = set(st.session_state.check_estado.keys())
    	for clave in claves_guardadas - claves_actuales:
    		del st.session_state.check_estado[clave]
    	claves_guardadas = set(st.session_state.check_estado.keys())
    	for clave in claves_guardadas - claves_actuales:
    		del st.session_state.check_estado[clave]

    
    # INGRESO MANUAL SIMPLE
    st.subheader("Agregar ingrediente manual")
    
    
    if "manual_items" not in st.session_state:
    	st.session_state.manual_items = []
    
    
    texto_manual = st.text_input("Escribe un ingrediente (ej: 2 kg arroz)")
    
    
    if st.button("Agregar"):
    	if texto_manual:
    		st.session_state.manual_items.append({
    			"texto": texto_manual,
    			"checked": False,
    		})
    
    
    # Mostrar ingredientes manuales
    if st.session_state.manual_items:
    	st.markdown("### Ingredientes manuales")
    
    
    	nuevos_items = []
    
    
    	for i, item in enumerate(st.session_state.manual_items):
    		col_chk, col_txt, col_del = st.columns([1, 6, 1])
    
    
    		with col_chk:
    			item["checked"] = st.checkbox(
    				"",
    				value=item["checked"],
    				key=f"manual_chk_{i}"
    			)
    
    
    		with col_txt:
    			st.write(item["texto"])
    
    
    		with col_del:
    			if st.button("❌", key=f"del_{i}"):
    				continue
    
    
    		nuevos_items.append(item)
    
    
    	st.session_state.manual_items = nuevos_items
    

# ===============================
# SECCIÓN 2 → PRECIOS HISTÓRICOS
# ===============================
st.divider()
st.header("Historial de precios")

# Selector de producto
producto = st.selectbox(
    "Elige un producto",
    tabla2["Producto"].unique()
)

# Filtrar datos del producto DESDE tabla2 (no tabla1)
fila = tabla2[tabla2["Producto"] == producto]

# Quitar la columna de nombre de producto y transponer
fila = fila.drop(columns="Producto").T

# Si no hay datos válidos, evitar error de columnas
if fila.shape[1] == 0:
    st.warning("Este producto no tiene datos.")
else:
    fila.columns = ["Precio"]

    # Limpiar símbolo de moneda si viene como texto
    fila["Precio"] = (
        fila["Precio"].astype(str)
        .str.replace("S/.", "", regex=False)
    )

    fila["Precio"] = pd.to_numeric(fila["Precio"], errors="coerce")

    # Convertir índice a fechas reales
    fila.index = pd.to_datetime(fila.index, format="%d/%m/%Y", errors="coerce")

    # Eliminar precios o fechas vacías
    fila = fila.dropna()

    # Mostrar gráfico
    if not fila.empty:
        fig, ax = plt.subplots()
        ax.plot(fila.index, fila["Precio"], marker="o")
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Precio (S/)")
        ax.set_title(f"Precio de {producto} en el tiempo")
        plt.xticks(rotation=45)

        st.pyplot(fig)

        # Último precio registrado
        ultima_fecha = fila.index.max()
        ultimo_precio = fila.loc[ultima_fecha, "Precio"]

        st.metric( 
            label=f"Último precio de {producto}", 
            value=f"S/ {ultimo_precio:.2f}", 
            delta=f"Registrado el {ultima_fecha}" 
        )

    else:
        st.warning("Este producto no tiene precios registrados.")

# ===============================
# SECCIÓN 3 → COSTO TOTAL POR PLATO
# ===============================
st.divider()
st.header("Costo total por plato")
                                             
# ===============================
# SECCIÓN 4 → GRÁFICO DE COSTOS
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

















