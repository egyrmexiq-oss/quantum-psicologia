import streamlit as st
import google.generativeai as genai
import requests
import time

# ==========================================
# ⚙️ 1. CONFIGURACIÓN Y ESTILOS
# ==========================================
st.set_page_config(page_title="Quantum Mind", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    audio { width: 100%; height: 50px; }
    /* Contenedor de Login */
    .login-container {
        text-align: center; padding: 50px; background-color: #161B22;
        border-radius: 20px; margin-top: 50px; border: 1px solid #30363D;
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

# Configurar Gemini (CORRECCIÓN: Usamos 1.5-flash que es el ESTÁNDAR)
#if GOOGLE_API_KEY:
    #genai.configure(api_key=GOOGLE_API_KEY)
    #try:
        # Usamos 1.5-flash. La versión 2.5 no existe públicamente aún y causa error.
model = genai.GenerativeModel('gemini-1.5-flash')
    #except Exception as e:
        #st.error(f"Error configurando modelo: {e}")
#else:
    #st.error("⚠️ Falta la GOOGLE_API_KEY en Secrets.")
    #st.stop()

# ==========================================
# 🔊 2. FUNCIONES (MOTOR)
# ==========================================

def texto_a_voz_elevenlabs(texto):
    """Genera audio con ElevenLabs"""
    if not ELEVEN_KEY: return None
    url = "https://api.elevenlabs.io/v1/text-to-speech/jsCqWAovK2LkecY7zXl4"
    headers = { "xi-api-key": ELEVEN_KEY, "Content-Type": "application/json" }
    data = { "text": texto[:400], "model_id": "eleven_multilingual_v2" }
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            # Si falla ElevenLabs, no rompemos la app, solo devolvemos None
            print(f"Error ElevenLabs: {response.text}")
            return None
    except: return None

def procesar_entrada_gemini(texto=None, audio_bytes=None, contexto=""):
    """Envía Texto o Audio a Gemini"""
    try:
        prompt_sistema = f"Actúa como psicólogo empático. {contexto}. Responde brevemente (máximo 2 frases) y con calidez."
        
        if audio_bytes:
            # Enviar AUDIO directamente
            response = model.generate_content([
                prompt_sistema + " (El usuario habla por audio, escúchalo):",
                {"mime_type": "audio/wav", "data": audio_bytes}
            ])
        else:
            # Enviar TEXTO
            response = model.generate_content(f"{prompt_sistema} El usuario dice: {texto}")
            
        return response.text
    except Exception as e:
        return f"Lo siento, tuve un problema técnico momentáneo ({str(e)}). ¿Podrías repetirlo?"

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
            audio_login = st.audio_input("Di tu clave (Ej: 'Demo')", key="login_mic")
            if audio_login:
                bytes_data = audio_login.read()
                try:
                    res = model.generate_content(["Transcribe SOLO la clave que se escucha:", {"mime_type": "audio/wav", "data": bytes_data}])
                    clave_detectada = res.text.strip().lower().replace(".","")
                    st.info(f"Escuché: {clave_detectada}")
                except: st.warning("No pude escuchar bien.")

        with tab2:
            texto_login = st.text_input("Clave de acceso", type="password")
            if st.button("Entrar"): clave_detectada = texto_login.strip().lower()

        if clave_detectada:
            llaves_validas = {k.lower(): v for k, v in ACCESO_KEYS.items()}
            if clave_detectada in llaves_validas:
                st.session_state.usuario_activo = llaves_validas[clave_detectada]
                st.success("¡Acceso Correcto!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("⛔ Clave incorrecta.")
    st.stop()

# ==========================================
# 🏠 4. APP PRINCIPAL
# ==========================================

with st.sidebar:
    st.title(f"Hola, {st.session_state.usuario_activo}")
    st.markdown("### ⚙️ Preferencias")
    profundidad = st.radio("Profundidad:", ["Escucha Breve", "Apoyo Emocional", "Orientación Teórica"])
    st.markdown("---")
    if st.button("🧹 Nueva Sesión"):
        st.session_state.mensajes = []
        st.rerun()
    st.markdown("---")
    if st.button("🔒 Salir"):
        st.session_state.usuario_activo = None
        st.rerun()

# ZONA PRINCIPAL
st.title("Quantum Mind 🧠")
st.caption(f"Modo: {profundidad}. Tu espacio seguro.")

# --- INPUT HÍBRIDO ---
# Usamos un contenedor para separar visualmente el input de voz
with st.container():
    audio_chat = st.audio_input("🎤 Toca para hablar (Respuesta con voz)", key="chat_mic")

# --- HISTORIAL ---
for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "audio" in msg: st.audio(msg["audio"], format="audio/mp3")

# --- LÓGICA DE PROCESAMIENTO ---
pregunta_usuario = None
es_audio = False

# 1. Detectar Audio Nuevo
if audio_chat:
    es_audio = True
    pregunta_usuario = "Mensaje de voz recibido"

# 2. Detectar Texto Nuevo
elif prompt := st.chat_input("Escribe aquí..."):
    pregunta_usuario = prompt
    with st.chat_message("user"): st.markdown(prompt)
    st.session_state.mensajes.append({"role": "user", "content": prompt})

# 3. Respuesta
if pregunta_usuario and (es_audio or prompt):
    if es_audio:
         with st.chat_message("user"): st.markdown("🎤 *Mensaje de voz enviado*")
    
    with st.chat_message("assistant"):
        with st.spinner("Procesando..."):
            
            # PROCESAMIENTO GEMINI
            if es_audio:
                # Importante: Leemos los bytes y reiniciamos el puntero por seguridad
                bytes_audio = audio_chat.read() 
                contexto = f"El usuario eligió el modo: {profundidad}"
                respuesta_texto = procesar_entrada_gemini(audio_bytes=bytes_audio, contexto=contexto)
            else:
                contexto = f"El usuario eligió el modo: {profundidad}"
                respuesta_texto = procesar_entrada_gemini(texto=pregunta_usuario, contexto=contexto)
            
            st.markdown(respuesta_texto)
            
            # PROCESAMIENTO ELEVENLABS (AUDIO OUTPUT)
            audio_salida = None
            if es_audio: # Solo gastamos créditos de voz si el usuario usó voz
                audio_salida = texto_a_voz_elevenlabs(respuesta_texto)
                if audio_salida:
                    st.audio(audio_salida, format="audio/mp3", autoplay=True)
            
            # GUARDAR EN HISTORIAL
            msg = {"role": "assistant", "content": respuesta_texto}
            if audio_salida: msg["audio"] = audio_salida
            st.session_state.mensajes.append(msg)
            st.session_state.mensajes.append(msg)
