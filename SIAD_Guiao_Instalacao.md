# SIAD — Guião de Instalação e Execução
### README "à prova de bala" para a Equipa
> Segue este guião **na ordem exacta** indicada. Saltar passos causa erros.  
> Tempo estimado desde o `git clone` até à interface a funcionar: **~15 minutos** (+ download do modelo ~2 GB)

---

## Pré-requisitos

Antes de começar, confirma que tens instalado:

- **Python 3.11** (verificar: `python --version`)
- **Git** (verificar: `git --version`)
- **Ligação à internet** no Passo 1 e Passo 3 (depois podes trabalhar offline)
- **~4 GB de espaço livre em disco** (modelo Phi3 ~2 GB + dependências)

---

## Passo 1 — Instalar o Ollama e descarregar o modelo Phi3

O Ollama é o motor que corre o modelo de linguagem localmente na tua máquina. Os dados clínicos **nunca saem do teu computador**.

### 1.1 Instalar o Ollama

| Sistema Operativo | Instruções |
|---|---|
| **Windows** | Descarregar o instalador em [https://ollama.com/download](https://ollama.com/download) e executar |
| **macOS** | `brew install ollama` **ou** descarregar o `.dmg` em [https://ollama.com/download](https://ollama.com/download) |
| **Linux** | `curl -fsSL https://ollama.com/install.sh \| sh` |

Verificar instalação:
```bash
ollama --version
```

### 1.2 Descarregar o modelo Phi3

```bash
ollama pull phi3
```

> ⚠️ **Atenção:** O modelo tem ~2 GB. Aguarda até o download completar (a barra de progresso deve chegar a 100%).

### 1.3 Iniciar o servidor Ollama

**Opção A — Deixar a correr em background (recomendado):**

```bash
# Windows / macOS: o Ollama inicia automaticamente após instalação
# Linux:
ollama serve &
```

**Opção B — Numa aba/terminal separado:**
```bash
ollama serve
```

Verificar que está a correr:
```bash
curl http://localhost:11434
# Deve responder: "Ollama is running"
```

> ⚠️ **Mantém o Ollama a correr** durante toda a utilização do SIAD. Se fechar o terminal do `ollama serve`, o SIAD deixa de funcionar.

---

## Passo 2 — Clonar o repositório e criar o ambiente virtual

### 2.1 Clonar o repositório (se ainda não fizeste)

```bash
git clone https://github.com/<teu-grupo>/siad-sns24.git
cd siad-sns24
```

### 2.2 Criar o ambiente virtual Python

> **Porquê?** Para isolar as dependências deste projecto das do teu Python global.

**Windows (PowerShell ou CMD):**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

Se o PowerShell bloquear por política de execução:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Verificar activação (o prompt deve mostrar `(.venv)`):
```bash
which python   # macOS/Linux → deve apontar para .venv/bin/python
python --version  # deve mostrar Python 3.11.x
```

---

## Passo 3 — Instalar as dependências

Com o ambiente virtual activado:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Conteúdo do `requirements.txt`** (para referência):
```
langchain-core
langchain-community
langchain-chroma
langchain-ollama
sentence-transformers
chromadb
streamlit
docx2txt
python-docx
```

> ⏳ A primeira instalação demora 2–5 minutos. O `sentence-transformers` é a dependência mais pesada.

Verificar instalações críticas:
```bash
python -c "import langchain_core; print('LangChain OK')"
python -c "import chromadb; print('ChromaDB OK')"
python -c "import streamlit; print('Streamlit OK')"
```

---

## Passo 4 — ⚠️ OBRIGATÓRIO: Criar a base de dados vectorial (ChromaDB)

> **Este passo é obrigatório** e deve ser executado **antes** de qualquer outro script.  
> A pasta `./chroma_db` **não está no repositório Git** (está no `.gitignore`) porque:
> - Contém vectores binários (~50–200 MB) que tornariam o repo muito pesado
> - Cada máquina deve gerar a sua própria base vectorial a partir do ficheiro `.docx` fonte
> - Garantir que a base está sempre sincronizada com a versão mais recente do documento

Confirma que o ficheiro fonte está presente:
```bash
ls SISD_SNS24_Triagem.docx   # Windows: dir SISD_SNS24_Triagem.docx
```

Executar o pipeline de ingestão:
```bash
python data_ingestion.py
```

**Output esperado (exemplo):**
```
2024-01-15 10:23:01 [INFO] SIAD.DataIngestion — A carregar documento: 'SISD_SNS24_Triagem.docx'
2024-01-15 10:23:02 [INFO] SIAD.DataIngestion — ✔ Documento carregado: 1 página(s), 45,231 caracteres
2024-01-15 10:23:02 [INFO] SIAD.DataIngestion — A dividir em chunks (chunk_size=900, overlap=180)...
2024-01-15 10:23:02 [INFO] SIAD.DataIngestion — ✔ 67 chunks gerados. Tamanho médio: 742 chars.
2024-01-15 10:23:02 [INFO] SIAD.DataIngestion — A inicializar modelo de embeddings...
     (Na primeira execução, descarrega ~120 MB)
2024-01-15 10:23:45 [INFO] SIAD.DataIngestion — ✔ Vector Store criada: 67 vectores indexados.
2024-01-15 10:23:45 [INFO] SIAD.DataIngestion — ✅ Pipeline de ingestão concluído com sucesso!
```

Verificar que a pasta foi criada:
```bash
ls -la chroma_db/   # macOS/Linux
dir chroma_db\      # Windows
```

> ⚠️ **Se este passo falhar**, o `rag_engine.py` e o `app.py` não conseguem arrancar — mostram `FileNotFoundError: ChromaDB não encontrada`.

---

## Passo 5 — Iniciar a interface Streamlit

```bash
streamlit run app.py
```

**Alternativa (se o comando `streamlit` não for reconhecido):**
```bash
python -m streamlit run app.py
```

O Streamlit abre automaticamente o browser em `http://localhost:8501`.  
Se não abrir, copia o URL do terminal e cola no browser.

**Output esperado no terminal:**
```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501

2024-01-15 10:24:10 [INFO] SIAD.RAGEngine.LCEL — A carregar ChromaDB...
2024-01-15 10:24:11 [INFO] SIAD.RAGEngine.LCEL — ✔ ChromaDB carregada — 67 vectores disponíveis.
2024-01-15 10:24:11 [INFO] SIAD.RAGEngine.LCEL — ✔ Chain LCEL construída com sucesso.
2024-01-15 10:24:11 [INFO] SIAD.RAGEngine.LCEL — ✅ Motor RAG pronto para triagem.
```

> ⏳ A **primeira mensagem** demora mais (o Phi3 precisa de carregar em memória). As seguintes são mais rápidas.

---

## Resumo dos Comandos (Execução do Dia-a-Dia)

Depois de ter tudo instalado, para arrancar o projecto basta:

```bash
# 1. Activar o ambiente virtual
source .venv/bin/activate          # macOS/Linux
.venv\Scripts\activate             # Windows

# 2. Garantir que o Ollama está a correr (se não estiver)
ollama serve &                     # macOS/Linux (background)
# Windows: deve já estar a correr como serviço

# 3. Iniciar a interface
streamlit run app.py
```

---

## Resolução de Problemas Comuns

| Erro | Causa Provável | Solução |
|---|---|---|
| `FileNotFoundError: ChromaDB não encontrada` | Passo 4 não foi executado | Correr `python data_ingestion.py` |
| `Connection refused: http://localhost:11434` | Ollama não está a correr | `ollama serve` num terminal separado |
| `ModuleNotFoundError: No module named 'X'` | Ambiente virtual não activado | `source .venv/bin/activate` |
| `FileNotFoundError: SISD_SNS24_Triagem.docx` | Ficheiro `.docx` em falta | Colocar o ficheiro na raiz do projecto |
| `Error: model 'phi3' not found` | Modelo não descarregado | `ollama pull phi3` |
| Interface abre mas não responde | Phi3 ainda a carregar | Aguardar 30–60 segundos na primeira mensagem |
| `streamlit: command not found` | PATH do venv incompleto | Usar `python -m streamlit run app.py` |

---

## Estrutura do Repositório

```
siad-sns24/
│
├── data_ingestion.py        ← Sprint 1: ingestão e criação da ChromaDB
├── rag_engine.py            ← Sprint 2: motor RAG LCEL + SIADRagEngine
├── app.py                   ← Sprint 3: interface Streamlit
│
├── SISD_SNS24_Triagem.docx  ← Fonte de conhecimento clínico (Manual SNS24)
├── requirements.txt         ← Dependências Python
├── .gitignore               ← Inclui: chroma_db/, .venv/, models_cache/
│
├── chroma_db/               ← ⚠️ NÃO ESTÁ NO GIT — gerada pelo Passo 4
└── models_cache/            ← ⚠️ NÃO ESTÁ NO GIT — descarregada automaticamente
```

---

*Guião preparado pela equipa SIAD · Cadeira de SIAD · Para dúvidas, contactar o grupo no canal do projecto.*
