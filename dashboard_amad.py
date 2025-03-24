
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from io import BytesIO
from fpdf import FPDF
import base64

# Configuración de página
st.set_page_config(page_title="Dashboard AMAD", layout="wide")

# Logotipo
st.sidebar.image("logo_s10plus.png", width=200)

# Conexión a la base de datos
def cargar_datos():
    try:
        engine = create_engine("mysql+pymysql://spluscom_powerbi:S10Octubre2022@localhost/spluscom_db_amad")
        query = "SELECT * FROM temporal_amad"
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error("❌ Error al conectar con la base de datos o al cargar los datos.")
        return None

df = cargar_datos()

if df is not None:
    st.title("📊 Dashboard AMAD")

    # --- Filtros ---
    st.sidebar.header("🔎 Filtros")
    fechas = st.sidebar.date_input("Rango de fechas", [])
    localidad = st.sidebar.multiselect("Localidad", options=sorted(df["localidad"].dropna().unique()))
    concepto = st.sidebar.multiselect("Concepto", options=sorted(df["concepto"].dropna().unique()))

    # --- Aplicar filtros ---
    if fechas:
        if len(fechas) == 2:
            df = df[(df["fecha"] >= pd.to_datetime(fechas[0])) & (df["fecha"] <= pd.to_datetime(fechas[1]))]
    if localidad:
        df = df[df["localidad"].isin(localidad)]
    if concepto:
        df = df[df["concepto"].isin(concepto)]

    # --- KPIs ---
    col1, col2, col3 = st.columns(3)
    col1.metric("🧾 Total Actividades", len(df))
    col2.metric("👤 Usuarios Únicos", df["numero"].nunique())
    col3.metric("📍 Localidades", df["localidad"].nunique())

    # --- Gráficas ---
    st.subheader("📈 Actividades por Fecha")
    fig_fecha = px.histogram(df, x="fecha", nbins=30)
    st.plotly_chart(fig_fecha, use_container_width=True)

    st.subheader("⏰ Actividad por Hora")
    if "hora" in df.columns:
        df["hora"] = pd.to_numeric(df["hora"], errors="coerce")
        fig_hora = px.histogram(df.dropna(subset=["hora"]), x="hora", nbins=24)
        st.plotly_chart(fig_hora, use_container_width=True)

    st.subheader("🏷️ Actividades por Etiqueta")
    fig_etiqueta = px.histogram(df, x="etiqueta")
    st.plotly_chart(fig_etiqueta, use_container_width=True)

    st.subheader("📌 Actividades por Concepto")
    fig_concepto = px.histogram(df, x="concepto")
    st.plotly_chart(fig_concepto, use_container_width=True)

    st.subheader("🗺️ Mapa de Actividades")
    if "latitud" in df.columns and "longitud" in df.columns:
        df_mapa = df.dropna(subset=["latitud", "longitud"])
        st.map(df_mapa[["latitud", "longitud"]])

    # --- Exportar a Excel ---
    def generar_excel():
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="AMAD")
        datos = output.getvalue()
        b64 = base64.b64encode(datos).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="amad.xlsx">📥 Descargar Excel</a>'
        return href

    # --- Exportar a PDF (solo resumen) ---
    def generar_pdf(df):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Resumen de Actividad AMAD", ln=True, align="C")
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Total Actividades: {len(df)}", ln=True)
        pdf.cell(200, 10, txt=f"Usuarios Únicos: {df['numero'].nunique()}", ln=True)
        pdf.cell(200, 10, txt=f"Localidades: {df['localidad'].nunique()}", ln=True)
        output = BytesIO()
        pdf.output(output)
        b64 = base64.b64encode(output.getvalue()).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="resumen_amad.pdf">📥 Descargar PDF</a>'
        return href

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(generar_excel(), unsafe_allow_html=True)
    with col_b:
        st.markdown(generar_pdf(df), unsafe_allow_html=True)
else:
    st.warning("No se pudo cargar la base de datos. Revisa tu conexión.")
