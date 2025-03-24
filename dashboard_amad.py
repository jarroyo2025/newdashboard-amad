
import os
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
from sqlalchemy import create_engine

st.set_page_config(page_title="Dashboard AMAD", layout="wide")
logo_path = "logo_s10plus.png"

def cargar_datos():
    try:
        usuario = "spluscom_powerbi"
        contrasena = "S10Octubre2022"
        host = "s10plus.com"
        puerto = "3306"
        base = "spluscom_db_amad"
        
        engine = create_engine(f"mysql+pymysql://{usuario}:{contrasena}@{host}:{puerto}/{base}")
        query = "SELECT * FROM temporal_amad"
        df = pd.read_sql(query, engine)

        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df['hora'] = pd.to_datetime(df['hora'], format='%H:%M:%S', errors='coerce').dt.hour
        return df
    except Exception as e:
        st.error("❌ Error al conectar con la base de datos o al cargar los datos.")
        st.exception(e)
        return None

df = cargar_datos()

if df is not None:
    st.subheader("🧾 Columnas disponibles en la base de datos")
    st.write(df.columns.tolist())

if df is not None:
    with st.sidebar:
        st.image(logo_path, width=200)
        st.title("Filtros")
        fecha_min, fecha_max = st.date_input("Rango de Fechas", [df["fecha"].min(), df["fecha"].max()])
        localidades = st.multiselect("Localidad", df["localidad"].dropna().unique(), default=list(df["localidad"].dropna().unique()))
        df_filtrado = df[(df["fecha"] >= pd.to_datetime(fecha_min)) & (df["fecha"] <= pd.to_datetime(fecha_max))]
        df_filtrado = df_filtrado[df_filtrado["localidad"].isin(localidades)]

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📊 Total Actividad AMAD", int(df_filtrado["totaldia"].sum()))
    col2.metric("📱 Total Aplicación", int(df_filtrado["totalaplicacion"].sum()))
    col3.metric("📷 Total QR", int(df_filtrado["totalporconcepto"].sum()))
    col4.metric("💬 Conversaciones", int(df_filtrado["totaletiqueta"].sum()))
    col5.metric("👥 Usuarios Únicos", df_filtrado["Usuarios Únicos"].nunique() if "Usuarios Únicos" in df_filtrado.columns else "-")

    st.markdown("### Actividad por Hora")
    hora_total = df_filtrado["hora"].value_counts().sort_index()
    if not hora_total.empty:
        fig_hora = px.line(x=hora_total.index, y=hora_total.values,
                           labels={"x": "Hora del Día", "y": "Eventos"},
                           title="Eventos por Hora")
        st.plotly_chart(fig_hora, use_container_width=True)
    else:
        st.warning("⚠️ No hay datos por hora para mostrar.")

    def exportar_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name="Datos Filtrados")
            writer.save()
        return output.getvalue()

    st.download_button(
        label="📥 Exportar a Excel",
        data=exportar_excel(df_filtrado),
        file_name="reporte_actividad.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    def exportar_pdf(df):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        if os.path.exists(logo_path):
            pdf.image(logo_path, x=10, y=8, w=40)
        pdf.cell(200, 10, txt="Reporte de Actividad AMAD", ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.ln(20)
        pdf.cell(200, 10, f"Fecha de generación: {datetime.today().strftime('%Y-%m-%d')}", ln=True)

        pdf.ln(10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, f"Total Actividad: {int(df['totaldia'].sum())}", ln=True)
        pdf.cell(200, 10, f"Total Aplicación: {int(df['totalaplicacion'].sum())}", ln=True)
        pdf.cell(200, 10, f"Total QR: {int(df['totalporconcepto'].sum())}", ln=True)
        pdf.cell(200, 10, f"Conversaciones: {int(df['totaletiqueta'].sum())}", ln=True)
        if "Usuarios Únicos" in df.columns:
            pdf.cell(200, 10, f"Usuarios Únicos: {df['Usuarios Únicos'].nunique()}", ln=True)

        output = BytesIO()
        pdf.output(output)
        return output.getvalue()

    st.download_button(
        label="🧾 Exportar a PDF",
        data=exportar_pdf(df_filtrado),
        file_name="reporte_actividad.pdf",
        mime="application/pdf"
    )
