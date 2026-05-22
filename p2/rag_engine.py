"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          SIAD — Sistema Inteligente de Apoio à Decisão Clínica             ║
║          Motor RAG com ChromaDB e OllamaEmbeddings                         ║
║          Compatível com LangChain >= 0.2.x / 1.x                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

Módulo: rag_engine.py
"""

import logging
import shutil
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("SIAD.RAGEngine")

REGRAS_PATH:     str   = "./sns24Regras.txt"
OLLAMA_MODEL:    str   = "llama3.2:1b"
EMBEDDING_MODEL: str   = "nomic-embed-text"
OLLAMA_BASE_URL: str   = "http://localhost:11434"
OLLAMA_TEMP:     float = 0.1
CHROMA_DIR:      str   = "./chroma_db_cache"

def format_docs(docs: List[Document]) -> str:
    return "\n\n".join(doc.page_content for doc in docs)

SYSTEM_PROMPT: str = """
És o assistente virtual de triagem do SNS24 em Português de Portugal. A tua tarefa é fazer perguntas ao utente para decidir o encaminhamento correto.
Fala diretamente com o utente.

REGRAS DE FUNCIONAMENTO (Cumpre estritamente):
1. Faz APENAS UMA pergunta de cada vez. Aguarda sempre a resposta do utente.
2. NUNCA dês conselhos gerais (como "beba água" ou "descanse"). Apenas faz perguntas de triagem.
3. FOCO ESTRITO CLÍNICO (ANTI-TROLL): Se o utente abordar qualquer tema que não seja saúde humana (ex: cães, mecânica, piadas, assuntos aleatórios), RECUSA imediatamente o tema. Responde de forma curta e pragmática: "Este é o serviço de triagem clínica do SNS24. Apresenta algum sintoma ou problema de saúde?". Não justifiques nem desenvolvas o assunto fora do contexto.
4. NUNCA recuses atendimento CLÍNICO válido.

HIERARQUIA DA TRIAGEM:
PASSO 1: Começa SEMPRE por perguntar se o utente consegue respirar sem dificuldade e se está consciente/lúcido. (Não avances sem saber isto).
PASSO 2: Cruza os sintomas do utente com as REGRAS DO CONTEXTO CLÍNICO abaixo. Faz as perguntas necessárias (ex: temperatura exata, duração) para aplicar a regra.
PASSO 3: Quando a regra do contexto estiver preenchida, dá a decisão final (ex: "Ligue 112", ou "Fique em Autocuidado").

