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
    /* Estilo para el contenedor de Login */
    .login-container {
        text-align: center; padding: 50px; background-color: #161B22;
        border-radius: 20px; margin-top: 50px; border: 1px solid #30363D;
    }
    /* Sidebar styling */
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

# Configurar Gemini (Modelo Flash para rapidez y audio)
#if GOOGLE_API_KEY:
    #genai.configure(api_key=GOOGLE_API_KEY)
    # Usamos el modelo Flash que soporta audio nativo
model = genai.GenerativeModel('gemini-2.5-flash')
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
        return response.content if response.status_code == 200 else None
    except: return None

def procesar_entrada_gemini(texto=None, audio_bytes=None, contexto=""):
    """Envía Texto o Audio a Gemini y recibe respuesta"""
    try:
        prompt_sistema = f"Actúa como psicólogo empático. {contexto}. Responde brevemente y con calidez."
        
        if audio_bytes:
            # Enviar AUDIO directamente a Gemini (Multimodal)
            response = model.generate_content([
                prompt_sistema + " (El usuario te habla por audio, escúchalo y responde):",
                {"mime_type": "audio/wav", "data": audio_bytes}
            ])
        else:
            # Enviar TEXTO
            response = model.generate_content(f"{prompt_sistema} El usuario dice: {texto}")
            
        return response.text
    except Exception as e:
        return f"Error conectando con mi cerebro: {str(e)}"

# ==========================================
# 🔐 3. LÓGICA DE LOGIN (PORTERO)
# ==========================================

if not st.session_state.usuario_activo:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-container'><h1>Quantum Mind 🧠</h1><p>Espacio Seguro de Escucha</p></div>", unsafe_allow_html=True)
        
        # Opciones de Login
        tab1, tab2 = st.tabs(["🎙️ Voz", "⌨️ Texto"])
        
        clave_detectada = None
        
        with tab1:
            audio_login = st.audio_input("Di tu clave (Ej: 'Demo')", key="login_mic")
            if audio_login:
                # Usamos Gemini para "Oír" la clave
                bytes_data = audio_login.read()
                try:
                    res = model.generate_content(["Transcribe EXACTAMENTE solo lo que dice este audio:", {"mime_type": "audio/wav", "data": bytes_data}])
                    clave_detectada = res.text.strip().lower().replace(".","")
                    st.info(f"Escuché: {clave_detectada}")
                except: st.warning("No pude escuchar bien.")

        with tab2:
            texto_login = st.text_input("Clave de acceso", type="password")
            if st.button("Entrar"): clave_detectada = texto_login.strip().lower()

        # Validación
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
# 🏠 4. APP PRINCIPAL (CON BARRA LATERAL)
# ==========================================

# --- BARRA LATERAL RECUPERADA ---
with st.sidebar:
    st.title(f"Hola, {st.session_state.usuario_activo}")
    
    st.markdown("### ⚙️ Preferencias")
    profundidad = st.radio("Profundidad:", ["Escucha Breve", "Apoyo Emocional", "Orientación Teórica"])
    
    st.markdown("---")
    
    if st.button("🧹 Nueva Sesión"):
        st.session_state.mensajes = []
        st.rerun()
        
    st.markdown("---")
    st.markdown("### 🚑 Ayuda Profesional")
    ciudad = st.selectbox("Ciudad:", ["CDMX", "Monterrey", "Guadalajara", "Online"])
    if st.button("Encuentra Psicólogo"):
        st.info(f"Buscando especialistas en {ciudad}...")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🔒 Cerrar Sesión"):
        st.session_state.usuario_activo = None
        st.rerun()

# --- ZONA PRINCIPAL ---
st.title("Quantum Mind 🧠")
st.caption(f"Modo: {profundidad}. Tu espacio seguro.")

# Input de Voz Híbrido
audio_chat = st.audio_input("🎤 Toca para hablar (Te responderé con voz)", key="chat_mic")

# Historial
for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "audio" in msg: st.audio(msg["audio"], format="audio/mp3")

# Lógica de Respuesta
pregunta_usuario = None
es_audio = False

# 1. Si hay audio nuevo
if audio_chat:
    # IMPORTANTE: Streamlit recarga al usar audio, verificamos si ya procesamos este
    # (En MVP simple, procesamos siempre que no sea nulo)
    es_audio = True
    pregunta_usuario = "Audio del usuario" # Placeholder visual

# 2. Si hay texto
elif prompt := st.chat_input("Escribe aquí..."):
    pregunta_usuario = prompt
    with st.chat_message("user"): st.markdown(prompt)
    st.session_state.mensajes.append({"role": "user", "content": prompt})

# 3. Procesar y Responder
if pregunta_usuario and (es_audio or prompt):
    # Evitar repetición en bucle infinito (control simple)
    if es_audio:
         # Mostrar visualmente que se recibió audio
         with st.chat_message("user"): st.markdown("🎤 *Mensaje de voz enviado*")
    
    with st.chat_message("assistant"):
        with st.spinner("Escuchando y pensando..."):
            
            respuesta_texto = ""
            
            if es_audio:
                # ENVIAR AUDIO DIRECTO A GEMINI
                bytes_audio = audio_chat.read()
                contexto = f"El usuario eligió el modo: {profundidad}"
                respuesta_texto = procesar_entrada_gemini(audio_bytes=bytes_audio, contexto=contexto)
            else:
                # ENVIAR TEXTO
                contexto = f"El usuario eligió el modo: {profundidad}"
                respuesta_texto = procesar_entrada_gemini(texto=pregunta_usuario, contexto=contexto)
            
            st.markdown(respuesta_texto)
            
            # Generar Audio de Salida (Solo si el usuario usó voz)
            audio_salida = None
            if es_audio:
                audio_salida = texto_a_voz_elevenlabs(respuesta_texto)
                if audio_salida:
                    st.audio(audio_salida, format="audio/mp3", autoplay=True)
            
            # Guardar
            msg = {"role": "assistant", "content": respuesta_texto}
            if audio_salida: msg["audio"] = audio_salida
            st.session_state.mensajes.append(msg)
