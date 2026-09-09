import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from streamlit_gsheets import GSheetsConnection

# 1. Configuración de la aplicación web
st.set_page_config(page_title="Dashboard Financiero", layout="wide", initial_sidebar_state="collapsed")

# Estilo CSS personalizado para centrar títulos y ajustar márgenes
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; }
    h1 { text-align: center; color: #1E3A8A; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Análisis de Rentabilidad por Servicio - 2026")
st.markdown("<br>", unsafe_allow_html=True)

# 2. Conexión a la Base de Datos (Google Sheets)
url_sheets = "https://docs.google.com/spreadsheets/d/1S7MJBL_10-DfDCb4E4C3-GJDsluuI41bU_6bUOYl7LM/edit?usp=sharing" 

# Establecer conexión
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600) # Refresca los datos automáticamente cada 10 minutos
def cargar_datos():
    hojas = ["Geofisica", "Instrumentacion", "Geoelectrica"]
    diccionario_datos = {}
    for hoja in hojas:
        # Lee cada pestaña directamente desde la nube
        diccionario_datos[hoja] = conn.read(spreadsheet=url_sheets, worksheet=hoja)
    return diccionario_datos

datos_servicios = cargar_datos()

# Paleta de colores corporativa
COLOR_INGRESOS = '#2563EB'  # Azul corporativo brillante
COLOR_EGRESOS = '#64748B'   # Gris pizarra elegante
COLOR_MARGEN = '#F59E0B'    # Ámbar/Dorado para resaltar la rentabilidad
FONDO_GRAFICO = 'rgba(0,0,0,0)' # Transparente para adaptarse al tema de Streamlit

# 3. Crear Pestañas dinámicas
nombres_servicios = list(datos_servicios.keys())
pestañas = st.tabs([f"🏢 {nombre}" for nombre in nombres_servicios])

# 4. Procesar y graficar
for i, nombre in enumerate(nombres_servicios):
    with pestañas[i]:
        df = datos_servicios[nombre]
        
        if not {'Mes', 'Ingresos', 'Egresos'}.issubset(df.columns):
            st.warning(f"La hoja {nombre} no tiene las columnas requeridas.")
            continue
            
        # Rellenar valores nulos (NaN) con 0 por seguridad
        df['Ingresos'] = df['Ingresos'].fillna(0)
        df['Egresos'] = df['Egresos'].fillna(0)

        # Cálculo de márgenes mensuales para la gráfica
        df['Ganancia'] = df['Ingresos'] - df['Egresos']
        df['Margen (%)'] = np.where(
            df['Ingresos'] > 0, 
            (df['Ganancia'] / df['Ingresos']) * 100, 
            0 # Si no hay ingresos, el margen es 0 para la gráfica
        )
        
        # --- CÁLCULO CORREGIDO DEL MARGEN GLOBAL ---
        ingresos_totales = df['Ingresos'].sum()
        egresos_totales = df['Egresos'].sum()
        ganancia_total = ingresos_totales - egresos_totales
        
        if ingresos_totales > 0:
            margen_promedio_real = (ganancia_total / ingresos_totales) * 100
        else:
            margen_promedio_real = 0
        
        # Tarjetas de métricas (KPIs) - Ahora con 4 columnas
        cols = st.columns(4)
        
        # 1. Ingresos
        cols[0].metric("Ingresos Anuales", f"${ingresos_totales:,.0f}")
        
        # 2. Egresos
        cols[1].metric("Egresos Anuales", f"${egresos_totales:,.0f}")
        
        # 3. Utilidad Total (NUEVO)
        cols[2].metric("Utilidad Total", f"${ganancia_total:,.0f}", 
                       delta="Ganancia" if ganancia_total > 0 else "Déficit", 
                       delta_color="normal" if ganancia_total > 0 else "inverse")
        
        # 4. Margen Global
        cols[3].metric("Margen Global", f"{margen_promedio_real:.1f}%", 
                       delta="Rentabilidad Positiva" if margen_promedio_real > 0 else "Alerta", 
                       delta_color="normal" if margen_promedio_real > 0 else "inverse")
        
        st.divider()

        # Construcción del gráfico
        fig = go.Figure()

        # Barras de Ingresos
        fig.add_trace(go.Bar(
            x=df['Mes'], 
            y=df['Ingresos'], 
            name='Ingresos', 
            marker_color=COLOR_INGRESOS,
            # hovertemplate explícito para asegurar que se muestre
            hovertemplate='<b>Mes:</b> %{x}<br><b>Ingreso:</b> $%{y:,.0f}<extra></extra>' 
        ))
        
        # Barras de Egresos
        fig.add_trace(go.Bar(
            x=df['Mes'], 
            y=df['Egresos'], 
            name='Egresos', 
            marker_color=COLOR_EGRESOS,
            hovertemplate='<b>Mes:</b> %{x}<br><b>Egreso:</b> $%{y:,.0f}<extra></extra>'
        ))

        # Línea de Margen
        fig.add_trace(go.Scatter(
            x=df['Mes'], 
            y=df['Margen (%)'], 
            name='Margen Mensual', 
            yaxis='y2', 
            mode='lines+markers', 
            marker=dict(size=8, color=COLOR_MARGEN, symbol='diamond'), 
            line=dict(width=2.5, color=COLOR_MARGEN),
            hovertemplate='<b>Mes:</b> %{x}<br><b>Margen:</b> %{y:.1f}%<extra></extra>'
        ))

        # Diseño Profesional
        fig.update_layout(
            title=dict(
                text=f"Flujo Financiero Mensual - {nombre}",
                font=dict(size=20, color='#334155'),
                y=0.95
            ),
            barmode='group',
            plot_bgcolor=FONDO_GRAFICO,
            paper_bgcolor=FONDO_GRAFICO,
            # Configuración Eje Y Principal (Valores)
            yaxis=dict(
                title=dict(text="Valor en COP ($)", font=dict(color=COLOR_INGRESOS)),
                tickfont=dict(color='#475569'),
                showgrid=True,
                gridcolor='#E2E8F0',
                zeroline=True,
                zerolinecolor='#CBD5E1'
            ),
            # Configuración Eje Y Secundario (Porcentaje)
            yaxis2=dict(
                title=dict(text="Margen Mensual (%)", font=dict(color=COLOR_MARGEN)), 
                tickfont=dict(color=COLOR_MARGEN),
                overlaying='y', 
                side='right', 
                showgrid=False,
                zeroline=True,
                zerolinecolor=COLOR_MARGEN,
            ),
            # El hovermode 'x' agrupa los datos al pasar el cursor si están en el mismo punto X,
            # pero 'closest' asegura que se dispare la tarjeta individual de la barra/punto que toques.
            hovermode="closest", 
            legend=dict(
                orientation="h", 
                yanchor="bottom", 
                y=1.05, 
                xanchor="center", 
                x=0.5,
                bgcolor='rgba(255,255,255,0.8)'
            ),
            margin=dict(l=40, r=40, t=80, b=40)
        )

        st.plotly_chart(fig, use_container_width=True)
        
        #cd C:\Users\Inteinsa\Desktop\Python\Indicadores
        #streamlit run Indicadores.py