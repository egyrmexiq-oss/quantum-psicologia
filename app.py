import streamlit as st
import google.generativeai as genai
import requests
import time
import speech_recognition as sr  # Asegúrate de que esto siga instalado

# ==========================================
# ⚙️ 1. CONFIGURACIÓN Y ESTILOS
# ==========================================
st.set_page_config(page_title="Quantum Mind Access", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    /* Hacemos el reproductor de audio más grande para accesibilidad */
    audio { width: 100%; height: 60px; }
    /* Estilo para el contenedor de Login */
    .login-container {
        text-align: center;
        padding: 50px;
        background-color: #161B22;
        border-radius: 20px;
        margin-top: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

# Inicializar Estado de Sesión
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []
if "usuario_activo" not in st.session_state:
    st.session_state.usuario_activo = None

# Configurar API Keys
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")
ELEVEN_KEY = st.secrets.get("ELEVENLABS_API_KEY")
ACCESO_KEYS = st.secrets.get("access_keys", {})

# Configurar Gemini
#if GOOGLE_API_KEY:
    #genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
#else:
    #st.error("Falta la GOOGLE_API_KEY")
    #st.stop()

# ==========================================
# 🔊 2. FUNCIONES DE MOTOR (VOZ Y TEXTO)
# ==========================================

def texto_a_voz_elevenlabs(texto):
    """Genera audio con ElevenLabs"""
    if not ELEVEN_KEY: return None
    url = "https://api.elevenlabs.io/v1/text-to-speech/jsCqWAovK2LkecY7zXl4" # Voz Freya
    headers = { "xi-api-key": ELEVEN_KEY, "Content-Type": "application/json" }
    data = { "text": texto[:400], "model_id": "eleven_multilingual_v2" }
    try:
        response = requests.post(url, json=data, headers=headers)
        return response.content if response.status_code == 200 else None
    except: return None

def transcribir_audio(audio_file):
    """Convierte audio a texto usando SpeechRecognition"""
    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = r.record(source)
            # Intentamos español, si falla, no rompe la app
            texto = r.recognize_google(audio_data, language="es-MX")
            return texto
    except Exception as e:
        st.warning(f"No pude entender el audio: {e}")
        return None

def limpiar_texto_clave(texto):
    """Limpia el texto para comparar contraseñas (quita puntos, mayúsculas, etc)"""
    if not texto: return ""
    # Quita puntos, comas y espacios extra, y lo hace minúscula
    return texto.lower().replace(".", "").replace(",", "").strip()

# ==========================================
# 🔐 3. LÓGICA DE LOGIN (PORTERO)
# ==========================================

if not st.session_state.usuario_activo:
    # --- PANTALLA DE ACCESO ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-container'><h1>Quantum Mind 🧠</h1><p>Acceso por Voz o Texto</p></div>", unsafe_allow_html=True)
        
        # INPUT 1: MICROFONO DE ACCESO
        st.markdown("### 🎙️ Opción A: Di tu clave")
        audio_login = st.audio_input("Toca para hablar (Di 'Demo')", key="login_mic")
        
        # INPUT 2: TEXTO
        st.markdown("### ⌨️ Opción B: Escribe tu clave")
        texto_login = st.text_input("Clave de acceso", type="password", label_visibility="collapsed")
        btn_entrar = st.button("Entrar")

        # PROCESAR INTENTO DE LOGIN
        clave_detectada = None
        
        # Caso A: Usó Voz
        if audio_login:
            with st.spinner("Verificando voz..."):
                transcripcion = transcribir_audio(audio_login)
                if transcripcion:
                    st.info(f"Escuché: '{transcripcion}'")
                    clave_detectada = limpiar_texto_clave(transcripcion)
        
        # Caso B: Usó Texto
        if btn_entrar and texto_login:
            clave_detectada = limpiar_texto_clave(texto_login)

        # VERIFICACIÓN FINAL
        if clave_detectada:
            # Buscamos si la clave está en los secrets (comparando en minúsculas)
            # Convertimos las llaves del secret a minusculas para comparar
            llaves_validas = {k.lower(): v for k, v in ACCESO_KEYS.items()}
            
            if clave_detectada in llaves_validas:
                st.session_state.usuario_activo = llaves_validas[clave_detectada]
                st.success(f"¡Bienvenido, {st.session_state.usuario_activo}!")
                
                # Feedback auditivo de éxito (Opcional)
                bienvenida_audio = texto_a_voz_elevenlabs(f"Bienvenido al sistema, {st.session_state.usuario_activo}. Te escucho.")
                if bienvenida_audio:
                    st.audio(bienvenida_audio, format="audio/mp3", autoplay=True)
                
                time.sleep(2) # Dar tiempo a escuchar
                st.rerun() # 🚀 RECARGAR PARA ENTRAR A LA APP
            else:
                st.error(f"⛔ Acceso denegado. '{clave_detectada}' no es una clave válida.")

    st.stop() # 🛑 DETIENE EL CÓDIGO AQUÍ SI NO HA ENTRADO

# ==========================================
# 🏠 4. APP PRINCIPAL (SOLO SI YA ENTRÓ)
# ==========================================

st.sidebar.title(f"Hola, {st.session_state.usuario_activo}")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state.usuario_activo = None
    st.rerun()

st.title("Quantum Mind 🧠")
st.caption("Tu espacio seguro. Habla con libertad.")

# --- ZONA DE AUDIO (ACCESIBILIDAD) ---
audio_usuario = st.audio_input("🎤 Toca para hablar (Modo Terapia)", key="chat_mic")

# --- HISTORIAL ---
for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])
        if "audio" in mensaje:
            st.audio(mensaje["audio"], format="audio/mp3")

# --- PROCESAMIENTO ---
pregunta = None
modo = "texto"

# 1. Voz
if audio_usuario:
    modo = "voz"
    transcripcion = transcribir_audio(audio_usuario)
    if transcripcion:
        pregunta = transcripcion
        # Mostrar lo que dijo el usuario
        with st.chat_message("user"):
            st.markdown(f"🎤 {pregunta}")
            st.session_state.mensajes.append({"role": "user", "content": f"🎤 {pregunta}"})

# 2. Texto
elif prompt := st.chat_input("Escribe aquí..."):
    modo = "texto"
    pregunta = prompt
    with st.chat_message("user"):
        st.markdown(pregunta)
        st.session_state.mensajes.append({"role": "user", "content": pregunta})

# 3. Respuesta IA
if pregunta:
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            prompt_sistema = f"Actúa como un psicólogo empático. El usuario dice: '{pregunta}'. Responde brevemente y con calidez."
            response = model.generate_content(prompt_sistema)
            texto_resp = response.text
            
            st.markdown(texto_resp)
            
            audio_bytes = None
            if modo == "voz":
                audio_bytes = texto_a_voz_elevenlabs(texto_resp)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
            
            msg = {"role": "assistant", "content": texto_resp}
            if audio_bytes: msg["audio"] = audio_bytes
            st.session_state.mensajes.append(msg)
