"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          SIAD — Sistema Inteligente de Apoio à Decisão Clínica             ║
║          Motor RAG + LCEL — Sprint 2 (Reescrita Moderna)                   ║
║          Compatível com LangChain >= 0.2.x / 1.x  (sem chains legacy)     ║
╚══════════════════════════════════════════════════════════════════════════════╝

Módulo: rag_engine.py

Arquitetura LCEL do pipeline (notação pipe):

    Input: {"question": str, "chat_history": List[BaseMessage]}
                        │
                        ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  RunnableParallel                                           │
    │  ├─ "context"      → retriever(question) | _format_docs    │
    │  ├─ "question"     → RunnablePassthrough()                 │
    │  └─ "chat_history" → RunnablePassthrough()                 │
    └─────────────────────────────────────────────────────────────┘
                        │
                        ▼
            ChatPromptTemplate
            (SystemMessage + MessagesPlaceholder + HumanMessage)
                        │
                        ▼
            ChatOllama(model="phi3", temperature=0.1)
                        │
                        ▼
            StrOutputParser()  →  str

Dependências:
    pip install langchain-core langchain-community langchain-chroma langchain-ollama
    pip install sentence-transformers chromadb
"""

# ─── Stdlib ──────────────────────────────────────────────────────────────────
import logging
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# ─── LangChain Core (LCEL — sem imports de langchain.chains) ─────────────────
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)

# ─── Integrações Externas ─────────────────────────────────────────────────────
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_ollama import ChatOllama

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("SIAD.RAGEngine.LCEL")


# ════════════════════════════════════════════════════════════════════════════
# CONSTANTES — devem coincidir EXATAMENTE com as do data_ingestion.py
# ════════════════════════════════════════════════════════════════════════════

CHROMA_DB_DIR:   str   = "./chroma_db"
COLLECTION_NAME: str   = "sns24_triagem"
EMBEDDING_MODEL: str   = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OLLAMA_MODEL:    str   = "phi3"
OLLAMA_BASE_URL: str   = "http://localhost:11434"
OLLAMA_TEMP:     float = 0.1   # Baixo → respostas deterministas (essencial em triagem)
RETRIEVER_TOP_K: int   = 4     # Chunks recuperados por query


# ════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT CLÍNICO RESTRITIVO — v2 (Comportamento Afinado)
# ════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT: str = """
És o Assistente Virtual de Triagem do SNS24.
Estás numa chamada telefónica a falar DIRETAMENTE com o utente.

══════════════════════════════════════════
IDENTIDADE E VOZ — REGRAS ABSOLUTAS
══════════════════════════════════════════
1. Fala SEMPRE na primeira pessoa e dirige-te SEMPRE ao utente na segunda pessoa.
   ✅ CORRETO:  "Compreendo. Consegue dizer-me se..."
   ✅ CORRETO:  "Obrigado por essa informação. Tem também..."
   ❌ PROIBIDO: "Avalie se o utente..." / "O assistente deve..." / "O utente refere..."
2. NUNCA mostres nem cites a sintaxe interna do manual (proibido escrever
   "SE (condição) ENTÃO", "Regra F-R4", "ADR-SU", ou qualquer código interno).
   Usa linguagem natural e acessível ao cidadão comum.
3. NÃO és médico. NUNCA faças diagnósticos. NUNCA prescrevas medicamentos.

══════════════════════════════════════════
RACIOCÍNIO CLÍNICO — REGRA DE OURO
══════════════════════════════════════════
4. Antes de aceitar qualquer valor ou sintoma que o utente refira, compara-o
   com os limiares definidos no CONTEXTO CLÍNICO abaixo.
   Exemplos obrigatórios:
   • O utente diz "tenho 36ºC" → o contexto define febre como >= 38ºC →
     CONCLUIS internamente: 36ºC NÃO é febre clínica. Não assumas o sintoma.
     Responde: "36ºC está dentro dos valores normais, por isso não se trata
     de febre. Diga-me, essa sensação de calor surgiu..."
   • O utente diz "dói um pouco" → avalia se se qualifica para a regra antes
     de avançar.
5. Usa APENAS a informação do CONTEXTO CLÍNICO fornecido para guiar a triagem.
   Nunca uses conhecimento médico geral ou de treino.
6. Se a situação NÃO estiver coberta pelo contexto, diz APENAS:
   "Vou encaminhar a sua chamada para um Enfermeiro Sénior."
   Não acrescentes mais nada.

