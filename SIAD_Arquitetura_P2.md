# SIAD — Explicação da Arquitetura P2
### Base para a Secção do Relatório Académico
> **Cadeira:** SIAD · **Projeto:** Sistema Inteligente de Suporte à Decisão (SISD)  
> **Âmbito:** Parte 2 — Motor RAG + Interface Conversacional de Triagem Clínica SNS24

---

## 1. Visão Geral do Sistema

O sistema implementado é um **Agente Conversacional de Triagem Médica** baseado na arquitectura *Retrieval-Augmented Generation* (RAG). Em vez de depender exclusivamente do conhecimento interno do modelo de linguagem — que pode ser impreciso, desactualizado ou inventado —, o agente recupera dinamicamente os protocolos clínicos reais do SNS24 a partir de uma base de dados vectorial local, e injeta-os como contexto em cada resposta.

O resultado é um sistema que:

- Responde **exclusivamente** com base nas regras de triagem do Manual SNS24 (versão 2022_V4.0)
- Mantém **memória conversacional** ao longo de uma sessão de triagem
- Escala automaticamente o nível de urgência, terminando com uma **Disposição Final** estruturada
- Corre **completamente offline**, sem enviar dados clínicos para servidores externos

---

## 2. Stack Tecnológica

| Camada | Tecnologia | Justificação |
|---|---|---|
| **Linguagem** | Python 3.11 | Ecossistema LangChain; tipagem com Type Hints |
| **Orquestração LLM** | LangChain LCEL (≥ 0.2) | Pipeline declarativo com operador `\|`; sem classes legacy |
| **Vector Store** | ChromaDB (local) | Open-source; persiste em disco; zero latência de rede |
| **Embeddings** | `paraphrase-multilingual-MiniLM-L12-v2` | Suporte PT-PT; ~120 MB; eficiente em CPU |
| **LLM Local** | Ollama + Phi3 | Inferência local; dados clínicos não saem da máquina |
| **Interface** | Streamlit | Prototipagem rápida; `st.chat_message` nativo |
| **Fonte de Conhecimento** | Manual SNS24 2022_V4.0 (`.docx`) | Autoridade clínica oficial do SNS português |

---

## 3. Arquitectura em Três Sprints

### Sprint 1 — Pipeline de Ingestão (`data_ingestion.py`)

**Objectivo:** Transformar o documento `.docx` do SNS24 numa base de dados vectorial pesquisável.

```
[SISD_SNS24_Triagem.docx]
         │
         ▼ Docx2txtLoader
[Texto extraído + metadados de rastreabilidade]
         │
         ▼ RecursiveCharacterTextSplitter
         │   chunk_size=900, overlap=180
         │   separadores: \n\n → \n → ". " → " "
[N chunks semânticos — cada um contém uma regra clínica completa]
         │
         ▼ HuggingFaceEmbeddings (MiniLM-L12-v2)
[Vectores de 384 dimensões por chunk]
         │
         ▼ Chroma.from_documents()
[./chroma_db  —  Vector Store persistida em disco]
```

**Decisões de design críticas:**

- **`chunk_size=900`:** Dimensionado para conter uma regra de produção SNS24 completa (condição `SE` + conclusão `ENTÃO` + nota clínica), sem a cortar a meio.
- **`chunk_overlap=180`:** Garante que variáveis definidas no início de uma secção estão disponíveis nos chunks que contêm as regras que as referenciam.
- **Metadados enriquecidos:** Cada chunk recebe `fonte`, `modulo`, `chunk_id` e `start_index`, que são expostos no Painel de Debug da interface para prova de funcionamento do RAG.

---

### Sprint 2 — Motor RAG LCEL (`rag_engine.py`)

**Objectivo:** Ligar a Vector Store ao LLM local através de uma chain conversacional moderna.

#### 2.1 Arquitectura LCEL (LangChain Expression Language)

A versão final do motor usa **LCEL pura** — sem `ConversationalRetrievalChain` nem `ConversationBufferMemory` (classes removidas no LangChain ≥ 1.x). O pipeline completo em notação pipe:

