"""
Script: rag_sns24_simples.py
Descrição: Implementação Educativa Procedimental de RAG (Retrieval-Augmented Generation)
Objetivo: Triagem Clínica SNS24 usando Ollama (llama3.2:1b) e LangChain Clássico.
"""

import os
import warnings

# Omitir avisos desnecessários na consola para uma visualização mais limpa
warnings.filterwarnings("ignore")

# 1. Importações da sintaxe LangChain clássica
from langchain.chains import RetrievalQA
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama

def main():
    print("\n" + "="*70)
    print(" INICIALIZANDO O MOTOR RAG (Retrieval-Augmented Generation)")
    print("="*70)
    
    # -------------------------------------------------------------------------
    # PASSO 1: CARREGAMENTO DOS DADOS (Data Ingestion)
    # -------------------------------------------------------------------------
    # O TextLoader lê o ficheiro de regras do SNS24. O sistema precisa desta
    # base de conhecimento porque os LLMs (como o Llama) não foram treinados
    # especificamente com as regras atualizadas do SNS24 português.
    caminho_ficheiro = "sns24Regras.txt"
    print(f"[*] A carregar o ficheiro de conhecimento: {caminho_ficheiro}...")
    
    try:
        loader = TextLoader(caminho_ficheiro, encoding="utf-8")
        documentos = loader.load()
    except Exception as e:
        print(f"[!] Erro ao carregar o ficheiro: {e}")
        return

    # -------------------------------------------------------------------------
    # PASSO 2: CHUNKING (Divisão de Texto)
    # -------------------------------------------------------------------------
    # O LLM e os modelos de embeddings têm um limite de quantos "tokens" (palavras)
    # conseguem processar de uma só vez. O RecursiveCharacterTextSplitter divide
    # as regras completas em "chunks" (blocos) menores de 500 caracteres, com
    # uma sobreposição (overlap) de 50 caracteres para não cortar o sentido a meio.
    print("[*] A dividir o texto em pequenos chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, 
        chunk_overlap=50
    )
    textos_divididos = text_splitter.split_documents(documentos)
    print(f"    -> O ficheiro foi dividido em {len(textos_divididos)} blocos.")

    # -------------------------------------------------------------------------
    # PASSO 3: MODELO DE EMBEDDINGS E BASE DE DADOS VETORIAL
    # -------------------------------------------------------------------------
    # Os embeddings transformam o texto em coordenadas matemáticas (vetores).
    # Usamos o modelo 'nomic-embed-text' através do Ollama local.
    print("[*] A carregar o modelo de Embeddings (nomic-embed-text)...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    # O ChromaDB é a nossa base de dados vetorial.
    # O parâmetro persist_directory guarda os vetores numa pasta no disco,
    # para não termos de os calcular todos de novo na próxima vez que corrermos.
    pasta_chroma = "./chroma_sns24"
    print(f"[*] A criar e guardar a Base de Dados Vetorial em '{pasta_chroma}'...")
    
    vectorstore = Chroma.from_documents(
        documents=textos_divididos,
        embedding=embeddings,
        persist_directory=pasta_chroma
    )

    # O Retriever é a ferramenta de "busca" da base de dados.
    # k=3 significa que quando o utente fizer uma pergunta, o sistema vai 
    # buscar apenas as 3 regras/chunks matematicamente mais relevantes.
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # -------------------------------------------------------------------------
    # PASSO 4: MODELO DE LINGUAGEM (LLM) E PROMPT CHAIN-OF-THOUGHT
    # -------------------------------------------------------------------------
    print("[*] A ligar ao modelo LLM (llama3.2:1b)...")
    # Usamos temperatura=0.1 para as respostas serem determinísticas e 
    # factuais (não queremos que a IA invente diagnósticos).
    llm = ChatOllama(model="llama3.2:1b", temperature=0.1)

    # Prompt Engineering: A técnica "Chain-of-Thought" (Cadeia de Raciocínio)
    # força a IA a pensar passo-a-passo (listar sintomas -> verificar alarme ->
    # determinar urgência -> criar resposta final). Isto reduz alucinações
    # drasticamente e torna o comportamento "explicável".
    system_prompt = """És o Assistente Virtual de Triagem do SNS24.
Usa APENAS o Contexto fornecido para responder à queixa do utente.
Se o contexto não tiver informação suficiente, diz que não tens informação para triar essa situação.

CONTEXTO DE REGRAS SNS24:
{context}

=== ESTRUTURA DE RESPOSTA OBRIGATÓRIA ===
Responde OBRIGATORIAMENTE seguindo exata e rigorosamente esta estrutura numerada:
1. Sintomas identificados: (lista os sintomas que o utente referiu)
2. Sinais de alarme: (indica se há sinais de alarme graves baseados no contexto)
3. Disposição Clínica: (indica o encaminhamento: EMERGÊNCIA 112 / URGÊNCIA / CONSULTA / AUTO-CUIDADO)
4. Resposta ao Utente: (mensagem empática e direta ao utente com a recomendação)
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Queixa do Utente: {question}")
    ])

    # -------------------------------------------------------------------------
    # PASSO 5: CADEIA CLÁSSICA (RetrievalQA)
    # -------------------------------------------------------------------------
    # O RetrievalQA é a sintaxe clássica do LangChain. Ele junta três peças:
    # 1. O LLM (quem gera a resposta)
    # 2. O Retriever (quem vai buscar a informação à Base de Dados)
    # 3. O Prompt (instruções de como agir)
    print("[*] A construir a cadeia de recuperação (RetrievalQA)...")
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff", # "stuff" mete todos os chunks recuperados diretamente no prompt
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )
    
    print("\n" + "="*70)
    print(" ✅ ASSISTENTE SNS24 PRONTO PARA TRIAGEM (Escreva 'sair' para parar)")
    print("="*70 + "\n")

    # -------------------------------------------------------------------------
    # PASSO 6: INTERFACE DE TERMINAL (Loop Infinito)
    # -------------------------------------------------------------------------
    while True:
        try:
            pergunta = input("\n👤 Utente: ").strip()
            
            if not pergunta:
                continue
                
            if pergunta.lower() in ['sair', 'exit', 'quit']:
                print("\n👋 A encerrar o assistente. Obrigado!")
                break
                
            print("\n🤖 A processar o raciocínio clínico...")
            
            # Invocar o LLM com a pergunta
            resultado = qa_chain.invoke({"query": pergunta})
            resposta_llm = resultado['result']
            
            print("\n" + "="*60)
            print(resposta_llm)
            print("="*60)
            
        except KeyboardInterrupt:
            print("\n👋 A encerrar o assistente abruptamente. Adeus!")
            break
        except EOFError:
            print("\n👋 Fim de entrada de dados. A encerrar.")
            break
        except Exception as e:
            print(f"\n[!] Ocorreu um erro: {e}")
            break

if __name__ == "__main__":
    main()
