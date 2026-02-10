import streamlit as st
import google.generativeai as genai
import requests
import time

# ==========================================
# ⚙️ 1. CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Quantum Mind", page_icon="🧠", layout="centered")

# Estilos para ocultar elementos molestos y limpiar la interfaz
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    /* Hacemos el reproductor de audio más grande y accesible */
    audio { width: 100%; height: 50px; }
    </style>
    """, unsafe_allow_html=True)

# Inicializar Estado de Sesión
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# Configurar API Keys
#GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")
ELEVEN_KEY = st.secrets.get("ELEVENLABS_API_KEY")

# Configurar Gemini
#if GOOGLE_API_KEY:
    #genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash') # Modelo rápido y multimodal
#else:
    #st.error("Falta la GOOGLE_API_KEY")
    #st.stop()

# ==========================================
# 🔊 2. FUNCIONES DE VOZ (MOTOR OCULTO)
# ==========================================

def texto_a_voz_elevenlabs(texto):
    """Convierte la respuesta de la IA en Audio MP3 usando ElevenLabs"""
    if not ELEVEN_KEY:
        return None
        
    url = "https://api.elevenlabs.io/v1/text-to-speech/jsCqWAovK2LkecY7zXl4" # Voz "Freya" (suave)
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_KEY
    }
    
    # Limitamos el texto para no gastar créditos excesivos en pruebas
    data = {
        "text": texto[:400], # Lee los primeros 400 caracteres (ajustable)
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            st.warning(f"Error ElevenLabs: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error conexión audio: {e}")
        return None

# ==========================================
# 🏠 3. INTERFAZ DE USUARIO (VISUAL + AUDITIVA)
# ==========================================

st.title("Quantum Mind 🧠")
st.caption("Tu espacio seguro. Escribe o habla, te escucho.")

# --- ZONA DE AUDIO (ACCESIBILIDAD) ---
# Colocamos el micrófono arriba para que sea fácil de encontrar con lectores de pantalla
audio_usuario = st.audio_input("🎤 Toca para hablar (Modo Voz)", key="mic_input")

# --- ZONA DE HISTORIAL ---
for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])
        # Si el mensaje tiene audio guardado, lo mostramos
        if "audio" in mensaje:
            st.audio(mensaje["audio"], format="audio/mp3")

# --- LÓGICA DEL CEREBRO ---

pregunta_usuario = None
modo_entrada = "texto"

# 1. Detectar si habló por micrófono
if audio_usuario:
    modo_entrada = "voz"
    # Usamos Gemini para transcribir el audio (Multimodal)
    # Gemini puede "escuchar" el archivo de audio directamente
    with st.spinner("Escuchando..."):
        try:
            # Enviar audio + prompt a Gemini
            prompt_audio = "Escucha este audio del usuario. Transcribe lo que dice y luego RESPONDE como un terapeuta empático y breve."
            
            # Nota técnica: Para pasar bytes a Gemini a veces requerimos subirlo primero o usar SpeechRecognition.
            # Para simplificar y NO usar otra API, usaremos un truco:
            # Asumiremos que Gemini 'entiende' el contexto si le pasamos el audio como Blob (DataPart).
            # SI ESTO FALLA en tu versión, avísame y usamos la librería 'SpeechRecognition' clásica.
            
            # PLAN B (Más robusto para Streamlit Cloud): Usar SpeechRecognition gratuito de Google
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.AudioFile(audio_usuario) as source:
                audio_data = r.record(source)
                texto_transcrito = r.recognize_google(audio_data, language="es-MX")
                
            pregunta_usuario = texto_transcrito
            
            # Mostramos lo que entendió
            with st.chat_message("user"):
                st.markdown(f"🎤 *Dijiste:* {pregunta_usuario}")
                st.session_state.mensajes.append({"role": "user", "content": f"🎤 {pregunta_usuario}"})

        except Exception as e:
            st.error(f"No pude entender el audio. Intenta de nuevo. Error: {e}")

# 2. Detectar si escribió por texto (Chat Input tradicional)
if prompt_texto := st.chat_input("Escribe aquí..."):
    pregunta_usuario = prompt_texto
    modo_entrada = "texto"
    with st.chat_message("user"):
        st.markdown(pregunta_usuario)
        st.session_state.mensajes.append({"role": "user", "content": pregunta_usuario})

# --- GENERAR RESPUESTA ---
if pregunta_usuario and modo_entrada:
    # Solo generamos respuesta si es una NUEVA interacción (evitar duplicados al recargar)
    # (En este código simplificado, asumo que corre linealmente)
    
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            # Generar texto con Gemini
            prompt_sistema = f"Actúa como un psicólogo empático. El usuario dice: '{pregunta_usuario}'. Responde brevemente (máximo 3 oraciones) y con calidez."
            response = model.generate_content(prompt_sistema)
            texto_respuesta = response.text
            
            st.markdown(texto_respuesta)
            
            # VARIABLE PARA EL AUDIO
            audio_bytes = None
            
            # SOLO generamos audio si la entrada fue por VOZ (Ahorro de dinero y UX lógica)
            if modo_entrada == "voz":
                with st.spinner("Generando voz..."):
                    audio_bytes = texto_a_voz_elevenlabs(texto_respuesta)
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
            
            # Guardar en historial
            msg_bot = {"role": "assistant", "content": texto_respuesta}
            if audio_bytes:
                msg_bot["audio"] = audio_bytes
                
            st.session_state.mensajes.append(msg_bot)