```python
chain = RunnableParallel(
    context  = extrair_question | retriever | format_docs,
    question = extrair_question,
    chat_history = extrair_history,
) | ChatPromptTemplate | ChatOllama(model="phi3") | StrOutputParser()
```

**Detalhe técnico — o problema do `RunnableParallel`:**  
O retriever ChromaDB só aceita `str` como input, mas o input da chain é um `dict`. A solução foi usar `RunnableLambda(lambda x: x["question"])` para extrair apenas a string da pergunta antes de a passar ao retriever, mantendo as restantes chaves via passthrough.

#### 2.2 Gestão de Memória sem Classes Legacy

O histórico conversacional é gerido como `List[BaseMessage]` directamente na classe `SIADRagEngine`. A cada turno:

```
Utente envia mensagem
    → chain.invoke({"question": input, "chat_history": self._chat_history})
    → chat_history.append(HumanMessage(content=input))
    → chat_history.append(AIMessage(content=resposta))
```

O `MessagesPlaceholder(variable_name="chat_history")` no `ChatPromptTemplate` injeta estes objectos directamente como mensagens reais no diálogo — não como string concatenada — o que o Phi3 interpreta com muito maior fidelidade.

#### 2.3 Separação Retriever / Chain

O retriever é invocado **separadamente** da chain principal:

```python
fontes = self._retriever.invoke(user_input)   # → List[Document] (para exposição)
resposta = self._chain.invoke({...})           # → str (para o utente)
```

Esta separação é necessária porque a chain LCEL apenas expõe o output final (`str`), não os documentos intermédios. Devolver as fontes separadamente permite ao `app.py` mostrá-las no painel de debug sem modificar a chain.

---

### Sprint 3 — Interface Web Streamlit (`app.py`)

**Objectivo:** Interface profissional que consome o motor RAG e apresenta o painel de debug.

#### Componentes principais

| Componente Streamlit | Função |
|---|---|
| `st.set_page_config` | Título, ícone 🏥 e layout `wide` |
| `@st.cache_resource` | Instancia `SIADRagEngine` uma única vez por processo |
| `st.session_state` | Persiste `messages`, `last_sources` e `turn_count` entre reruns |
| `st.chat_message` | Renderiza o histórico de chat com avatares |
| `st.chat_input` | Input do utente fixo no fundo da página |
| `st.sidebar` | Painel de Debug do Arquiteto (chunks + métricas + configuração) |

#### Porquê `@st.cache_resource` é crítico

O Streamlit **re-executa o script completo** a cada mensagem enviada. Sem o decorator, a ChromaDB (~120 MB de vectores) e o modelo de embeddings seriam recarregados dezenas de vezes por sessão. O `@st.cache_resource` mantém a instância em memória partilhada entre todos os reruns — a inicialização corre uma única vez por arranque do servidor.

#### Dois históricos distintos (separação de responsabilidades)

| Onde | Tipo | Para quê |
|---|---|---|
| `st.session_state.messages` | `List[dict]` com `role` e `content` | Renderizar o chat na UI Streamlit |
| `engine._chat_history` | `List[BaseMessage]` LangChain | Injetar no `MessagesPlaceholder` LCEL |

O `app.py` nunca manipula o segundo — delega completamente à `SIADRagEngine`.

---

## 4. Engenharia de Prompts — O Desafio do Phi3

### 4.1 O Problema: "Alignment Tax" do Phi3

O modelo Phi3 (Microsoft) foi extensivamente *fine-tuned* para ser útil, inofensivo e honesto. Este alinhamento cria o que internamente designámos por **"Alignment Tax"** no contexto clínico: o modelo resiste sistematicamente a ser restritivo.

Os comportamentos problemáticos observados:

- **Resposta na terceira pessoa:** "Avalie se o utente tem febre..." em vez de falar directamente ao utente
- **Exposição da sintaxe interna:** O modelo reproduzia literalmente a estrutura `SE (Condição) ENTÃO (Conclusão)` do manual
- **Raciocínio clínico ingénuo:** Aceitava "36ºC de febre" como febre clínica sem comparar com o limiar definido no contexto (≥ 38ºC)
- **Tendência para dar conselhos gerais:** Em vez de se limitar ao contexto recuperado, usava conhecimento médico geral de treino

