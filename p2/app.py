"""
SIAD — Sistema Inteligente de Apoio à Decisão Clínica
Interface Web Streamlit — Sprint 3
"""

# ─── Stdlib ──────────────────────────────────────────────────────────────────
import logging
from typing import Any, Dict, List, Optional

# ─── Streamlit ────────────────────────────────────────────────────────────────
import streamlit as st

# ─── Motor RAG (Sprint 2) ─────────────────────────────────────────────────────
from rag_engine import SIADRagEngine

# ─── Logging (silenciar libs ruidosas na UI) ──────────────────────────────────
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("SIAD.App")


# ════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DA PÁGINA
# ════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="SIAD · Triagem SNS24",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ════════════════════════════════════════════════════════════════════════════
# CSS PERSONALIZADO
# ════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    /* Cabeçalho da aplicação */
    .siad-header {
        background: linear-gradient(135deg, #0057A8 0%, #003f7f 100%);
        color: white;
        padding: 1.2rem 1.8rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    .siad-header h1 { margin: 0; font-size: 1.6rem; }
    .siad-header p  { margin: 0.2rem 0 0 0; font-size: 0.9rem; opacity: 0.85; }

    /* Cartão de chunk na sidebar */
    .chunk-card {
        background: #f0f4f8;
        border-left: 4px solid #0057A8;
        border-radius: 6px;
        padding: 0.7rem 0.9rem;
        margin-bottom: 0.8rem;
        font-size: 0.8rem;
        line-height: 1.5;
    }
    .chunk-card .chunk-meta {
        color: #0057A8;
        font-weight: 700;
        font-size: 0.75rem;
        margin-bottom: 0.3rem;
    }
    .chunk-card .chunk-text { color: #333; }

    /* Badge de disposição final */
    .badge-emergencia  { background:#dc2626; color:white; padding:3px 10px;
                         border-radius:20px; font-size:0.78rem; font-weight:700; }
    .badge-urgencia    { background:#ea580c; color:white; padding:3px 10px;
                         border-radius:20px; font-size:0.78rem; font-weight:700; }
    .badge-primarios   { background:#2563eb; color:white; padding:3px 10px;
                         border-radius:20px; font-size:0.78rem; font-weight:700; }
    .badge-autocuidado { background:#16a34a; color:white; padding:3px 10px;
                         border-radius:20px; font-size:0.78rem; font-weight:700; }

    /* Sidebar — título da secção */
    .debug-title {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748b;
        font-weight: 700;
        margin: 1rem 0 0.5rem 0;
    }

    /* Esconder o menu hamburger padrão do Streamlit */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# CACHE DO MOTOR RAG
# ════════════════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner="A carregar o motor de triagem, aguarde...")
def carregar_engine() -> SIADRagEngine:
    engine = SIADRagEngine(ollama_model="phi3")
    engine.inicializar()
    return engine


# ════════════════════════════════════════════════════════════════════════════
# INICIALIZAÇÃO DO SESSION STATE
# ════════════════════════════════════════════════════════════════════════════

def _init_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_sources" not in st.session_state:
        st.session_state.last_sources = []
    if "turn_count" not in st.session_state:
        st.session_state.turn_count = 0
    if "triagem_ativa" not in st.session_state:
        st.session_state.triagem_ativa = True


_init_session_state()


# ════════════════════════════════════════════════════════════════════════════
# CARREGAMENTO DO MOTOR (com tratamento de erro na UI)
# ════════════════════════════════════════════════════════════════════════════

try:
    engine: SIADRagEngine = carregar_engine()
    engine_ok = True
except FileNotFoundError:
    engine_ok = False
    st.error(
        "**Base de dados não encontrada.**\n\n"
        "Execute primeiro o pipeline de ingestão:\n"
        "```bash\npython data_ingestion.py\n```",
    )
except Exception as exc:
    engine_ok = False
    st.error(
        f"**Erro ao inicializar o motor RAG:**\n\n`{type(exc).__name__}: {exc}`\n\n"
        "Verifique se o Ollama está em execução: `ollama serve`",
    )


# ════════════════════════════════════════════════════════════════════════════
# CABEÇALHO DA APLICAÇÃO
# ════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="siad-header">
    <h1>SIAD &mdash; Assistente de Triagem SNS24</h1>
    <p>Sistema Inteligente de Apoio à Decisão Clínica &middot; phi3 + ChromaDB &middot; LCEL</p>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR — PAINEL DE DEBUG
# ════════════════════════════════════════════════════════════════════════════

with st.sidebar:

    st.markdown("## Painel de Debug RAG")
    st.caption("Informação interna do sistema — visível apenas para desenvolvimento")

    st.divider()

    # ── Métricas da Sessão ──────────────────────────────────────────────────
    st.markdown('<p class="debug-title">Métricas da sessão</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    col1.metric("Turnos", st.session_state.turn_count)
    col2.metric("Mensagens", len(st.session_state.messages))

    st.divider()

    # ── Chunks Recuperados ──────────────────────────────────────────────────
    st.markdown('<p class="debug-title">Chunks recuperados (última query)</p>', unsafe_allow_html=True)

    fontes = st.session_state.last_sources

    if not fontes:
        st.info("Ainda não houve interações. Envie uma mensagem para ver os chunks recuperados.")
    else:
        st.caption(f"{len(fontes)} chunk(s) recuperado(s) da ChromaDB por similaridade coseno")

        for i, doc in enumerate(fontes, start=1):
            chunk_id    = doc.metadata.get("chunk_id", "?")
            chunk_total = doc.metadata.get("chunk_total", "?")
            fonte       = doc.metadata.get("fonte", "N/A")
            modulo      = doc.metadata.get("modulo", "N/A")
            start_idx   = doc.metadata.get("start_index", "N/A")
            preview     = doc.page_content[:300].strip().replace("\n", " ")
            if len(doc.page_content) > 300:
                preview += "…"

            st.markdown(f"""
<div class="chunk-card">
    <div class="chunk-meta">
        #{i} &middot; Chunk {chunk_id}/{chunk_total} &middot; índice {start_idx}
    </div>
    <div class="chunk-meta" style="color:#64748b; font-weight:400;">
        Fonte: {fonte}<br>Módulo: {modulo}
    </div>
    <div class="chunk-text">{preview}</div>
</div>
""", unsafe_allow_html=True)

    st.divider()

    # ── Configuração Técnica ────────────────────────────────────────────────
    st.markdown('<p class="debug-title">Configuração técnica</p>', unsafe_allow_html=True)

    st.markdown("""
| Parâmetro | Valor |
|-----------|-------|
| LLM | `phi3` (Ollama) |
| Embeddings | `MiniLM-L12-v2` |
| Vector Store | ChromaDB local |
| Top-K retrieval | 4 chunks |
| Temperatura | 0.1 |
| Framework | LangChain LCEL |
""")

    st.divider()

    # ── Botão de Nova Sessão ────────────────────────────────────────────────
    st.markdown('<p class="debug-title">Controlo de sessão</p>', unsafe_allow_html=True)

    if st.button("Nova triagem (limpar histórico)", use_container_width=True):
        if engine_ok:
            engine.nova_sessao()
        st.session_state.messages     = []
        st.session_state.last_sources = []
        st.session_state.turn_count   = 0
        st.session_state.triagem_ativa = True
        st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# ÁREA PRINCIPAL — HISTÓRICO DO CHAT
# ════════════════════════════════════════════════════════════════════════════

if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(
            "Olá, bem-vindo ao assistente de triagem do **SNS24**. "
            "Estou aqui para ajudar a avaliar a situação de saúde do utente.\n\n"
            "Para começar, diga-me: **o utente está consciente e consegue comunicar?**"
        )

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ════════════════════════════════════════════════════════════════════════════
# INPUT DO UTENTE E PROCESSAMENTO RAG
# ════════════════════════════════════════════════════════════════════════════

user_input: Optional[str] = st.chat_input(
    placeholder="Descreva os sintomas do utente...",
    disabled=not engine_ok,
)

if user_input and engine_ok:

    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("A consultar os protocolos clínicos..."):
            try:
                resposta, fontes = engine.chat_with_bot(user_input)
            except Exception as exc:
                resposta = (
                    f"Ocorreu um erro interno: `{exc}`\n\n"
                    "Por favor tente novamente ou reinicie a sessão."
                )
                fontes = []
                logger.exception("Erro em chat_with_bot")

        st.markdown(resposta)

    st.session_state.messages.append({"role": "assistant", "content": resposta})
    st.session_state.last_sources = fontes
    st.session_state.turn_count  += 1

    st.rerun()