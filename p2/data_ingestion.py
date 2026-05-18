"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          SIAD — Sistema Inteligente de Apoio à Decisão Clínica             ║
║          Pipeline de Ingestão de Dados — Sprint 1                          ║
║          Fonte: Manual SNS24 — Algoritmos de Triagem (2022_V4.0)           ║
╚══════════════════════════════════════════════════════════════════════════════╝
 
Módulo: data_ingestion.py
Objetivo: Carrega o ficheiro SISD_SNS24_Triagem.docx, divide o texto em
          chunks semânticos preservando regras clínicas completas, gera
          embeddings multilingues e persiste numa Vector Store ChromaDB local.
 
Dependências (instalar via pip):
    pip install langchain langchain-community langchain-chroma
    pip install sentence-transformers
    pip install docx2txt python-docx
    pip install chromadb
"""
 
# ─── Imports da Biblioteca Padrão ───────────────────────────────────────────
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional
 
# ─── Imports LangChain ──────────────────────────────────────────────────────
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
 
# ─── Configuração de Logging ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("SIAD.DataIngestion")
 
 
# ════════════════════════════════════════════════════════════════════════════
# CONSTANTES DE CONFIGURAÇÃO
# ════════════════════════════════════════════════════════════════════════════
 
# Caminho para o ficheiro .docx de origem
DOCX_PATH: str = "SISD_SNS24_Triagem.docx"
 
# Pasta onde a Vector Store ChromaDB será persistida
CHROMA_DB_DIR: str = "./chroma_db"
 
# Nome da coleção dentro do ChromaDB
COLLECTION_NAME: str = "sns24_triagem"
 
# Modelo de embeddings — multilíngue e leve, ideal para Português de Portugal.
# paraphrase-multilingual-MiniLM-L12-v2:
#   • Treinado em 50+ línguas incluindo PT
#   • ~120MB, rápido em CPU
#   • Excelente para frases clínicas e regras médicas
EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
 
# ── Parâmetros de Chunking Semântico ────────────────────────────────────────
# chunk_size = 900 caracteres:
#   • Suficiente para conter uma regra completa (ex: F-R4 com condição + nota)
#   • Evita cortar a meio de uma tabela de variáveis ou de uma disposição final
# chunk_overlap = 180 caracteres:
#   • Garante que o contexto entre regras adjacentes é preservado
#   • Crítico para regras que referenciam variáveis definidas no chunk anterior
CHUNK_SIZE: int = 900
CHUNK_OVERLAP: int = 180
 
# Separadores ordenados do mais estrutural para o mais granular.
# O RecursiveCharacterTextSplitter tenta cada separador na ordem indicada:
#   1. "\n\n"  → quebras de parágrafo duplas (mudança de secção/regra)
#   2. "\n"    → quebras de linha simples (linhas dentro de uma tabela/regra)
#   3. ". "    → fim de frase (fallback para frases longas)
#   4. " "     → espaço (último recurso)
#   5. ""      → caracter a caracter (evitar a todo o custo)
TEXT_SEPARATORS: List[str] = ["\n\n", "\n", ". ", " ", ""]
 
 
# ════════════════════════════════════════════════════════════════════════════
# FUNÇÃO 1: CARREGAMENTO DO DOCUMENTO
# ════════════════════════════════════════════════════════════════════════════
 
def carregar_documento(caminho_ficheiro: str) -> List[Document]:
    """
    Carrega um ficheiro .docx utilizando o Docx2txtLoader do LangChain.
 
    O Docx2txtLoader preserva todo o texto do documento Word, incluindo
    conteúdo de tabelas (onde residem as regras de produção SNS24),
    o que é crítico para este projeto.
 
    Args:
        caminho_ficheiro: Caminho relativo ou absoluto para o ficheiro .docx.
 
    Returns:
        Lista de objetos Document do LangChain (normalmente um por ficheiro).
 
    Raises:
        FileNotFoundError: Se o ficheiro não existir no caminho indicado.
        ValueError: Se o ficheiro não for um .docx válido ou estiver vazio.
    """
    logger.info(f"A carregar documento: '{caminho_ficheiro}'")
 
    # Verificar existência do ficheiro antes de tentar abrir
    caminho = Path(caminho_ficheiro)
    if not caminho.exists():
        raise FileNotFoundError(
            f"Ficheiro não encontrado: '{caminho_ficheiro}'\n"
            f"  → Diretório de trabalho atual: {Path.cwd()}\n"
            f"  → Certifique-se que o .docx está na mesma pasta que este script."
        )
 
    if not caminho.suffix.lower() == ".docx":
        raise ValueError(
            f"Extensão inválida: '{caminho.suffix}'. Esperado: '.docx'"
        )
 
    # Carregamento com Docx2txtLoader
    loader = Docx2txtLoader(str(caminho))
    documentos: List[Document] = loader.load()
 
    if not documentos:
        raise ValueError(
            f"O ficheiro '{caminho_ficheiro}' foi carregado mas está vazio."
        )
 
    # Enriquecer metadados de origem para rastreabilidade nos resultados RAG
    for doc in documentos:
        doc.metadata.update({
            "fonte": "Manual SNS24 — Triagem 2022_V4.0",
            "modulo": "Febre | Dispneia | Tosse",
            "projeto": "SIAD",
        })
 
    total_chars = sum(len(doc.page_content) for doc in documentos)
    logger.info(
        f"✔ Documento carregado com sucesso: "
        f"{len(documentos)} página(s), {total_chars:,} caracteres totais."
    )
    return documentos
 
 
# ════════════════════════════════════════════════════════════════════════════
# FUNÇÃO 2: DIVISÃO EM CHUNKS SEMÂNTICOS
# ════════════════════════════════════════════════════════════════════════════
 
def dividir_em_chunks(
    documentos: List[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Document]:
    """
    Divide os documentos em chunks semânticos usando RecursiveCharacterTextSplitter.
 
    Estratégia adotada para o documento SNS24:
    - Os separadores respeitam a estrutura do documento (parágrafos → linhas → frases)
    - O chunk_size (900) é calibrado para conter uma regra completa com a sua
      nota clínica (📌), evitando cortar a condição SE da conclusão ENTÃO
    - O chunk_overlap (180) assegura que variáveis definidas no início de uma
      secção estão disponíveis nos chunks que contêm as regras que as usam
 
    Args:
        documentos:    Lista de Documents LangChain a dividir.
        chunk_size:    Tamanho máximo de cada chunk em caracteres.
        chunk_overlap: Sobreposição entre chunks consecutivos em caracteres.
 
    Returns:
        Lista de Documents com o texto dividido em chunks semânticos.
 
    Raises:
        ValueError: Se a lista de documentos estiver vazia.
    """
    if not documentos:
        raise ValueError("Lista de documentos vazia — impossível criar chunks.")
 
    logger.info(
        f"A dividir documento em chunks "
        f"(chunk_size={chunk_size}, overlap={chunk_overlap})..."
    )
 
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=TEXT_SEPARATORS,
        # length_function padrão = len() em caracteres
        # keep_separator=True preserva o separador no início do chunk seguinte,
        # útil para manter a integridade de linhas de tabela
        keep_separator=True,
        add_start_index=True,   # Adiciona metadado 'start_index' para depuração
    )
 
    chunks: List[Document] = splitter.split_documents(documentos)
 
    if not chunks:
        raise ValueError("O splitter não gerou nenhum chunk. Verifique o documento.")
 
    # Enriquecer cada chunk com o seu índice para rastreabilidade
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i
        chunk.metadata["chunk_total"] = len(chunks)
 
    logger.info(
        f"✔ {len(chunks)} chunks gerados. "
        f"Tamanho médio: {sum(len(c.page_content) for c in chunks) // len(chunks)} chars."
    )
 
    # Log de diagnóstico: mostrar os primeiros 3 chunks para validação
    logger.debug("── Primeiros 3 chunks (diagnóstico) ──")
    for i, chunk in enumerate(chunks[:3]):
        logger.debug(
            f"  Chunk #{i}: {len(chunk.page_content)} chars | "
            f"Início: '{chunk.page_content[:80].strip()}...'"
        )
 
    return chunks
 
 
# ════════════════════════════════════════════════════════════════════════════
# FUNÇÃO 3: CRIAÇÃO DO MODELO DE EMBEDDINGS
# ════════════════════════════════════════════════════════════════════════════
 
def criar_modelo_embeddings(
    nome_modelo: str = EMBEDDING_MODEL,
) -> HuggingFaceEmbeddings:
    """
    Inicializa o modelo de embeddings HuggingFace para Português de Portugal.
 
    Modelo escolhido: paraphrase-multilingual-MiniLM-L12-v2
    Justificação:
    - Treinado em 50+ línguas incluindo PT-PT
    - Arquitetura MiniLM (12 camadas) — boa relação performance/velocidade
    - Dimensão de vetor: 384 — eficiente para ChromaDB local
    - Funciona bem em CPU sem GPU dedicada (importante para projeto académico)
    - Adequado para frases clínicas curtas como as regras de produção SNS24
 
    Args:
        nome_modelo: Identificador HuggingFace do modelo de embeddings.
 
    Returns:
        Instância configurada de HuggingFaceEmbeddings.
 
    Raises:
        RuntimeError: Se o modelo não puder ser descarregado/inicializado.
    """
    logger.info(f"A inicializar modelo de embeddings: '{nome_modelo}'")
    logger.info("  (Na primeira execução, o modelo será descarregado ~120MB)")
 
    try:
        modelo = HuggingFaceEmbeddings(
            model_name=nome_modelo,
            model_kwargs={"device": "cpu"},  # Forçar CPU (compatível sem GPU)
            encode_kwargs={
                "normalize_embeddings": True,  # Normalizar para cosine similarity
                "batch_size": 32,              # Processar 32 chunks por batch
            },
            # Guardar modelo em cache local para evitar novo download
            cache_folder="./models_cache",
        )
    except Exception as e:
        raise RuntimeError(
            f"Falha ao inicializar modelo de embeddings '{nome_modelo}': {e}\n"
            f"  → Verifique a ligação à internet na primeira execução.\n"
            f"  → Execute: pip install sentence-transformers"
        ) from e
 
    logger.info("✔ Modelo de embeddings inicializado com sucesso.")
    return modelo
 
 
# ════════════════════════════════════════════════════════════════════════════
# FUNÇÃO 4: CRIAÇÃO E PERSISTÊNCIA DA VECTOR STORE
# ════════════════════════════════════════════════════════════════════════════
 
def criar_vector_store(
    chunks: List[Document],
    modelo_embeddings: HuggingFaceEmbeddings,
    diretorio_db: str = CHROMA_DB_DIR,
    nome_colecao: str = COLLECTION_NAME,
) -> Chroma:
    """
    Cria ou atualiza uma Vector Store ChromaDB persistente com os chunks indexados.
 
    A ChromaDB é uma base de dados vetorial open-source que persiste os vetores
    em disco (pasta ./chroma_db), permitindo que as consultas RAG sejam feitas
    sem re-indexar o documento em cada execução.
 
    Se a coleção já existir (execuções subsequentes), é recriada do zero para
    garantir consistência com o documento fonte atual.
 
    Args:
        chunks:             Lista de Document chunks a indexar.
        modelo_embeddings:  Modelo HuggingFace para gerar os vetores.
        diretorio_db:       Pasta local onde o ChromaDB será persistido.
        nome_colecao:       Nome da coleção dentro do ChromaDB.
 
    Returns:
        Instância da Chroma Vector Store pronta para consultas.
 
    Raises:
        RuntimeError: Se a criação da Vector Store falhar.
    """
    logger.info(
        f"A criar Vector Store ChromaDB em '{diretorio_db}' "
        f"(coleção: '{nome_colecao}')..."
    )
 
    # Garantir que a pasta de destino existe
    os.makedirs(diretorio_db, exist_ok=True)
 
    try:
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=modelo_embeddings,
            persist_directory=diretorio_db,
            collection_name=nome_colecao,
            collection_metadata={
                "descricao": "Algoritmos de triagem clínica SNS24 — SIAD",
                "versao": "2022_V4.0",
                "sintomas": "Febre, Dispneia, Tosse",
            },
        )
    except Exception as e:
        raise RuntimeError(
            f"Falha ao criar Vector Store ChromaDB: {e}\n"
            f"  → Execute: pip install chromadb langchain-chroma"
        ) from e
 
    logger.info(
        f"✔ Vector Store criada com sucesso: "
        f"{vector_store._collection.count()} vetores indexados."
    )
    return vector_store
 
 
# ════════════════════════════════════════════════════════════════════════════
# FUNÇÃO 5: CONSULTA DE TESTE À VECTOR STORE
# ════════════════════════════════════════════════════════════════════════════
 
def executar_query_teste(
    vector_store: Chroma,
    query: str,
    k: int = 3,
) -> List[Document]:
    """
    Executa uma consulta de similaridade semântica na Vector Store.
 
    Utiliza a distância cosseno entre o embedding da query e os embeddings
    dos chunks indexados para recuperar os k documentos mais relevantes.
 
    Args:
        vector_store: Instância ChromaDB inicializada.
        query:        Pergunta em linguagem natural (Português).
        k:            Número de chunks a recuperar (top-k por similaridade).
 
    Returns:
        Lista dos k Documents mais relevantes para a query.
    """
    logger.info(f"A executar query de teste: '{query}'")
    resultados = vector_store.similarity_search(query=query, k=k)
    logger.info(f"✔ {len(resultados)} chunk(s) recuperado(s).")
    return resultados
 
 
# ════════════════════════════════════════════════════════════════════════════
# FUNÇÃO PRINCIPAL: PIPELINE COMPLETO DE INGESTÃO
# ════════════════════════════════════════════════════════════════════════════
 
def executar_pipeline_ingestao(
    caminho_docx: str = DOCX_PATH,
    diretorio_chroma: str = CHROMA_DB_DIR,
) -> Optional[Chroma]:
    """
    Orquestra o pipeline completo de ingestão de dados RAG:
 
        [.docx] → Carregamento → Chunking → Embeddings → ChromaDB
 
    Args:
        caminho_docx:      Caminho para o ficheiro .docx de origem.
        diretorio_chroma:  Pasta de destino para a Vector Store ChromaDB.
 
    Returns:
        Instância Chroma pronta para consultas, ou None em caso de erro.
    """
    logger.info("=" * 70)
    logger.info("  SIAD — Pipeline de Ingestão de Dados — SNS24 Triagem")
    logger.info("=" * 70)
 
    try:
        # PASSO 1: Carregamento do documento .docx
        documentos = carregar_documento(caminho_docx)
 
        # PASSO 2: Divisão em chunks semânticos
        chunks = dividir_em_chunks(documentos)
 
        # PASSO 3: Inicialização do modelo de embeddings
        modelo_embeddings = criar_modelo_embeddings()
 
        # PASSO 4: Criação e persistência da Vector Store
        vector_store = criar_vector_store(chunks, modelo_embeddings, diretorio_chroma)
 
        logger.info("=" * 70)
        logger.info("  ✅ Pipeline de ingestão concluído com sucesso!")
        logger.info(f"  📁 Vector Store persistida em: {Path(diretorio_chroma).resolve()}")
        logger.info("=" * 70)
 
        return vector_store
 
    except FileNotFoundError as e:
        logger.error(f"❌ ERRO — Ficheiro não encontrado:\n  {e}")
        return None
    except ValueError as e:
        logger.error(f"❌ ERRO — Dados inválidos:\n  {e}")
        return None
    except RuntimeError as e:
        logger.error(f"❌ ERRO — Falha de execução:\n  {e}")
        return None
    except Exception as e:
        logger.error(f"❌ ERRO INESPERADO: {type(e).__name__}: {e}")
        return None
 
 
# ════════════════════════════════════════════════════════════════════════════
# BLOCO DE TESTE INTEGRADO
# ════════════════════════════════════════════════════════════════════════════
 
if __name__ == "__main__":
 
    # ── FASE 1: Executar o pipeline de ingestão completo ──────────────────
    vector_store = executar_pipeline_ingestao(
        caminho_docx=DOCX_PATH,
        diretorio_chroma=CHROMA_DB_DIR,
    )
 
    # Se a ingestão falhou, terminar com código de erro
    if vector_store is None:
        logger.error("Pipeline de ingestão falhou. A terminar.")
        sys.exit(1)
 
    # ── FASE 2: Queries de teste para validação do RAG ────────────────────
    print("\n" + "═" * 70)
    print("  🔍 TESTE DE CONSULTA À VECTOR STORE")
    print("═" * 70)
 
    queries_teste = [
        {
            "pergunta": "Quais são as regras para febre superior a 40 graus?",
            "descricao": "Regra F-R4 — Febre ≥ 40°C → ADR-SU",
        },
        {
            "pergunta": "Quais são os sinais de alarme de emergência (Red Flags)?",
            "descricao": "Secção 7 — Red Flags de emergência absoluta",
        },
        {
            "pergunta": "O que fazer quando o utente tem cianose labial ou não consegue falar?",
            "descricao": "Regra D-R1 — Dispneia grave → INEM/112",
        },
    ]
 
    for idx, item in enumerate(queries_teste, start=1):
        print(f"\n{'─' * 70}")
        print(f"  Query #{idx}: {item['pergunta']}")
        print(f"  Contexto esperado: {item['descricao']}")
        print(f"{'─' * 70}")
 
        try:
            resultados = executar_query_teste(
                vector_store=vector_store,
                query=item["pergunta"],
                k=3,
            )
 
            for r_idx, doc in enumerate(resultados, start=1):
                print(f"\n  [Chunk #{r_idx} | ID: {doc.metadata.get('chunk_id', '?')}]")
                print(f"  Fonte: {doc.metadata.get('fonte', 'N/A')}")
                # Mostrar os primeiros 500 caracteres do chunk para validação
                preview = doc.page_content[:500].strip()
                if len(doc.page_content) > 500:
                    preview += "..."
                print(f"\n  {preview}\n")
 
        except Exception as e:
            logger.error(f"  ❌ Falha na query #{idx}: {e}")
 
    print("\n" + "═" * 70)
    print("  ✅ Teste concluído. Vector Store funcional e pronta para RAG.")
    print(f"  📁 ChromaDB persistida em: {Path(CHROMA_DB_DIR).resolve()}")
    print("═" * 70 + "\n")