### 4.2 A Solução: System Prompt Híbrido

A solução adoptada combina duas estratégias num único System Prompt:

**Estratégia 1 — Ordens absolutas com exemplos explícitos de certo/errado (topo do prompt)**

Em vez de instruções abstractas ("fala na segunda pessoa"), usámos pares concretos:

```
✅ CORRETO:  "Compreendo. Consegue dizer-me se..."
❌ PROIBIDO: "Avalie se o utente..." / "O assistente deve..."
```

Modelos de linguagem pequenos como o Phi3 respondem muito melhor a exemplos do que a meta-instruções. O par ✅/❌ elimina a ambiguidade de interpretação.

**Estratégia 2 — Raciocínio clínico com casos de uso explícitos**

Para o problema da validação de valores numéricos, injectámos o caso exacto observado como exemplo obrigatório:

```
• O utente diz "tenho 36ºC" → o contexto define febre como >= 38ºC →
  CONCLUIS internamente: 36ºC NÃO é febre clínica.
  Responde: "36ºC está dentro dos valores normais..."
```

**Estrutura final do prompt:**

```
[BLOCO 1] Identidade e Voz       → Quem és + exemplos ✅/❌
[BLOCO 2] Raciocínio Clínico     → Como validar valores + casos de uso
[BLOCO 3] Protocolo de Interação → Hierarquia Red Flags → Triagem → Disposição
[BLOCO 4] {context}              → Chunks SNS24 injectados pelo retriever
```

A colocação da lógica clínica **antes** do `{context}` é deliberada: garante que as regras de comportamento têm precedência sobre o conteúdo recuperado, impedindo que o modelo "siga" a sintaxe do manual em vez das instruções do prompt.

---

## 5. Fluxo de uma Interação Completa

```
Utente: "Tenho 36ºC de febre, muita tosse e garganta inflamada"
                │
                ▼
   [app.py] st.chat_input captura o input
                │
                ▼
   [SIADRagEngine.chat_with_bot()]
                │
        ┌───────┴───────┐
        ▼               ▼
   retriever         chain LCEL
   .invoke(input)    .invoke({question, chat_history})
        │               │
        ▼               ▼
   4 chunks SNS24   RunnableParallel
   (List[Document]) → format_docs → {context: str}
                        │
                        ▼
                   ChatPromptTemplate
                   (system + history + human)
                        │
                        ▼
                   ChatOllama(phi3)
                        │
                        ▼
                   StrOutputParser → resposta: str
                │
                ▼
   "36ºC está dentro dos valores normais, por isso não se
    trata de febre clínica. Relativamente à tosse —
    há quanto tempo tem este sintoma?"
                │
                ▼
   [app.py] Renderiza resposta + actualiza sidebar com 4 chunks
```

---

## 6. Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                    SIAD — Arquitectura P2                   │
│                                                             │
│  ┌──────────────┐    ┌───────────────┐    ┌─────────────┐  │
│  │data_ingestion│    │  rag_engine   │    │    app.py   │  │
│  │    .py       │    │     .py       │    │ (Streamlit) │  │
│  │              │    │               │    │             │  │
│  │ Docx2txt     │    │ carregar_     │    │ @cache_     │  │
│  │ Splitter     │───▶│ vector_store  │◀───│ resource    │  │
│  │ Embeddings   │    │               │    │             │  │
│  │ Chroma.from_ │    │ construir_    │    │ session_    │  │
│  │ documents()  │    │ chain_lcel    │    │ state       │  │
│  └──────────────┘    │               │    │             │  │
│         │            │ SIADRagEngine │    │ chat_msg    │  │
│         ▼            │ .chat_with_   │    │ chat_input  │  │
│  ┌──────────────┐    │  bot()        │    │ sidebar     │  │
│  │  ./chroma_db │    └───────────────┘    └─────────────┘  │
│  │ (Vector Store│              ▲                            │
│  │  persistida) │              │                            │
│  └──────────────┘    ┌─────────────────┐                   │
│                      │  Ollama (phi3)  │                   │
│                      │  localhost:11434│                   │
│                      └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```
