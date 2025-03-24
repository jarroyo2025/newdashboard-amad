
import os
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

# Configuración inicial
st.set_page_config(page_title="Dashboard AMAD", layout="wide")
st.title("📊 Dashboard AMAD - Actividad General")
st.markdown("Conexión a la base de datos `spluscom_db_amad`, tabla `temporal_amad`.")

# --- CARGAR DATOS ---
@st.cache_data
def cargar_datos():
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

df = cargar_datos()

# --- FILTROS ---
st.sidebar.header("🔍 Filtros")

fecha_min = df['fecha'].min().date()
fecha_max = df['fecha'].max().date()
fecha_inicio = st.sidebar.date_input("Desde", fecha_min)
fecha_fin = st.sidebar.date_input("Hasta", fecha_max)

origenes = st.sidebar.multiselect("Origen", df['origen'].dropna().unique(), default=df['origen'].dropna().unique())
localidades = st.sidebar.multiselect("Localidad", df['localidad'].dropna().unique(), default=df['localidad'].dropna().unique())
modelos = st.sidebar.multiselect("Modelo", df['modelo'].dropna().unique(), default=df['modelo'].dropna().unique())
etiquetas = st.sidebar.multiselect("Etiqueta", df['etiqueta'].dropna().unique(), default=df['etiqueta'].dropna().unique())

df_filtrado = df[
    (df['fecha'].dt.date >= fecha_inicio) &
    (df['fecha'].dt.date <= fecha_fin) &
    (df['origen'].isin(origenes)) &
    (df['localidad'].isin(localidades)) &
    (df['modelo'].isin(modelos)) &
    (df['etiqueta'].isin(etiquetas))
]

# --- VISUALIZACIONES ---

st.subheader("📅 Actividad Total por Día")
actividad_dia = df_filtrado['fecha'].dt.date.value_counts().sort_index()
fig_dia = px.line(x=actividad_dia.index, y=actividad_dia.values,
                  labels={'x': 'Fecha', 'y': 'Eventos'},
                  title="Eventos registrados por día")
st.plotly_chart(fig_dia, use_container_width=True)

st.subheader("👥 Usuarios Únicos por Día")
if 'Usuarios Únicos' in df_filtrado.columns:
    usuarios_dia = df_filtrado.groupby(df_filtrado['fecha'].dt.date)['Usuarios Únicos'].sum()
    fig_usuarios = px.bar(x=usuarios_dia.index, y=usuarios_dia.values,
                          labels={'x': 'Fecha', 'y': 'Usuarios Únicos'},
                          title="Usuarios únicos por día")
    st.plotly_chart(fig_usuarios, use_container_width=True)

st.subheader("⏰ Actividad por Hora")
if 'hora' in df_filtrado.columns:
    hora_total = df_filtrado['hora'].value_counts().sort_index()
    if not hora_total.empty:
        fig_hora = px.line(x=hora_total.index, y=hora_total.values,
                           labels={'x': 'Hora del Día', 'y': 'Eventos'},
                           title="Eventos por Hora")
        st.plotly_chart(fig_hora, use_container_width=True)
    else:
        st.warning("⚠️ No hay datos de actividad por hora para los filtros seleccionados.")

st.subheader("📡 Actividad por Origen")
origen_total = df_filtrado['origen'].value_counts()
fig_origen = px.bar(x=origen_total.index, y=origen_total.values,
                    labels={'x': 'Origen', 'y': 'Total'}, title="Eventos por Origen")
st.plotly_chart(fig_origen, use_container_width=True)

st.subheader("🏙️ Actividad por Localidad")
localidad_total = df_filtrado['localidad'].value_counts().nlargest(15)
fig_localidad = px.bar(x=localidad_total.index, y=localidad_total.values,
                       labels={'x': 'Localidad', 'y': 'Eventos'}, title="Top 15 Localidades")
st.plotly_chart(fig_localidad, use_container_width=True)

st.subheader("🏷️ Etiquetas más utilizadas")
etiqueta_total = df_filtrado['etiqueta'].value_counts().nlargest(10)
fig_etiqueta = px.bar(x=etiqueta_total.index, y=etiqueta_total.values,
                      labels={'x': 'Etiqueta', 'y': 'Eventos'}, title="Top 10 Etiquetas")
st.plotly_chart(fig_etiqueta, use_container_width=True)

st.subheader("📱 Modelos más utilizados")
modelo_total = df_filtrado['modelo'].value_counts().nlargest(10)
fig_modelo = px.bar(x=modelo_total.index, y=modelo_total.values,
                    labels={'x': 'Modelo', 'y': 'Eventos'}, title="Top 10 Modelos")
st.plotly_chart(fig_modelo, use_container_width=True)

# --- MAPA DE GEOLOCALIZACIÓN ---
if 'latitud' in df_filtrado.columns and 'longitud' in df_filtrado.columns:
    st.subheader("🗺️ Mapa de Geolocalización")
    df_geo = df_filtrado.dropna(subset=['latitud', 'longitud'])
    fig_map = px.scatter_mapbox(df_geo,
                                lat='latitud',
                                lon='longitud',
                                hover_name='localidad',
                                zoom=4,
                                height=500)
    fig_map.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig_map, use_container_width=True)

st.success("✅ Dashboard cargado con éxito.")