══════════════════════════════════════════
PROTOCOLO DE INTERAÇÃO
══════════════════════════════════════════
7. Faz APENAS UMA PERGUNTA DE CADA VEZ. Aguarda a resposta antes de continuar.
8. Segue SEMPRE esta hierarquia de avaliação:

   FASE 1 — Red Flags (pré-triagem obrigatória, por esta ordem):
     a) Consciência → "Está consciente e a conseguir falar comigo?"
     b) Respiração  → "Consegue respirar sem dificuldade?"
     c) Cianose     → "Reparou se tem os lábios ou as unhas com uma cor azulada?"
   Só avança para a Fase 2 depois de excluíres TODAS as Red Flags.

   FASE 2 — Árvore de decisão do sintoma principal:
     Faz as perguntas necessárias para completar a regra do contexto
     (ex: duração, intensidade, sintomas associados, medicação já tomada).
     Uma pergunta de cada vez. Aguarda sempre a resposta.

   FASE 3 — Disposição Final:
     Só dás a disposição quando tiveres TODAS as respostas necessárias
     para aplicar uma regra do contexto. Apresenta-a em linguagem natural:
     ✅ "Face ao que me descreveu, recomendo que ligue imediatamente para
        o 112, pois a situação requer assistência de emergência."
     ✅ "Pela sua situação, pode gerir em casa com repouso e líquidos.
        Se os sintomas piorarem nas próximas 24 horas, contacte-nos novamente."
     ❌ PROIBIDO: "EMERGÊNCIA 112" / "ADR-SU" / "AUTOCUIDADO" como etiquetas soltas.

