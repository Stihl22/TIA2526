"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          SIAD — Sistema Inteligente de Apoio à Decisão Clínica             ║
║          Interface Web Streamlit — Sprint 3                                ║
║          Importa: rag_engine.py (Sprint 2)                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

Módulo: app.py
Objetivo: Interface Web profissional sobre o motor RAG do Sprint 2.

Executar:
    streamlit run app.py

Dependências novas:
    pip install streamlit
"""

# ─── Stdlib ──────────────────────────────────────────────────────────────────
import logging
from typing import Any, Dict, List

# ─── Streamlit ────────────────────────────────────────────────────────────────
import streamlit as st

# ─── Motor RAG (Sprint 2) ─────────────────────────────────────────────────────
# Importamos apenas a classe — a chain LCEL, o retriever e a ChromaDB são
# todos encapsulados dentro de SIADRagEngine.inicializar().
from rag_engine import SIADRagEngine

# ─── Logging (silenciar libs ruidosas na UI) ──────────────────────────────────
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("SIAD.App")


# ════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DA PÁGINA — deve ser a PRIMEIRA chamada Streamlit do script
# ════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="SIAD · Triagem SNS24",
    page_icon="🏥",
    layout="wide",              # Usa toda a largura para acomodar o painel de debug
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

    /* Esconder o menu hamburger padrão do Streamlit (opcional) */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# CACHE DO MOTOR RAG — @st.cache_resource
# ════════════════════════════════════════════════════════════════════════════
# @st.cache_resource garante que SIADRagEngine.inicializar() é chamado
# UMA ÚNICA VEZ por processo Streamlit, independentemente de quantas
# mensagens o utente envie ou quantas vezes a página recarregar.
#
# Sem este decorator, a ChromaDB e o modelo de embeddings seriam
# recarregados a cada interação — tornando a app inutilizável.

@st.cache_resource(show_spinner="🔄 A carregar o motor RAG (só na primeira vez)...")
def carregar_engine() -> SIADRagEngine:
    """
    Instancia e inicializa o motor RAG uma única vez por sessão de servidor.

    Returns:
        SIADRagEngine pronto para receber mensagens.

    Raises:
        Qualquer exceção de inicialização é propagada e mostrada na UI.
    """
    engine = SIADRagEngine(ollama_model="phi3")
    engine.inicializar()
    return engine


# ════════════════════════════════════════════════════════════════════════════
# INICIALIZAÇÃO DO SESSION STATE
# ════════════════════════════════════════════════════════════════════════════
# st.session_state persiste entre reruns (cada mensagem enviada causa um
# rerun do script). Inicializamos as chaves apenas se ainda não existirem.

def _init_session_state() -> None:
    """Garante que todas as chaves do session_state existem."""

    # Lista de mensagens para o chat UI: cada item é um dict
    # {"role": "user"|"assistant", "content": str}
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Chunks recuperados na última interação (para o painel de debug)
    if "last_sources" not in st.session_state:
        st.session_state.last_sources = []

    # Número total de turnos (para métricas na sidebar)
    if "turn_count" not in st.session_state:
        st.session_state.turn_count = 0

    # Estado da triagem (em curso / concluída)
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
        "**ChromaDB não encontrada.**\n\n"
        "Execute primeiro o pipeline de ingestão:\n"
        "```bash\npython data_ingestion.py\n```",
        icon="❌",
    )
except Exception as exc:
    engine_ok = False
    st.error(
        f"**Erro ao inicializar o motor RAG:**\n\n`{type(exc).__name__}: {exc}`\n\n"
        "Verifique se o Ollama está em execução: `ollama serve`",
        icon="❌",
    )


# ════════════════════════════════════════════════════════════════════════════
# CABEÇALHO DA APLICAÇÃO
# ════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="siad-header">
    <h1>🏥 SIAD · Assistente de Triagem SNS24</h1>
    <p>Sistema Inteligente de Apoio à Decisão Clínica · phi3 + ChromaDB · LCEL</p>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR — PAINEL DE DEBUG DO ARQUITETO
# ════════════════════════════════════════════════════════════════════════════

with st.sidebar:

    st.markdown("## 🔬 Painel de Debug RAG")
    st.caption("Visível apenas para o Arquiteto · Prova que o RAG está ativo")

    st.divider()

    # ── Métricas da Sessão ──────────────────────────────────────────────────
    st.markdown('<p class="debug-title">📊 Métricas da Sessão</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    col1.metric("Turnos", st.session_state.turn_count)
    col2.metric("Msgs", len(st.session_state.messages))

    st.divider()

    # ── Chunks Recuperados ──────────────────────────────────────────────────
    st.markdown('<p class="debug-title">📚 Chunks Recuperados (última query)</p>', unsafe_allow_html=True)

    fontes = st.session_state.last_sources

    if not fontes:
        st.info("Ainda não houve interações. Envie uma mensagem para ver os chunks.")
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

            # Renderizar cada chunk como cartão HTML
            st.markdown(f"""
