import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. CONFIGURACIÓN Y BASE DE DATOS
PROFESIONALES = ["Secretaría FAU"] 
PASSWORD_PRO = "salta2026"
DB_FILE = "turnos_db.csv"

if not os.path.exists(DB_FILE):
    df = pd.DataFrame(columns=["ID", "Profesional", "Fecha", "Hora", "Cliente", "Motivo", "Estado"])
    df.to_csv(DB_FILE, index=False)

def cargar_datos():
    return pd.read_csv(DB_FILE)

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

HORARIOS = [f"{h:02d}:{m:02d}" for h in range(9, 14) for m in (0, 30)] + ["14:00"]

st.set_page_config(page_title="Gestión de Turnos FAU", layout="wide")

# --- ESTILO INSTITUCIONAL ---
st.markdown("""
    <style>
    .main-header {
        background-color: #C0392B;
        padding: 15px;
        border-radius: 8px;
        color: white !important;
        text-align: center;
        margin-bottom: 20px;
        border-bottom: 4px solid #1B4F72;
    }
    .aviso-caja {
        background-color: #F8F9F9;
        padding: 20px;
        border-radius: 8px;
        border-left: 8px solid #C0392B;
        color: #1B4F72;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    .stButton>button {
        background-color: #1B4F72;
        color: white;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGACIÓN ---
menu = st.sidebar.radio("Navegación", ["Reserva de Turnos", "Panel Administrativo"])

# --- VISTA: RESERVA DE TURNOS ---
if menu == "Reserva de Turnos":
    # CAMBIO DE NOMBRE AQUÍ:
    st.markdown('<div class="main-header"><h1>SISTEMA DE TURNOS FAU</h1></div>', unsafe_allow_html=True)
    
    col_izq, col_der = st.columns([2, 1], gap="large")

    with col_izq:
        st.subheader("Solicitud de Turno")
        df = cargar_datos()
        
        if 'ultimo_turno' in st.session_state:
            st.success(f"EL TURNO SE REGISTRÓ CORRECTAMENTE: {st.session_state['ultimo_turno']}")
        
        with st.form("form_reserva"):
            prof = st.selectbox("Profesional:", PROFESIONALES)
            fecha = st.date_input("Fecha:", min_value=datetime.today())
            
            fecha_str = fecha.strftime("%d/%m/%Y")
            ocupados = df[(df["Profesional"] == prof) & (df["Fecha"] == fecha_str)]["Hora"].tolist()
            disponibles = [h for h in HORARIOS if h not in ocupados]
            
            hora_sel = st.selectbox("Horarios disponibles:", disponibles if disponibles else ["No hay horarios"])
            nombre = st.text_input("Nombre y Apellido del Docente:")
            motivo = st.text_input("Motivo del trámite:")
            
            enviar = st.form_submit_button("CONFIRMAR RESERVA")
            
            if enviar:
                if not disponibles or hora_sel == "No hay horarios":
                    st.error("No hay turnos para la fecha seleccionada.")
                elif not nombre:
                    st.warning("Debe ingresar su nombre completo.")
                else:
                    # ID ROBUSTO CON MICROSEGUNDOS
                    nuevo_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
                    nuevo = pd.DataFrame({
                        "ID": [nuevo_id],
                        "Profesional": [prof], "Fecha": [fecha_str], "Hora": [hora_sel],
                        "Cliente": [nombre], "Motivo": [motivo], "Estado": ["Pendiente"]
                    })
                    df = pd.concat([df, nuevo], ignore_index=True)
                    guardar_datos(df)
                    
                    st.session_state['ultimo_turno'] = f"{nombre} - {fecha_str} a las {hora_sel}"
                    st.rerun()

    with col_der:
        st.markdown(f"""
        <div class="aviso-caja">
            <h3 style="color:#C0392B;">AVISO IMPORTANTE</h3>
            <p>Antes de solicitar turno, verificar el cumplimiento de los requisitos establecidos para cada categoría docente, 
            conforme a lo dispuesto en la <b>Resolución Rectoral N.º 466/22</b> y en la <b>Resolución Rectoral N.º 872/24</b>, 
            especialmente lo previsto en sus artículos 6° y 7°.</p>
        </div>
        """, unsafe_allow_html=True)

# --- VISTA: PANEL ADMINISTRATIVO ---
else:
    st.markdown('<div class="main-header"><h1>ACCESO PROFESIONALES</h1></div>', unsafe_allow_html=True)
    
    pw = st.text_input("Ingrese la clave de acceso:", type="password")
    
    if pw == PASSWORD_PRO:
        df = cargar_datos()
        filtro_prof = st.selectbox("Ver turnos de:", PROFESIONALES)
        turnos_filtrados = df[df["Profesional"] == filtro_prof].copy()
        
        if turnos_filtrados.empty:
            st.info("No hay turnos registrados.")
        else:
            for index, row in turnos_filtrados.iterrows():
                with st.expander(f"{row['Fecha']} | {row['Hora']} - {row['Cliente']}"):
                    st.write(f"Motivo: {row['Motivo']}")
                    st.write(f"Estado: {row['Estado']}")
                    
                    c1, c2 = st.columns(2)
                    # KEYS ÚNICAS CON ID + INDEX
                    if c1.button("Confirmar", key=f"conf_{row['ID']}_{index}"):
                        df.loc[df["ID"] == row["ID"], "Estado"] = "Confirmado"
                        guardar_datos(df)
                        st.rerun()
                    if c2.button("Eliminar", key=f"del_{row['ID']}_{index}"):
                        df = df[df["ID"] != row["ID"]]
                        guardar_datos(df)
                        st.rerun()
            
            st.divider()
            st.dataframe(turnos_filtrados)
    elif pw != "":
        st.error("Contraseña incorrecta")
