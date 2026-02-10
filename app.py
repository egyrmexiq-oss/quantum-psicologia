import streamlit as st
import google.generativeai as genai
import requests
import time
import speech_recognition as sr
from gtts import gTTS
from io import BytesIO

# ==========================================
# ⚙️ 1. CONFIGURACIÓN Y ESTILOS PRO
# ==========================================
st.set_page_config(page_title="Quantum Mind", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    
    /* ESTILO PARA FIJAR LA BARRA DE ENTRADA AL FONDO */
    .fixed-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #161B22;
        padding: 20px 10px 10px 10px;
        z-index: 999;
        border-top: 1px solid #30363D;
        text-align: center;
    }
    
    /* Ajuste para que el chat no quede tapado por la barra fija */
    .main-content {
        padding-bottom: 150px; 
    }
    
    /* Estilos Login */
    .login-box { 
        padding: 30px; background-color: #161B22; 
        border-radius: 15px; border: 1px solid #30363D; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

if "mensajes" not in st.session_state: st.session_state.mensajes = []
if "usuario_activo" not in st.session_state: st.session_state.usuario_activo = None
if "modo_terapia" not in st.session_state: st.session_state.modo_terapia = "Escucha Empática" # Default

# APIs
#GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")
#ELEVEN_KEY = st.secrets.get("ELEVENLABS_API_KEY")
#ACCESO_KEYS = st.secrets.get("access_keys", {})

#if GOOGLE_API_KEY:
    #genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
#else:
    #st.stop()

# ==========================================
# 🔊 2. MOTORES DE VOZ
# ==========================================
def generar_audio_inteligente(texto):
    # 1. ElevenLabs
    if ELEVEN_KEY:
        url = "https://api.elevenlabs.io/v1/text-to-speech/jsCqWAovK2LkecY7zXl4"
        headers = { "xi-api-key": ELEVEN_KEY, "Content-Type": "application/json" }
        data = { "text": texto[:400], "model_id": "eleven_multilingual_v2" }
        try:
            r = requests.post(url, json=data, headers=headers)
            if r.status_code == 200: return r.content
        except: pass 
    # 2. Google (Respaldo)
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
            aud = st.audio_input("Hablar", key="login_mic")
            if aud:
                txt = transcribir_google(aud)
                if txt:
                    st.success(f"Escuché: {txt}")
                    clave = txt.strip().lower().replace(".","")
        with tab2:
            txt_in = st.text_input("Clave", type="password")
            if st.button("Entrar"): clave = txt_in.strip().lower()

        if clave:
            validas = {k.lower(): v for k, v in ACCESO_KEYS.items()}
            if clave == "demos": clave = "demo"
            if clave in validas:
                st.session_state.usuario_activo = validas[clave]
                st.rerun()
            else: st.error("Incorrecto")
    st.stop()

# ==========================================
# 🏠 4. APP PRINCIPAL (LAYOUT INVERTIDO)
# ==========================================

# SIDEBAR (Configuración)
with st.sidebar:
    st.title(f"Hola, {st.session_state.usuario_activo}")
    
    # Selector de Modo (Aquí está la magia de la diferencia)
    modo_seleccionado = st.radio("Enfoque de la Sesión:", ["Escucha Empática", "Consejo Práctico"])
    st.session_state.modo_terapia = modo_seleccionado
    
    st.info(f"Modo actual: **{modo_seleccionado}**")
    if modo_seleccionado == "Escucha Empática":
        st.caption("👂 Solo te escucharé y validaré tus sentimientos. No te daré tareas.")
    else:
        st.caption("💡 Te daré tips, herramientas y pasos a seguir.")

    if st.button("Salir"):
        st.session_state.usuario_activo = None
        st.rerun()

st.title("Quantum Mind 🧠")
st.caption(f"Modo: {st.session_state.modo_terapia}")

# --- AQUI PINTAMOS EL HISTORIAL (ARRIBA) ---
# Usamos un contenedor para empujar el contenido hacia arriba y dejar espacio abajo
chat_container = st.container()
with chat_container:
    for msg in st.session_state.mensajes:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "audio" in msg: st.audio(msg["audio"], format="audio/mp3")
    
    # Espaciador invisible para que el último mensaje no quede tapado por el footer
    st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)


# --- AQUI ESTÁ LA BARRA FIJA (ABAJO) ---
# Usamos st.bottom_container() si tu versión lo soporta, o un contenedor simple al final
# Como tienes Streamlit nuevo, vamos a intentar ponerlo al final del flujo script.

st.markdown("---") # Separador visual

# LÓGICA DE INPUT
input_audio = None
input_text = None

# Creamos columnas para organizar Texto y Audio abajo
col_audio, col_texto = st.columns([1, 4])

with col_audio:
    input_audio = st.audio_input("🎙️", key="chat_mic")

with col_texto:
    input_text = st.chat_input("Escribe algo...")

# PROCESAMIENTO
prompt_user = None
es_audio = False

if input_audio:
    es_audio = True
    trans = transcribir_google(input_audio)
    if trans: prompt_user = trans
    else: st.warning("No se escuchó nada.")

elif input_text:
    prompt_user = input_text

# CEREBRO Y RESPUESTA
if prompt_user:
    # 1. Mostrar mensaje usuario
    if es_audio:
        with chat_container.chat_message("user"): st.markdown(f"🎤 {prompt_user}")
        st.session_state.mensajes.append({"role": "user", "content": f"🎤 {prompt_user}"})
    else:
        with chat_container.chat_message("user"): st.markdown(prompt_user)
        st.session_state.mensajes.append({"role": "user", "content": prompt_user})

    # 2. DEFINIR PERSONALIDAD SEGÚN MODO
    instruccion_modo = ""
    if st.session_state.modo_terapia == "Escucha Empática":
        instruccion_modo = "TU OBJETIVO: Solo valida las emociones. Usa frases como 'Entiendo', 'Debe ser duro'. NO des consejos ni soluciones. Solo acompaña y haz una pregunta corta para indagar más."
    else: # Consejo Práctico
        instruccion_modo = "TU OBJETIVO: Sé proactivo. Después de validar brevemente, da 2 o 3 pasos concretos, ejercicios o cambios de perspectiva accionables. Sé un coach amable."

    # 3. GENERAR
    with chat_container.chat_message("assistant"):
        with st.spinner("Conectando..."):
            try:
                full_prompt = f"Actúa como psicólogo. {instruccion_modo}. El usuario dice: '{prompt_user}'. Respuesta breve."
                res = model.generate_content(full_prompt)
                texto_ia = res.text
                
                st.markdown(texto_ia)
                
                audio_bytes = None
                if es_audio:
                    audio_bytes = generar_audio_inteligente(texto_ia)
                    if audio_bytes: 
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                
                msg = {"role": "assistant", "content": texto_ia}
                if audio_bytes: msg["audio"] = audio_bytes
                st.session_state.mensajes.append(msg)
                
            except Exception as e:
                st.error(f"Error: {e}")
