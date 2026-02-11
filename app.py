import streamlit as st
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS
from io import BytesIO
import time

# ==========================================
# ⚙️ 1. CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Quantum Mind", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .login-box { 
        padding: 40px; background-color: #161B22; 
        border-radius: 15px; border: 1px solid #30363D; text-align: center;
    }
    .block-container { padding-bottom: 140px; }
    </style>
    """, unsafe_allow_html=True)

# --- SECRETOS BLINDADOS ---
GOOGLE_API_KEY = None
ACCESO_KEYS = {"demo": "Usuario Demo"}

try:
    if "GOOGLE_API_KEY" in st.secrets:
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    if "access_keys" in st.secrets:
        ACCESO_KEYS = st.secrets["access_keys"]
except:
    pass

if not GOOGLE_API_KEY:
    st.error("⚠️ Error: Falta configurar GOOGLE_API_KEY en los Secrets.")
    st.stop()

# Inicializar
if "mensajes" not in st.session_state: st.session_state.mensajes = []
if "usuario_activo" not in st.session_state: st.session_state.usuario_activo = None
if "modo_terapia" not in st.session_state: st.session_state.modo_terapia = "Escucha Empática"

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# ==========================================
# 🔊 2. MOTORES
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
# 🔐 3. LOGIN
# ==========================================
if not st.session_state.usuario_activo:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-box'><h1>Quantum Mind 🧠</h1><p>Bienvenido</p></div>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🎙️ Voz", "⌨️ Texto"])
        clave = None
        
        with tab1:
            st.info("Di 'Demo'")
            aud = st.audio_input("Hablar", key="login_mic")
            if aud:
                txt = transcribir_google(aud)
                if txt:
                    st.success(f"Escuché: {txt}")
                    clave = txt.strip().lower().replace(".", "")
        
        with tab2:
            txt_in = st.text_input("Clave", type="password")
            if st.button("Entrar"): clave = txt_in.strip().lower()

        if clave:
            validas = {k.lower(): v for k, v in ACCESO_KEYS.items()}
            if clave == "demos": clave = "demo"
            if clave in validas:
                st.session_state.usuario_activo = validas[clave]
                st.rerun()
            else: st.error("Clave incorrecta")
    st.stop()

# ==========================================
# 🏠 4. APP PRINCIPAL
# ==========================================
with st.sidebar:
    st.title(f"Hola, {st.session_state.usuario_activo}")
    st.session_state.modo_terapia = st.radio("Modo:", ["Escucha Empática", "Consejo Práctico"])
    if st.button("Salir"):
        st.session_state.usuario_activo = None
        st.rerun()

st.title("Quantum Mind 🧠")
st.caption(f"Modo: {st.session_state.modo_terapia}")

# Historial
for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "audio" in msg: st.audio(msg["audio"], format="audio/mp3")

# INPUT ESTABLE (Sin columnas)
st.markdown("---")
st.caption("🎙️ Graba o escribe:")
input_audio = st.audio_input(" ", key="chat_mic")
input_text = st.chat_input("Escribe aquí...")

# Lógica
prompt = None
es_audio = False

if input_audio:
    es_audio = True
    trans = transcribir_google(input_audio)
    if trans: prompt = trans
elif input_text:
    prompt = input_text

if prompt:
    # Usuario
    with st.chat_message("user"):
        st.markdown(f"{'🎙️ ' if es_audio else ''}{prompt}")
    st.session_state.mensajes.append({"role": "user", "content": f"{'🎙️ ' if es_audio else ''}{prompt}"})

    # IA
    instruccion = "Solo valida emociones." if st.session_state.modo_terapia == "Escucha Empática" else "Da consejos breves."
    
    with st.chat_message("assistant"):
        with st.spinner("..."):
            try:
                res = model.generate_content(f"Actúa como psicólogo. {instruccion}. Usuario: '{prompt}'")
                texto = res.text
                st.markdown(texto)
                
                audio_bytes = None
                if es_audio:
                    audio_bytes = generar_audio_gtts(texto)
                    if audio_bytes: st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                
                msg = {"role": "assistant", "content": texto}
                if audio_bytes: msg["audio"] = audio_bytes
                st.session_state.mensajes.append(msg)
            except Exception as e: st.error(f"Error: {e}")
