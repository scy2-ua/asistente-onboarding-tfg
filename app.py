import streamlit as st
import uuid
from dotenv import load_dotenv
# Importar tipos de mensajes para mantener el contexto conversacional
from langchain_core.messages import HumanMessage, AIMessage

from core.document_processor import procesar_repositorio, procesar_reglas_empresa
from agents.graph import init_agent

load_dotenv()

# Inicializar configuración de la UI
# El estado inicial del sidebar se fuerza a expandido.
st.set_page_config(
    page_title="Mentor IA", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INYECCIÓN DE CSS PERSONALIZADO ---
st.markdown("""
<style>
    /* 1. Bloqueo del colapso de la barra lateral */
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }
    
    /* 2. Ocultar elementos nativos de Streamlit */
    header {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    #MainMenu {display: none !important;}
    footer {display: none !important;}
    .stAppDeployButton {display: none !important;}
    
    /* 3. Configuración de la paleta de colores oscuros */
    .stApp {
        background-color: #212121;
    }
    [data-testid="stSidebar"] {
        background-color: #171717;
        border-right: 1px solid #333;
    }
    
    /* 4. Estilos de botones personalizados */
    .stButton>button {
        background-color: #2f2f2f;
        color: #ececec;
        border-radius: 8px;
        border: 1px solid transparent;
        transition: all 0.2s;
        width: 100%;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #40414f;
        border: 1px solid #565869;
        color: white;
    }
    
    /* 5. Estilizar el input de texto del chat */
    [data-testid="stChatInput"] {
        background-color: #2f2f2f !important;
        border-radius: 12px !important;
        border: 1px solid #444 !important;
    }
    
    /* 6. Estilizar inputs secundarios y zona de drag-and-drop */
    .stTextInput input, [data-testid="stFileUploaderDropzone"] {
        background-color: #2f2f2f !important;
        color: white !important;
        border-radius: 8px !important;
        border: 1px solid #444 !important;
    }
    
    /* 7. Tipografía base global */
    h1, h2, h3, p, span, div {
        color: #ececec !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZAR ESTADO DE SESIÓN ---
if "messages" not in st.session_state: st.session_state.messages = []
if "thread_id" not in st.session_state: st.session_state.thread_id = str(uuid.uuid4())
if "archivos_subidos" not in st.session_state: st.session_state.archivos_subidos = [] 

# --- RENDERIZAR BARRA LATERAL ---
with st.sidebar:
    st.markdown("### 🤖 Mentor IA")
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("📝 Nuevo chat"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<span style='font-size: 0.8rem; color: #888 !important;'>CONTEXTO TÉCNICO</span>", unsafe_allow_html=True)
    url = st.text_input("Repositorio Git", placeholder="https://github.com/...", label_visibility="collapsed")
    if st.button("Analizar Proyecto"):
        with st.spinner("Clonando..."):
            procesar_repositorio(url)
            st.session_state.repo_listo = True
            st.success("¡Indexado!")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<span style='font-size: 0.8rem; color: #888 !important;'>CONTEXTO CORPORATIVO</span>", unsafe_allow_html=True)
    guia = st.file_uploader("Manuales (PDF/TXT)", type=["pdf", "txt"], label_visibility="collapsed")
    if st.button("Asimilar Documento"):
        if guia:
            if guia.name not in st.session_state.archivos_subidos:
                procesar_reglas_empresa(guia)
                st.session_state.archivos_subidos.append(guia.name)
                st.success(f"Asimilado: {guia.name}")
            else:
                st.warning("Ya asimilado.")

    if st.session_state.archivos_subidos:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<span style='font-size: 0.8rem; color: #888 !important;'>DOCUMENTOS EN MEMORIA</span>", unsafe_allow_html=True)
        for archivo in st.session_state.archivos_subidos:
            st.markdown(f"<span style='font-size: 0.9rem;'>📄 {archivo}</span>", unsafe_allow_html=True)

# --- RENDERIZAR VISTA PRINCIPAL ---
if st.session_state.get("repo_listo"):
    agent_app = init_agent()
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    # Renderizar landing page vacía (solo si no hay mensajes)
    if len(st.session_state.messages) == 0:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
            st.markdown("<h2 style='text-align: center;'>¿En qué puedo ayudarte con tu código hoy?</h2>", unsafe_allow_html=True)
            st.markdown("<br><br>", unsafe_allow_html=True)

    # Renderizar historial de mensajes en la interfaz
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): 
            st.markdown(msg["content"])

    # Procesar nuevo input
    if prompt := st.chat_input("Pregunta sobre el código, audita un fragmento o consulta a RRHH..."):
        # Persistir mensaje de usuario en estado local
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): 
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    # Parsear historial para LangGraph
                    historial_langchain = []
                    for m in st.session_state.messages:
                        if m["role"] == "user":
                            historial_langchain.append(HumanMessage(content=m["content"]))
                        else:
                            historial_langchain.append(AIMessage(content=m["content"]))

                    # Invocar el grafo con el contexto completo
                    events = agent_app.stream({"messages": historial_langchain}, config, stream_mode="values")
                    
                    last_msg = None
                    for event in events: 
                        last_msg = event["messages"][-1]
                    
                    # Procesar y persistir la respuesta del agente
                    st.markdown(last_msg.content)
                    st.session_state.messages.append({"role": "assistant", "content": last_msg.content})
                except Exception as e:
                    st.error(f"Error: {e}")
else:
    # Renderizar pantalla de onboarding (sin repo conectado)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; font-size: 3rem;'>Mentor IA</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #aaa !important;'>Conecta un repositorio en la barra lateral para comenzar la vectorización.</p>", unsafe_allow_html=True)