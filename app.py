import streamlit as st
import google.generativeai as genai
import requests
import time
import speech_recognition as sr # 🔙 VOLVEMOS A LA LIBRERÍA QUE FUNCIONABA

# ==========================================
# ⚙️ 1. CONFIGURACIÓN Y ESTILOS
# ==========================================
st.set_page_config(page_title="Quantum Mind", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    audio { width: 100%; height: 50px; }
    .login-container {
        text-align: center; padding: 40px; background-color: #161B22;
        border-radius: 20px; margin-top: 40px; border: 1px solid #30363D;
    }
    section[data-testid="stSidebar"] { background-color: #161B22; }
    </style>
    """, unsafe_allow_html=True)

# Inicializar Estado
if "mensajes" not in st.session_state: st.session_state.mensajes = []
if "usuario_activo" not in st.session_state: st.session_state.usuario_activo = None

# Configurar APIs
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")
ELEVEN_KEY = st.secrets.get("ELEVENLABS_API_KEY")
ACCESO_KEYS = st.secrets.get("access_keys", {})

# 🧠 CEREBRO GEMINI (Usamos 1.5-Flash que es el oficial y estable)
#if GOOGLE_API_KEY:
    #genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')
#else:
    #st.error("⚠️ Falta la GOOGLE_API_KEY en Secrets.")
    #st.stop()

# ==========================================
# 🔊 2. FUNCIONES DE MOTOR (VOZ PRECISA)
# ==========================================

def texto_a_voz_elevenlabs(texto):
    """Genera audio con ElevenLabs"""
    if not ELEVEN_KEY: return None
    url = "https://api.elevenlabs.io/v1/text-to-speech/jsCqWAovK2LkecY7zXl4"
    headers = { "xi-api-key": ELEVEN_KEY, "Content-Type": "application/json" }
    data = { "text": texto[:400], "model_id": "eleven_multilingual_v2" }
    try:
        response = requests.post(url, json=data, headers=headers)
        return response.content if response.status_code == 200 else None
    except: return None

def transcribir_con_google(audio_widget):
    """
    Usa la librería SpeechRecognition (Google Speech API)
    Es mucho más precisa para comandos cortos como 'Demo'.
    """
    if audio_widget is None: return None
    
    r = sr.Recognizer()
    try:
        # Convertimos el audio de Streamlit a un formato que SR entienda
        with sr.AudioFile(audio_widget) as source:
            audio_data = r.record(source)
            # Reconocimiento en Español
            texto = r.recognize_google(audio_data, language="es-MX")
            return texto
    except sr.UnknownValueError:
        return None # No entendió nada
    except Exception as e:
        st.warning(f"Error de audio: {e}")
        return None

# ==========================================
# 🔐 3. LÓGICA DE LOGIN (PORTERO)
# ==========================================

if not st.session_state.usuario_activo:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-container'><h1>Quantum Mind 🧠</h1><p>Espacio Seguro</p></div>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🎙️ Voz", "⌨️ Texto"])
        clave_detectada = None
        
        with tab1:
            st.info("💡 Di 'Demo' claro y fuerte.")
            audio_login = st.audio_input("Toca para hablar", key="login_mic")
            
            if audio_login:
                with st.spinner("Escuchando..."):
                    # Usamos la transcripción "Antigua" que funcionaba bien
                    transcripcion = transcribir_con_google(audio_login)
                    
                    if transcripcion:
                        st.success(f"Escuché: '{transcripcion}'")
                        # Limpiamos el texto (quitamos puntos, mayúsculas)
                        clave_detectada = transcripcion.strip().lower().replace(".", "")
                    else:
                        st.warning("No te entendí bien. Intenta acercarte más.")

        with tab2:
            texto_login = st.text_input("Clave de acceso", type="password")
            if st.button("Entrar"): 
                clave_detectada = texto_login.strip().lower()

        # Verificación
        if clave_detectada:
            llaves_validas = {k.lower(): v for k, v in ACCESO_KEYS.items()}
            
            # Truco: Si escuchó "sol" o "demos", intentamos ser flexibles
            if clave_detectada in llaves_validas:
                st.session_state.usuario_activo = llaves_validas[clave_detectada]
                st.success("¡Acceso Correcto!")
                time.sleep(1)
                st.rerun()
            elif clave_detectada == "demos": # Corrección común de voz
                st.session_state.usuario_activo = llaves_validas["demo"]
                st.rerun()
            else:
                st.error(f"⛔ Clave incorrecta: '{clave_detectada}'")
    st.stop()

# ==========================================
# 🏠 4. APP PRINCIPAL
# ==========================================

with st.sidebar:
    st.title(f"Hola, {st.session_state.usuario_activo}")
    profundidad = st.radio("Profundidad:", ["Escucha Breve", "Apoyo Emocional"])
    if st.button("🧹 Nueva Sesión"):
        st.session_state.mensajes = []
        st.rerun()
    if st.button("🔒 Salir"):
        st.session_state.usuario_activo = None
        st.rerun()

st.title("Quantum Mind 🧠")
st.caption(f"Modo: {profundidad}. Tu espacio seguro.")

# INPUT HÍBRIDO
with st.container():
    audio_chat = st.audio_input("🎤 Toca para hablar (Respuesta con voz)", key="chat_mic")

# HISTORIAL
for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "audio" in msg: st.audio(msg["audio"], format="audio/mp3")

# LÓGICA
pregunta_usuario = None
es_audio = False

# 1. Audio
if audio_chat:
    es_audio = True
    # Transcribir con Google (Más preciso)
    texto_voz = transcribir_con_google(audio_chat)
    if texto_voz:
        pregunta_usuario = texto_voz
    else:
        st.warning("No se escuchó audio. Intenta de nuevo.")

# 2. Texto
elif prompt := st.chat_input("Escribe aquí..."):
    pregunta_usuario = prompt
    with st.chat_message("user"): st.markdown(prompt)
    st.session_state.mensajes.append({"role": "user", "content": prompt})

# 3. Respuesta
if pregunta_usuario and (es_audio or prompt):
    if es_audio:
         with st.chat_message("user"): st.markdown(f"🎤 *{pregunta_usuario}*")
         st.session_state.mensajes.append({"role": "user", "content": f"🎤 {pregunta_usuario}"})
    
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            
            # Prompt para Gemini 1.5
            prompt_sistema = f"Actúa como psicólogo empático. El usuario dice: '{pregunta_usuario}'. Responde brevemente y con calidez."
            
            try:
                response = model.generate_content(prompt_sistema)
                respuesta_texto = response.text
                
                st.markdown(respuesta_texto)
                
                # Audio Salida
                audio_salida = None
                if es_audio:
                    audio_salida = texto_a_voz_elevenlabs(respuesta_texto)
                    if audio_salida:
                        st.audio(audio_salida, format="audio/mp3", autoplay=True)
                
                msg = {"role": "assistant", "content": respuesta_texto}
                if audio_salida: msg["audio"] = audio_salida
                st.session_state.mensajes.append(msg)
                
            except Exception as e:
                st.error(f"Error de IA: {e}")
