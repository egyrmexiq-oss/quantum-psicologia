import streamlit as st
#import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS
from io import BytesIO
import time
from openai import OpenAI

# ==========================================
# ⚙️ 1. CONFIGURACIÓN Y ESTILOS
# ==========================================
st.set_page_config(page_title="Quantum Mind", page_icon="🧠", layout="wide")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

MODEL_NAME = "gpt-4.1-mini"
MAX_TOKENS = 300
TEMPERATURE = 0.7
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    
    /* BARRA FIJA INFERIOR (ESTILO WHATSAPP) */
    .fixed-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #161B22;
        padding: 1rem;
        z-index: 999;
        border-top: 1px solid #30363D;
    }
    
    /* Espacio para que el chat no quede tapado */
    .block-container {
        padding-bottom: 120px;
    }
    
    /* Login Box */
    .login-box { 
        padding: 40px; background-color: #161B22; 
        border-radius: 15px; border: 1px solid #30363D; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIÓN DE SECRETOS (BLINDADA) ---
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    # Intentamos leer las claves, si falla, usamos un fallback seguro
    ACCESO_KEYS = st.secrets.get("access_keys", {"demo": "Usuario Demo"})
except Exception as e:
    st.error(f"Error de configuración de Secretos: {e}")
    st.stop()

# Inicializar Estado
if "mensajes" not in st.session_state: st.session_state.mensajes = []
if "usuario_activo" not in st.session_state: st.session_state.usuario_activo = None
if "modo_terapia" not in st.session_state: st.session_state.modo_terapia = "Escucha Empática"

# Configurar Gemini
#genai.configure(api_key=GOOGLE_API_KEY)
#model = genai.GenerativeModel('gemini-2.5-flash')

# ==========================================
# 🔊 2. MOTORES DE VOZ (SOLO GOOGLE GRATIS)
# ==========================================

def generar_audio_gtts(texto):
    """Genera audio usando Google Text-to-Speech (Gratis y Robusto)"""
    try:
        tts = gTTS(text=texto, lang='es')
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp.getvalue()
    except Exception as e:
        return None

def transcribir_google(audio_widget):
    """Convierte Voz a Texto"""
    if not audio_widget: return None
    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio_widget) as source:
            # Ajustamos ruido ambiental para mejorar precisión
            r.adjust_for_ambient_noise(source) 
            return r.recognize_google(r.record(source), language="es-MX")
    except: return None

# ==========================================
# 🔐 3. LOGIN (PORTERO)
# ==========================================

if not st.session_state.usuario_activo:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-box'><h1>Quantum Mind 🧠</h1><p>Bienvenido</p></div>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🎙️ Voz", "⌨️ Texto"])
        clave = None
        
        with tab1:
            st.info("Di 'Demo'")
            aud = st.audio_input("Toca para hablar", key="login_mic")
            if aud:
                with st.spinner("Escuchando..."):
                    txt = transcribir_google(aud)
                    if txt:
                        st.success(f"Escuché: {txt}")
                        clave = txt.strip().lower().replace(".", "")
                    else:
                        st.warning("No pude entender. Intenta de nuevo.")

        with tab2:
            txt_in = st.text_input("Clave", type="password")
            if st.button("Entrar"): clave = txt_in.strip().lower()

        # Validación
        if clave:
            # Normalizamos claves del secrets a minúsculas para comparar
            validas = {k.lower(): v for k, v in ACCESO_KEYS.items()}
            
            # Corrección fonética común
            if clave == "demos": clave = "demo"
            
            if clave in validas:
                st.session_state.usuario_activo = validas[clave]
                st.rerun()
            else:
                st.error(f"Clave incorrecta: {clave}")
    st.stop()

# ==========================================
# 🏠 4. APP PRINCIPAL (CON FOOTER FIJO)
# ==========================================

# SIDEBAR
with st.sidebar:
    st.title(f"Hola, {st.session_state.usuario_activo}")
    
    st.markdown("### ⚙️ Modo")
    modo = st.radio("Enfoque:", ["Escucha Empática", "Consejo Práctico"])
    st.session_state.modo_terapia = modo
    
    if modo == "Escucha Empática":
        st.caption("👂 Solo validación emocional.")
    else:
        st.caption("💡 Soluciones y pasos a seguir.")

    if st.button("Salir"):
        st.session_state.usuario_activo = None
        st.rerun()

st.title("Quantum Mind 🧠")
st.caption(f"Modo: {st.session_state.modo_terapia}")

# --- HISTORIAL DE CHAT (Zona Superior) ---
# Mostramos todos los mensajes
for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "audio" in msg: st.audio(msg["audio"], format="audio/mp3")

# --- BARRA DE ENTRADA (FIXED FOOTER) ---
# Usamos un contenedor al final para simular la barra fija visualmente
st.markdown("---")

col_audio, col_texto = st.columns([1, 4])
with col_audio:
    input_audio = st.audio_input("🎙️", key="chat_mic")
with col_texto:
    input_text = st.chat_input("Escribe aquí...")

# LÓGICA DE PROCESAMIENTO
prompt_user = None
es_audio = False

if input_audio:
    es_audio = True
    trans = transcribir_google(input_audio)
    if trans: prompt_user = trans

elif input_text:
    prompt_user = input_text

# CEREBRO Y RESPUESTA
if prompt_user:
    # 1. Mostrar Usuario
    with st.chat_message("user"):
        if es_audio: st.markdown(f"🎤 {prompt_user}")
        else: st.markdown(prompt_user)
    
    st.session_state.mensajes.append({"role": "user", "content": f"{'🎤 ' if es_audio else ''}{prompt_user}"})

    # 2. Instrucción IA
    instruccion = ""
    if st.session_state.modo_terapia == "Escucha Empática":
        instruccion = "Solo valida emociones. Di 'te entiendo', 'es válido'. NO des consejos. Haz una pregunta suave."
    else:
        instruccion = "Sé un coach proactivo. Da 2 pasos prácticos o soluciones concretas. Sé breve."

    # 3. Generar
    with st.chat_message("assistant"):
        with st.spinner("..."):
            try:
                # Generar Texto
                full_prompt = f"Actúa como psicólogo. {instruccion}. Usuario: '{prompt_user}'. Respuesta muy breve."
                res = model.generate_content(full_prompt)
                texto_ia = res.text
                st.markdown(texto_ia)
                
                # Generar Audio (Solo si usó voz)
                audio_bytes = None
                if es_audio:
                    # Usamos gTTS (Google) - GRATIS y FIABLE
                    audio_bytes = generar_audio_gtts(texto_ia)
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                
                # Guardar
                msg = {"role": "assistant", "content": texto_ia}
                if audio_bytes: msg["audio"] = audio_bytes
                st.session_state.mensajes.append(msg)
                
            except Exception as e:
                st.error(f"Error: {e}")
                
            except Exception as e:
                st.error(f"Error: {e}")