REGRAS DO CONTEXTO CLÍNICO:
{context}
"""

from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document

def carregar_e_indexar_regras(caminho_ficheiro: str = REGRAS_PATH, base_url: str = OLLAMA_BASE_URL) -> Chroma:
    logger.info(f"A carregar regras de '{caminho_ficheiro}'...")
    path = Path(caminho_ficheiro)
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro não encontrado em '{caminho_ficheiro}'.\n")
    
    texto_completo = path.read_text(encoding="utf-8")
    
    # 1. Definir os cabeçalhos Markdown a respeitar
    headers_to_split_on = [
        ("##", "Protocolo"),
        ("###", "Nivel_Urgencia")
    ]
    
    # 2. Dividir o texto respeitando a hierarquia clínica
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    chunks = markdown_splitter.split_text(texto_completo)
    
    for i, chunk in enumerate(chunks, 1):
        chunk.metadata["fonte"] = path.name
        chunk.metadata["chunk_id"] = str(i)
        chunk.metadata["chunk_total"] = str(len(chunks))
    
    logger.info(f"Gerados {len(chunks)} chunks de conhecimento (Formatados por Markdown).")
    
    # Limpar cache antigo para evitar conflitos de schema do SQLite
    chroma_path = Path(CHROMA_DIR)
    if chroma_path.exists():
        shutil.rmtree(chroma_path)
        logger.info("Cache ChromaDB anterior removido.")

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=base_url)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name="siad_regras",
    )
    logger.info(f"✔ Vector Store criada em '{CHROMA_DIR}' — {len(chunks)} vectores indexados.")
    return vectorstore

from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

def construir_chain_rag(retriever, modelo: str = OLLAMA_MODEL, base_url: str = OLLAMA_BASE_URL, temp: float = OLLAMA_TEMP):
    logger.info(f"A construir chain RAG (History-Aware) — modelo: '{modelo}'")

    try:
        llm = ChatOllama(model=modelo, base_url=base_url, temperature=temp)
    except Exception as exc:
        raise RuntimeError(f"Falha ao criar ChatOllama: {exc}") from exc

    # 1. Prompt para contextualizar a pergunta (O "Tradutor" de histórico)
    contextualize_q_system_prompt = (
        "Dada a história da conversa e a última interação do utente, "
        "reescreve a frase do utente para que seja uma afirmação ou pergunta completa e "
        "independente do contexto passado. NÃO respondas, apenas reformula a frase "
        "para que possa ser usada numa pesquisa de base de dados clínica."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])
    
    # Criar o Retriever Inteligente
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    # 2. Prompt principal da Triagem (O que tu já tinhas, ajustado para as chains modernas)
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])
    
    # Construir a Chain final
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    logger.info("✔ Chain RAG History-Aware construída com sucesso.")
    return rag_chain

class SIADRagEngine:
    def __init__(
        self,
        regras_path:  str   = REGRAS_PATH,
        ollama_model: str   = OLLAMA_MODEL,
        ollama_url:   str   = OLLAMA_BASE_URL,
        temperatura:  float = OLLAMA_TEMP,
    ) -> None:
        self.regras_path     = regras_path
        self.ollama_model    = ollama_model
        self.ollama_url      = ollama_url
        self.temperatura     = temperatura

        self._vectorstore                  = None
        self._retriever                    = None
        self._chain                        = None
        self._chat_history: List[BaseMessage] = []
        self._pronto:    bool              = False

    def inicializar(self) -> "SIADRagEngine":
        logger.info("=" * 62)
        logger.info(f"  SIAD — Motor RAG LCEL | modelo: {self.ollama_model}")
        logger.info("=" * 62)

        self._vectorstore = carregar_e_indexar_regras(self.regras_path, self.ollama_url)
        self._retriever = self._vectorstore.as_retriever(search_kwargs={"k": 3})
        
        self._chain = construir_chain_rag(
            retriever=self._retriever,
            modelo=self.ollama_model,
            base_url=self.ollama_url,
            temp=self.temperatura,
        )

        self._pronto = True
        logger.info("=" * 62)
        logger.info("  ✅ Motor RAG pronto para triagem.")
        logger.info("=" * 62)
        return self

    def nova_sessao(self) -> None:
        self._chat_history = []
        logger.info("✔ Nova sessão — histórico limpo.")

    def get_history(self) -> List[dict]:
        """Devolve o histórico atual de mensagens de forma legível."""
        historico_legivel = []
        for msg in self._chat_history:
            if isinstance(msg, HumanMessage):
                historico_legivel.append({"role": "utente", "content": msg.content})
            elif isinstance(msg, AIMessage):
                historico_legivel.append({"role": "assistente", "content": msg.content})
        return historico_legivel

    def chat_with_bot(self, user_input: str) -> Tuple[str, List[Document]]:
        if not self._pronto or self._chain is None:
            raise RuntimeError("Motor não inicializado.")

        if not user_input.strip():
            return "Não entendi. Pode repetir, por favor?", []

        # Usar a nova chain que trata de TUDO (Reescrita -> Recuperação -> Geração)
        resposta_chain = self._chain.invoke({
            "input": user_input, # A nova chain usa 'input' em vez de 'question'
            "chat_history": self._chat_history,
        })

        resposta = resposta_chain["answer"]
        docs_recuperados = resposta_chain["context"]

        # Atualizar histórico
        self._chat_history.append(HumanMessage(content=user_input))
        self._chat_history.append(AIMessage(content=resposta))

        logger.info(
            f"Resposta: {len(resposta)} chars | "
            f"Histórico: {len(self._chat_history) // 2} turno(s) | "
            f"Chunks: {len(docs_recuperados)}"
        )
        
        return resposta, docs_recuperados

        