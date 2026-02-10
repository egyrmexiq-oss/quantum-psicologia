import streamlit as st
import google.generativeai as genai
import requests
import time
import speech_recognition as sr
from gtts import gTTS
from io import BytesIO

# ==========================================
# ⚙️ 1. CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Quantum Mind", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    audio { width: 100%; height: 50px; }
    .login-box { 
        padding: 30px; background-color: #161B22; 
        border-radius: 15px; border: 1px solid #30363D; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

if "mensajes" not in st.session_state: st.session_state.mensajes = []
if "usuario_activo" not in st.session_state: st.session_state.usuario_activo = None

# APIs
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")
ELEVEN_KEY = st.secrets.get("ELEVENLABS_API_KEY")
ACCESO_KEYS = st.secrets.get("access_keys", {})

#if GOOGLE_API_KEY:
    #genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')
#else:
    #st.error("Falta API Key")
    #st.stop()

# ==========================================
# 🔊 2. MOTORES DE VOZ (PREMIUM + RESPALDO)
# ==========================================

def generar_audio_inteligente(texto):
    """
    Intenta ElevenLabs (Premium). 
    Si falla, usa Google (Gratis). 
    ¡Nunca se queda callado!
    """
    # 1. INTENTO PREMIUM (ElevenLabs)
    if ELEVEN_KEY:
        url = "https://api.elevenlabs.io/v1/text-to-speech/jsCqWAovK2LkecY7zXl4"
        headers = { "xi-api-key": ELEVEN_KEY, "Content-Type": "application/json" }
        data = { "text": texto[:400], "model_id": "eleven_multilingual_v2" }
        try:
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                return response.content # ¡Éxito Premium!
            else:
                print(f"Fallo ElevenLabs: {response.text}") # Log interno
        except:
            pass 

    # 2. INTENTO RESPALDO (Google gTTS - Gratis)
    try:
        tts = gTTS(text=texto, lang='es')
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp.getvalue() # ¡Éxito Gratis!
    except Exception as e:
        st.error(f"Error total de audio: {e}")
        return None

def transcribir_google(audio_widget):
    if audio_widget is None: return None
    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio_widget) as source:
            audio_data = r.record(source)
            return r.recognize_google(audio_data, language="es-MX")
    except: return None

# ==========================================
# 🔐 3. LOGIN
# ==========================================

if not st.session_state.usuario_activo:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-box'><h1>Quantum Mind 🧠</h1><p>Espacio Seguro</p></div>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🎙️ Voz", "⌨️ Texto"])
        clave = None
        
        with tab1:
            st.info("Di 'Demo' fuerte y claro.")
            audio = st.audio_input("Hablar", key="login_mic")
            if audio:
                txt = transcribir_google(audio)
                if txt:
                    st.success(f"Escuché: {txt}")
                    clave = txt.strip().lower().replace(".","")
                else:
                    st.warning("No entendí. Intenta de nuevo.")

        with tab2:
            txt_in = st.text_input("Clave", type="password")
            if st.button("Entrar"): clave = txt_in.strip().lower()

        if clave:
            validas = {k.lower(): v for k, v in ACCESO_KEYS.items()}
            # Corrección de "Demos" plural
            if clave == "demos": clave = "demo"
            
            if clave in validas:
                st.session_state.usuario_activo = validas[clave]
                st.rerun()
            else:
                st.error("Clave incorrecta")
    st.stop()

# ==========================================
# 🏠 4. APP PRINCIPAL
# ==========================================

with st.sidebar:
    st.title(f"Hola, {st.session_state.usuario_activo}")
    modo = st.radio("Modo:", ["Escucha", "Consejo"])
    if st.button("Salir"):
        st.session_state.usuario_activo = None
        st.rerun()

st.title("Quantum Mind 🧠")
st.caption("Estoy escuchando...")

# INPUT
with st.container():
    audio_chat = st.audio_input("🎤 Toca para hablar", key="chat_mic")

# HISTORIAL
for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "audio" in msg: st.audio(msg["audio"], format="audio/mp3")

# PROCESAMIENTO
prompt_user = None
es_audio = False

if audio_chat:
    es_audio = True
    txt = transcribir_google(audio_chat)
    if txt: prompt_user = txt
    else: st.warning("Audio vacío o inaudible.")

elif txt_chat := st.chat_input("Escribe..."):
    prompt_user = txt_chat

if prompt_user and (es_audio or txt_chat):
    if es_audio:
         with st.chat_message("user"): st.markdown(f"🎤 *{prompt_user}*")
         st.session_state.mensajes.append({"role": "user", "content": f"🎤 {prompt_user}"})
    else:
        # Solo agregamos si es texto para no duplicar visualmente
        st.session_state.mensajes.append({"role": "user", "content": prompt_user})

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                # 1. GENERAR TEXTO
                res = model.generate_content(f"Actúa como psicólogo breve. Usuario dice: {prompt_user}")
                texto_ia = res.text
                st.markdown(texto_ia)
                
                # 2. GENERAR AUDIO (ROBUSTO)
                audio_bytes = None
                if es_audio:
                    # Aquí ocurre la magia: Si falla ElevenLabs, entra Google
                    audio_bytes = generar_audio_inteligente(texto_ia)
                    
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                    else:
                        st.error("Error de audio: No se pudo generar voz.")

                # 3. GUARDAR
                msg = {"role": "assistant", "content": texto_ia}
                if audio_bytes: msg["audio"] = audio_bytes
                st.session_state.mensajes.append(msg)
                
            except Exception as e:
                st.error(f"Error: {e}")
            except Exception as e:
                st.error(f"Error de IA: {e}")