══════════════════════════════════════════
CONTEXTO CLÍNICO (Regras SNS24 recuperadas)
══════════════════════════════════════════
{context}
"""


# ════════════════════════════════════════════════════════════════════════════
# FUNÇÃO 1 — CARREGAR VECTOR STORE
# ════════════════════════════════════════════════════════════════════════════

def carregar_vector_store(
    diretorio_db: str = CHROMA_DB_DIR,
    nome_colecao: str = COLLECTION_NAME,
    nome_modelo:  str = EMBEDDING_MODEL,
) -> Chroma:
    """
    Carrega (só lê) a ChromaDB persistida pelo Sprint 1 (data_ingestion.py).

    O modelo de embeddings DEVE ser idêntico ao usado na ingestão.
    Qualquer diferença produz vetores incompatíveis e retrieval incorreto.

    Raises:
        FileNotFoundError: pasta chroma_db ausente → Sprint 1 não correu.
        RuntimeError:      falha ao inicializar o modelo de embeddings.
    """
    logger.info(f"A carregar ChromaDB de '{diretorio_db}' (coleção: '{nome_colecao}')...")

    if not Path(diretorio_db).exists():
        raise FileNotFoundError(
            f"ChromaDB não encontrada em '{diretorio_db}'.\n"
            f"  → Execute primeiro: python data_ingestion.py"
        )

    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=nome_modelo,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True, "batch_size": 32},
            cache_folder="./models_cache",
        )
    except Exception as exc:
        raise RuntimeError(
            f"Falha ao carregar modelo de embeddings '{nome_modelo}': {exc}\n"
            f"  → pip install sentence-transformers"
        ) from exc

    store = Chroma(
        persist_directory=diretorio_db,
        embedding_function=embeddings,
        collection_name=nome_colecao,
    )

    n = store._collection.count()
    logger.info(f"✔ ChromaDB carregada — {n} vetores disponíveis.")
    return store


# ════════════════════════════════════════════════════════════════════════════
# FUNÇÃO 2 — FORMATAR CHUNKS PARA O CONTEXTO DO PROMPT
# ════════════════════════════════════════════════════════════════════════════

def _format_docs(docs: List[Document]) -> str:
    """
    Concatena o conteúdo dos chunks recuperados num único bloco de texto.

    Cada chunk é separado por uma linha divisória para ajudar o phi3
    a distinguir as diferentes regras clínicas no contexto.

    Args:
        docs: Lista de Documents devolvida pelo retriever ChromaDB.

    Returns:
        String formatada para injeção na variável {context} do prompt.
    """
    if not docs:
        return "(Nenhuma regra clínica relevante encontrada para esta situação.)"

    secoes: List[str] = []
    for i, doc in enumerate(docs, start=1):
        chunk_id = doc.metadata.get("chunk_id", "?")
        modulo   = doc.metadata.get("modulo", "N/A")
        secoes.append(
            f"[Regra #{i} | Chunk {chunk_id} | {modulo}]\n{doc.page_content.strip()}"
        )
    return "\n\n---\n\n".join(secoes)


# ════════════════════════════════════════════════════════════════════════════
# FUNÇÃO 3 — CONSTRUIR A CHAIN LCEL
# ════════════════════════════════════════════════════════════════════════════

def construir_chain_lcel(
    store:    Chroma,
    top_k:    int   = RETRIEVER_TOP_K,
    modelo:   str   = OLLAMA_MODEL,
    base_url: str   = OLLAMA_BASE_URL,
    temp:     float = OLLAMA_TEMP,
):
    """
    Constrói a chain RAG em LCEL pura — zero dependência de langchain.chains.

    Input esperado pelo Runnable devolvido:
        {"question": str, "chat_history": List[BaseMessage]}

    Output:
        str  (resposta gerada pelo phi3)

    Detalhe do RunnableParallel:
        O retriever só aceita str (não aceita dict). Por isso, usamos
        RunnableLambda para extrair apenas "question" antes de passar ao
        retriever, enquanto as outras chaves passam via RunnablePassthrough.

    Returns:
        Tuplo (chain_runnable, retriever)
        O retriever é devolvido separadamente para permitir que
        chat_with_bot() recupere os documentos fonte de forma explícita.
    """
    logger.info(f"A construir chain LCEL — modelo: '{modelo}', top_k: {top_k}")

    # ── Retriever ─────────────────────────────────────────────────────────────
    retriever = store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k},
    )

    # ── LLM ───────────────────────────────────────────────────────────────────
    try:
        llm = ChatOllama(
            model=modelo,
            base_url=base_url,
            temperature=temp,
            num_predict=512,  # Limita a resposta — 1 pergunta de cada vez
        )
    except Exception as exc:
        raise RuntimeError(
            f"Falha ao criar ChatOllama(model='{modelo}'): {exc}\n"
            f"  → ollama pull {modelo}\n"
            f"  → pip install langchain-ollama"
        ) from exc

    # ── Prompt Template ───────────────────────────────────────────────────────
    # MessagesPlaceholder injeta a lista de HumanMessage/AIMessage do histórico
    # como mensagens reais na sequência do ChatPromptTemplate (não como string).
    # Isto é essencial para que o phi3 entenda o turn-by-turn do diálogo.
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ])

    # ── RunnableParallel ──────────────────────────────────────────────────────
    # Executa em paralelo antes de alimentar o prompt:
    #
    #   context      → extrai "question" do dict de entrada,
    #                  passa ao retriever, formata os docs devolvidos
    #
    #   question     → extrai "question" do dict (string simples)
    #
    #   chat_history → extrai "chat_history" do dict (List[BaseMessage])
    #
    # Nota: RunnablePassthrough() sozinho passaria o dict completo.
    # Usamos RunnableLambda para extrair individualmente cada chave.

    parallel_step = RunnableParallel(
        context=(
            RunnableLambda(lambda x: x["question"])   # dict → str
            | retriever                                # str → List[Document]
            | _format_docs                             # List[Document] → str
        ),
        question=RunnableLambda(lambda x: x["question"]),
        chat_history=RunnableLambda(lambda x: x["chat_history"]),
    )

    # ── Chain Final (pipe LCEL) ────────────────────────────────────────────────
    # parallel_step → prompt → llm → parser
    #
    # O StrOutputParser extrai o .content do AIMessage devolvido pelo ChatOllama,
    # convertendo-o numa str simples para devolução ao utilizador.
    chain = parallel_step | prompt | llm | StrOutputParser()

    logger.info("✔ Chain LCEL construída com sucesso.")
    return chain, retriever


# ════════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPAL — SIAD RAG ENGINE (LCEL)
# ════════════════════════════════════════════════════════════════════════════

class SIADRagEngine:
    """
    Motor RAG do SIAD usando LCEL pura (LangChain >= 0.2 / 1.x).

    O histórico de conversa é gerido internamente como lista de
    HumanMessage / AIMessage (objetos LangChain Core), compatíveis
    com MessagesPlaceholder. Não há dependência de ConversationBufferMemory
    nem de nenhuma classe legacy de langchain.memory.

    Exemplo de uso:
        engine = SIADRagEngine().inicializar()
        resposta, fontes = engine.chat_with_bot("Tenho febre há 3 dias.")
        print(resposta)
    """

    def __init__(
        self,
        chroma_dir:      str   = CHROMA_DB_DIR,
        collection:      str   = COLLECTION_NAME,
        embedding_model: str   = EMBEDDING_MODEL,
        ollama_model:    str   = OLLAMA_MODEL,
        ollama_url:      str   = OLLAMA_BASE_URL,
        temperatura:     float = OLLAMA_TEMP,
        top_k:           int   = RETRIEVER_TOP_K,
    ) -> None:
        self.chroma_dir      = chroma_dir
        self.collection      = collection
        self.embedding_model = embedding_model
        self.ollama_model    = ollama_model
        self.ollama_url      = ollama_url
        self.temperatura     = temperatura
        self.top_k           = top_k

        self._store:     Optional[Chroma] = None
        self._chain                       = None   # Runnable LCEL
        self._retriever                   = None   # ChromaDB retriever
        self._chat_history: List[BaseMessage] = [] # histórico da sessão atual
        self._pronto:    bool             = False

    # ── Inicialização ──────────────────────────────────────────────────────────

    def inicializar(self) -> "SIADRagEngine":
        """
        Carrega a Vector Store e constrói a chain LCEL.

        Separado do __init__ para permitir tratamento explícito de erros
        e inicialização lazy (útil em testes unitários).

        Returns:
            Self — encadeamento: engine.inicializar().chat_with_bot(...)
        """
        logger.info("=" * 62)
        logger.info(f"  SIAD — Motor RAG LCEL | modelo: {self.ollama_model}")
        logger.info("=" * 62)

        self._store = carregar_vector_store(
            self.chroma_dir, self.collection, self.embedding_model
        )
        self._chain, self._retriever = construir_chain_lcel(
            store=self._store,
            top_k=self.top_k,
            modelo=self.ollama_model,
            base_url=self.ollama_url,
            temp=self.temperatura,
        )

        self._pronto = True
        logger.info("=" * 62)
        logger.info("  ✅ Motor RAG pronto para triagem.")
        logger.info("=" * 62)
        return self

    # ── Gestão de Sessão ───────────────────────────────────────────────────────

    def nova_sessao(self) -> None:
        """
        Limpa o histórico de conversa para uma nova triagem.
        Não recarrega embeddings nem o LLM.
        """
        self._chat_history = []
        logger.info("✔ Nova sessão — histórico limpo.")

    # ── Interface Principal ────────────────────────────────────────────────────

    def chat_with_bot(
        self,
        user_input: str,
    ) -> Tuple[str, List[Document]]:
        """
        Processa o input do utente e devolve (resposta, fontes).

        Fluxo interno:
          1. Retriever recupera os chunks relevantes (fontes para exposição)
          2. Chain LCEL recebe question + chat_history → gera resposta
          3. Troca é adicionada ao histórico (HumanMessage + AIMessage)
          4. Devolve (resposta_str, lista_de_documentos_fonte)

        Args:
            user_input: Texto em Português do utente.

        Returns:
            Tuplo (resposta: str, fontes: List[Document])

        Raises:
            RuntimeError: se inicializar() não foi chamado.
        """
        if not self._pronto or self._chain is None:
            raise RuntimeError(
                "Motor não inicializado. Chame engine.inicializar() primeiro."
            )

        if not user_input.strip():
            return "Não entendi. Pode repetir, por favor?", []

        # Passo 1 — Recuperar fontes explicitamente (para devolver ao caller)
        # O retriever é invocado separadamente da chain porque a chain LCEL
        # apenas expõe o output final (str), não os documentos intermédios.
        fontes: List[Document] = self._retriever.invoke(user_input)

        # Passo 2 — Invocar a chain com o estado atual da conversa
        resposta: str = self._chain.invoke({
            "question":     user_input,
            "chat_history": self._chat_history,
        })

        # Passo 3 — Persistir a troca no histórico da sessão
        # HumanMessage / AIMessage são os tipos esperados pelo MessagesPlaceholder
        self._chat_history.append(HumanMessage(content=user_input))
        self._chat_history.append(AIMessage(content=resposta))

        logger.info(
            f"Resposta: {len(resposta)} chars | "
            f"Fontes: {len(fontes)} chunks | "
            f"Histórico: {len(self._chat_history) // 2} turno(s)"
        )
        return resposta, fontes


# ════════════════════════════════════════════════════════════════════════════
# UTILITÁRIO — FORMATAR FONTES PARA O TERMINAL
# ════════════════════════════════════════════════════════════════════════════

def formatar_fontes(fontes: List[Document]) -> str:
    """Formata a lista de chunks fonte para apresentação legível no terminal."""
    if not fontes:
        return "  (Nenhum chunk recuperado da Vector Store)"

    linhas: List[str] = []
    for i, doc in enumerate(fontes, start=1):
        chunk_id = doc.metadata.get("chunk_id", "?")
        fonte    = doc.metadata.get("fonte", "N/A")
        modulo   = doc.metadata.get("modulo", "N/A")
        preview  = doc.page_content[:200].strip().replace("\n", " ")
        if len(doc.page_content) > 200:
            preview += "…"
        linhas.append(
            f"  [{i}] Chunk #{chunk_id} | {fonte}\n"
            f"      Módulo: {modulo}\n"
            f"      ↳ {preview}"
        )
    return "\n".join(linhas)


# ════════════════════════════════════════════════════════════════════════════
# BLOCO PRINCIPAL — LOOP DE CHAT NO TERMINAL
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    # ── Banner ─────────────────────────────────────────────────────────────────
    print()
    print("╔" + "═" * 68 + "╗")
    print("║   SIAD — Assistente de Triagem SNS24  [LCEL + phi3]             ║")
    print("║   Sistema Inteligente de Apoio à Decisão Clínica                ║")
    print("║   LangChain >= 0.2 | ChromaDB local | Ollama                    ║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  Comandos especiais:")
    print("    'sair'  / 'exit'  → Terminar o programa")
    print("    'novo'  / 'reset' → Nova sessão (limpa histórico)")
    print("    'fontes'          → Mostrar / ocultar fontes da última resposta")
    print()

    # ── Inicialização do Motor ─────────────────────────────────────────────────
    engine = SIADRagEngine(ollama_model="phi3")

    try:
        engine.inicializar()
    except FileNotFoundError as exc:
        print(f"\n❌ ERRO: {exc}")
        print("   Solução: execute primeiro python data_ingestion.py")
        sys.exit(1)
    except RuntimeError as exc:
        print(f"\n❌ ERRO: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"\n❌ ERRO INESPERADO: {type(exc).__name__}: {exc}")
        sys.exit(1)

    print()
    print("─" * 70)
    print("  🏥 Assistente SNS24 pronto. Descreva a situação do utente.")
    print("─" * 70)
    print()

    # ── Estado do Loop ─────────────────────────────────────────────────────────
    mostrar_fontes: bool          = True
    ultima_fontes: List[Document] = []

    # ── Loop Principal while True ──────────────────────────────────────────────
    while True:

        try:
            user_input: str = input("  Utente: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n  👋 Sessão terminada. Cuide-se!")
            sys.exit(0)

        if not user_input:
            continue

        # Comandos especiais
        cmd = user_input.lower()

        if cmd in ("sair", "exit", "quit"):
            print("\n  👋 A encerrar o SIAD. Obrigado por usar o SNS24.")
            break

        if cmd in ("novo", "reset", "nova sessão"):
            engine.nova_sessao()
            ultima_fontes = []
            print("\n  🔄 Nova sessão iniciada — histórico limpo.\n")
            continue

        if cmd == "fontes":
            mostrar_fontes = not mostrar_fontes
            estado = "VISÍVEIS" if mostrar_fontes else "OCULTAS"
            print(f"\n  📚 Fontes agora {estado}.\n")
            if mostrar_fontes and ultima_fontes:
                print(formatar_fontes(ultima_fontes))
                print()
            continue

        # ── Invocar o Motor RAG ────────────────────────────────────────────────
        print()
        print("  Assistente SNS24:", end=" ", flush=True)

        try:
            resposta, fontes = engine.chat_with_bot(user_input)
            ultima_fontes    = fontes

            print(resposta)

            if mostrar_fontes and fontes:
                print()
                print("  ─ Fontes (Vector Store ChromaDB) ─────────────────────────")
                print(formatar_fontes(fontes))
                print("  ──────────────────────────────────────────────────────────")

        except Exception as exc:
            print(f"\n  ❌ ERRO: {type(exc).__name__}: {exc}")
            logger.exception("Erro não tratado no loop de chat.")

        print()