<div class="chunk-card">
    <div class="chunk-meta">
        #{i} · Chunk {chunk_id}/{chunk_total} · índice {start_idx}
    </div>
    <div class="chunk-meta" style="color:#64748b; font-weight:400;">
        📁 {fonte}<br>🔬 {modulo}
    </div>
    <div class="chunk-text">{preview}</div>
</div>
""", unsafe_allow_html=True)

    st.divider()

    # ── Configuração Técnica ────────────────────────────────────────────────
    st.markdown('<p class="debug-title">⚙️ Configuração Técnica</p>', unsafe_allow_html=True)

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
    st.markdown('<p class="debug-title">🔄 Controlo de Sessão</p>', unsafe_allow_html=True)

    if st.button("🗑️ Nova Triagem (limpar histórico)", use_container_width=True):
        # Limpar o histórico na engine (lista de BaseMessage)
        if engine_ok:
            engine.nova_sessao()
        # Limpar o session_state da UI
        st.session_state.messages    = []
        st.session_state.last_sources = []
        st.session_state.turn_count  = 0
        st.session_state.triagem_ativa = True
        st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# ÁREA PRINCIPAL — HISTÓRICO DO CHAT
# ════════════════════════════════════════════════════════════════════════════

# Mensagem de boas-vindas (só aparece se não houver histórico)
if not st.session_state.messages:
    with st.chat_message("assistant", avatar="🏥"):
        st.markdown(
            "Olá! Sou o Assistente de Triagem do **SNS24**. "
            "Estou aqui para o ajudar a avaliar a sua situação de saúde.\n\n"
            "Para começar, diga-me: **o utente está consciente e consegue falar comigo?**"
        )

# Renderizar todo o histórico de mensagens guardado no session_state.
# O Streamlit faz rerun a cada input, por isso precisamos de re-renderizar
# todas as mensagens anteriores em cada execução do script.
for msg in st.session_state.messages:
    avatar = "🧑" if msg["role"] == "user" else "🏥"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])


# ════════════════════════════════════════════════════════════════════════════
# INPUT DO UTENTE E PROCESSAMENTO RAG
# ════════════════════════════════════════════════════════════════════════════

# st.chat_input é sempre renderizado no fundo da página.
# Devolve None enquanto o utente não enviou nada; str quando enviou.
user_input: str | None = st.chat_input(
    placeholder="Descreva os sintomas do utente...",
    disabled=not engine_ok,   # Desativar se o motor falhou a inicializar
)

if user_input and engine_ok:

    # ── 1. Mostrar mensagem do utente imediatamente ─────────────────────────
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)

    # ── 2. Gerar resposta com o motor RAG ───────────────────────────────────
    with st.chat_message("assistant", avatar="🏥"):
        # Spinner enquanto o phi3 processa (pode demorar alguns segundos em CPU)
        with st.spinner("A consultar os protocolos SNS24..."):
            try:
                resposta, fontes = engine.chat_with_bot(user_input)
            except Exception as exc:
                resposta = (
                    f"⚠️ Ocorreu um erro interno: `{exc}`\n\n"
                    "Por favor tente novamente ou reinicie a sessão."
                )
                fontes = []
                logger.exception("Erro em chat_with_bot")

        st.markdown(resposta)

    # ── 3. Guardar resposta e fontes no session_state ───────────────────────
    st.session_state.messages.append({"role": "assistant", "content": resposta})
    st.session_state.last_sources = fontes
    st.session_state.turn_count  += 1

    # ── 4. Forçar rerun para atualizar a sidebar com os novos chunks ────────
    # Sem st.rerun(), a sidebar só atualizaria na próxima interação do utente.
    st.rerun()