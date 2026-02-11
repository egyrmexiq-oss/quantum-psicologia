import streamlit as st
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS
from io import BytesIO
import pandas as pd
import streamlit.components.v1 as components
import time

# ==========================================
# ⚙️ 1. CONFIGURACIÓN Y ESTILOS (AMBIENTE ZEN)
# ==========================================
st.set_page_config(page_title="Quantum Mind - Psicología", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* BARRA FIJA INFERIOR (ESTILO WHATSAPP) */
    .fixed-footer {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background-color: #161B22; padding: 1rem; z-index: 999;
        border-top: 1px solid #30363D;
    }
    
    /* Ajuste para que el chat no quede tapado */
    .block-container { padding-bottom: 140px; }
    
    /* Estilos Login */
    .login-container { text-align: center; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIÓN DE SECRETOS ---
try:
    # Intenta leer GOOGLE_API_KEY (o GEMINI_API_KEY si usaste ese nombre)
    API_KEY = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    ACCESO_KEYS = st.secrets.get("access_keys", {"demo": "Usuario Demo"})
except:
    st.error("⚠️ Error configurando Secrets.")
    st.stop()

if not API_KEY:
    st.error("⚠️ Falta la API KEY en los Secrets.")
    st.stop()

# Configurar Gemini
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Inicializar Estado
if "mensajes" not in st.session_state: st.session_state.mensajes = []
if "usuario_activo" not in st.session_state: st.session_state.usuario_activo = None
if "modo_terapia" not in st.session_state: st.session_state.modo_terapia = "Escucha Empática"

# --- CONTADOR DE VISITAS (NO RANDOM) ---
# Usamos un número base fijo + incremento por sesión para simular persistencia
if "visitas_contador" not in st.session_state:
    st.session_state.visitas_contador = 14205  # Número base fijo
    # Incremento pequeño aleatorio solo al iniciar sesión para dar realismo
    # pero luego se mantiene fijo durante la charla
    
# ==========================================
# 💎 2. CONEXIÓN CON HOJA DE CÁLCULO
# ==========================================
URL_GOOGLE_SHEET = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBFtqUTpPEcOvfXZteeYZJBEzcoucLwN9OYlLRvbAGx_ZjIoQsg1fzqE6lOeDjoSTm4LWnoAnV7C4q/pub?output=csv" 

@st.cache_data(ttl=3600) # Guardar en caché 1 hora para no gastar lecturas
def cargar_especialistas():
    try:
        df = pd.read_csv(URL_GOOGLE_SHEET)
        df.columns = [c.strip().lower() for c in df.columns]
        mapa = {}
        for col in df.columns:
            if "nombre" in col: mapa[col] = "nombre"
            elif "especialidad" in col: mapa[col] = "especialidad"
            elif "ciudad" in col: mapa[col] = "ciudad"
            elif "aprobado" in col: mapa[col] = "aprobado"
        
        df = df.rename(columns=mapa)
        # Filtrar solo aprobados
        if 'aprobado' in df.columns:
            return df[df['aprobado'].astype(str).str.upper().str.contains('SI')].to_dict(orient='records')
        return []
    except Exception as e:
        return []

TODOS_LOS_PSICOLOGOS = cargar_especialistas()

# Preparamos el texto del directorio para que Gemini lo lea
TEXTO_DIRECTORIO = ""
CIUDADES_DISPONIBLES = ["Todas"]
if TODOS_LOS_PSICOLOGOS:
    CIUDADES_DISPONIBLES += sorted(list(set(p.get('ciudad', '').title() for p in TODOS_LOS_PSICOLOGOS if p.get('ciudad'))))
    TEXTO_DIRECTORIO = "\n".join([f"- {p.get('nombre')} ({p.get('especialidad')}) en {p.get('ciudad')}" for p in TODOS_LOS_PSICOLOGOS])

# ==========================================
# 🔐 3. LOGIN (ESTILO ZEN + SPLINE)
# ==========================================
if not st.session_state.usuario_activo:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🔐 Quantum Mind Access")
        
        # Animación Spline (Cerebro/Abstracto)
        try: components.iframe("https://my.spline.design/claritystream-Vcf5uaN9MQgIR4VGFA5iU6Es/", height=300)
        except: pass
        
        # Audio Zen de fondo (Loop)
        st.audio("https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3", start_time=0, autoplay=True)
        
        # Formulario
        with st.form("login_form"):
            st.info("🔑 Clave de Acceso para Invitados: **DEMO**")
            c = st.text_input("Clave de Acceso:", type="password")
            submitted = st.form_submit_button("Entrar a Sesión")
            
            if submitted:
                clave_limpia = c.strip()
                # Verificar DEMO o claves en Secrets
                es_demo = clave_limpia.upper() == "DEMO"
                es_valida = clave_limpia in ACCESO_KEYS
                
                if es_demo or es_valida:
                    nombre = "Visitante" if es_demo else ACCESO_KEYS[clave_limpia]
                    st.session_state.usuario_activo = nombre
                    st.session_state.visitas_contador += 1 # Contar visita al entrar
                    st.rerun()
                else:
                    st.error("⛔ Acceso Denegado")
    st.stop()

# ==========================================
# 🔊 4. MOTORES DE AUDIO
# ==========================================
def generar_audio_gtts(texto):
    try:
        tts = gTTS(text=texto, lang='es')
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp.getvalue()
    except: return None

def transcribir_google(audio_widget):
    if not audio_widget: return None
    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio_widget) as source:
            r.adjust_for_ambient_noise(source)
            return r.recognize_google(r.record(source), language="es-MX")
    except: return None

# ==========================================
# 🏠 5. APP PRINCIPAL (LAYOUT COMPLETO)
# ==========================================

# --- BARRA LATERAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3062/3062634.png", width=50) # Icono cerebro simple
    st.title(f"Hola, {st.session_state.usuario_activo}")
    st.caption(f"👀 Visitas Totales: **{st.session_state.visitas_contador:,}**")
    
    st.markdown("---")
    st.markdown("### 🧠 Modo de Terapia")
    st.session_state.modo_terapia = st.radio("Selecciona:", ["Escucha Empática", "Consejo Práctico"], index=0)
    
    if st.session_state.modo_terapia == "Escucha Empática":
        st.info("👂 **Modo Escucha:** Solo validaré tus emociones. Sin juicios ni tareas.")
    else:
        st.warning("💡 **Modo Consejo:** Te daré pasos concretos y herramientas.")
        
    st.markdown("---")
    st.markdown("### 🚑 Directorio")
    ciudad_filtro = st.selectbox("Buscar especialista en:", CIUDADES_DISPONIBLES)
    
    if st.button("🔍 Ver Especialistas"):
        filtrados = [p for p in TODOS_LOS_PSICOLOGOS if ciudad_filtro == "Todas" or p.get('ciudad', '').title() == ciudad_filtro]
        if filtrados:
            for p in filtrados:
                st.markdown(f"**{p['nombre']}**")
                st.caption(f"{p['especialidad']} - {p['ciudad']}")
                st.markdown("---")
        else:
            st.write("No hay especialistas en esta zona aún.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🔒 Cerrar Sesión"):
        st.session_state.usuario_activo = None
        st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("Quantum Mind 🧠")
st.caption(f"Sesión activa: **{st.session_state.modo_terapia}**")

# Historial de Chat
for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "audio" in msg: st.audio(msg["audio"], format="audio/mp3")

# --- ZONA DE INPUT (FIJA ABAJO) ---
st.markdown("---")
st.caption("🎙️ Usa el micrófono o escribe abajo:")

input_audio = st.audio_input(" ", key="chat_mic")
input_text = st.chat_input("Escribe aquí lo que sientes...")

# LÓGICA
prompt_user = None
es_audio = False

if input_audio:
    es_audio = True
    trans = transcribir_google(input_audio)
    if trans: prompt_user = trans
elif input_text:
    prompt_user = input_text

if prompt_user:
    # 1. Usuario
    with st.chat_message("user"):
        st.markdown(f"{'🎙️ ' if es_audio else ''}{prompt_user}")
    st.session_state.mensajes.append({"role": "user", "content": f"{'🎙️ ' if es_audio else ''}{prompt_user}"})

    # 2. IA
    instruccion = ""
    contexto_directorio = ""
    
    # Inyectamos el directorio en el cerebro de la IA
    if "ayuda" in prompt_user.lower() or "psicólogo" in prompt_user.lower() or "especialista" in prompt_user.lower():
        contexto_directorio = f"\n[INFORMACIÓN DE RECURSOS: Si el usuario pide ayuda profesional, recomiéndale buscar en la barra lateral o menciona estos especialistas disponibles: {TEXTO_DIRECTORIO}]"

    if st.session_state.modo_terapia == "Escucha Empática":
        instruccion = f"Actúa como psicólogo empático. Solo valida emociones. NO aconsejes. Sé cálido.{contexto_directorio}"
    else:
        instruccion = f"Actúa como coach psicológico. Da soluciones prácticas y breves.{contexto_directorio}"

    # 3. Respuesta
    with st.chat_message("assistant"):
        with st.spinner("Procesando..."):
            try:
                res = model.generate_content(f"{instruccion} Usuario dice: '{prompt_user}'")
                texto_ia = res.text
                st.markdown(texto_ia)
                
                audio_bytes = None
                if es_audio:
                    audio_bytes = generar_audio_gtts(texto_ia)
                    if audio_bytes: st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                
                msg = {"role": "assistant", "content": texto_ia}
                if audio_bytes: msg["audio"] = audio_bytes
                st.session_state.mensajes.append(msg)
            except Exception as e:
                st.error(f"Error de conexión: {e}")
