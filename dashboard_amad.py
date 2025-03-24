
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
from PIL import Image

# -------- CONFIGURACIÓN --------
st.set_page_config(page_title="Dashboard AMAD", layout="wide")
logo_path = "logo_s10plus.png"

# -------- CARGA DE DATOS --------
@st.cache_data
def cargar_datos():
    # Este dataframe debe reemplazarse con la conexión real
    df = pd.read_csv("https://raw.githubusercontent.com/datablist/sample-csv-files/main/files/people/people-100.csv")
    df["fecha"] = pd.date_range(end=datetime.today(), periods=len(df))
    df["totaldia"] = pd.Series([i*10 for i in range(len(df))])
    df["totalaplicacion"] = df["totaldia"] * 0.4
    df["total_qr"] = df["totaldia"] * 0.3
    df["totaletiqueta"] = df["totaldia"] * 0.2
    df["Usuarios Únicos"] = df.index % 50
    df["hora"] = df["fecha"].dt.hour
    df["localidad"] = df["Country"]
    return df

df = cargar_datos()

# -------- FILTROS --------
with st.sidebar:
    st.image(logo_path, width=200)
    st.title("Filtros")
    fecha_min, fecha_max = st.date_input("Rango de Fechas", [df["fecha"].min(), df["fecha"].max()])
    localidades = st.multiselect("Localidad", df["localidad"].unique(), default=list(df["localidad"].unique()))
    df_filtrado = df[(df["fecha"] >= pd.to_datetime(fecha_min)) & (df["fecha"] <= pd.to_datetime(fecha_max))]
    df_filtrado = df_filtrado[df_filtrado["localidad"].isin(localidades)]

# -------- KPIs --------
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("📊 Total Actividad AMAD", int(df_filtrado["totaldia"].sum()))
col2.metric("📱 Total Aplicación", int(df_filtrado["totalaplicacion"].sum()))
col3.metric("📷 Total QR", int(df_filtrado["total_qr"].sum()))
col4.metric("💬 Conversaciones", int(df_filtrado["totaletiqueta"].sum()))
col5.metric("👥 Usuarios Únicos", df_filtrado["Usuarios Únicos"].nunique())

# -------- GRÁFICAS --------
st.markdown("### Actividad por Hora")
hora_total = df_filtrado["hora"].value_counts().sort_index()
if not hora_total.empty:
    fig_hora = px.line(x=hora_total.index, y=hora_total.values,
                       labels={"x": "Hora del Día", "y": "Eventos"},
                       title="Eventos por Hora")
    st.plotly_chart(fig_hora, use_container_width=True)
else:
    st.warning("⚠️ No hay datos por hora para mostrar.")

# -------- EXPORTAR A EXCEL --------
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

# -------- EXPORTAR A PDF --------
def exportar_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.image(logo_path, x=10, y=8, w=40)
    pdf.cell(200, 10, txt="Reporte de Actividad AMAD", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.ln(20)
    pdf.cell(200, 10, f"Fecha de generación: {datetime.today().strftime('%Y-%m-%d')}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, f"Total Actividad: {int(df['totaldia'].sum())}", ln=True)
    pdf.cell(200, 10, f"Total Aplicación: {int(df['totalaplicacion'].sum())}", ln=True)
    pdf.cell(200, 10, f"Total QR: {int(df['total_qr'].sum())}", ln=True)
    pdf.cell(200, 10, f"Conversaciones: {int(df['totaletiqueta'].sum())}", ln=True)
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
