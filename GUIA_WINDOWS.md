# Guia de Instalação e Execução - Windows (SIAD SNS24)

Este guia explica passo a passo como um utilizador com Windows pode configurar e correr o projeto na sua máquina.

## 1. Pré-requisitos Essenciais

Antes de começar, garante que tens as seguintes ferramentas instaladas:

1. **Python**:
   - Transfere o [Python (versão 3.9 a 3.12)](https://www.python.org/downloads/windows/).
   - **MUITO IMPORTANTE:** Durante a instalação do Python, lembra-te de marcar a caixa na parte inferior que diz **"Add Python to PATH"** ou **"Add python.exe to PATH"** antes de clicares em "Install Now".

2. **Ollama** (para correr a Inteligência Artificial localmente):
   - Transfere e instala o [Ollama para Windows](https://ollama.com/download/windows).

---

## 2. Configurar os Modelos de IA

Abre a tua Linha de Comandos (CMD) ou PowerShell e faz o download dos dois modelos necessários correndo os seguintes comandos (um de cada vez):

```cmd
ollama pull llama3.2:1b
```
```cmd
ollama pull nomic-embed-text
```
*Nota: Este passo pode demorar alguns minutos dependendo da velocidade da internet.*

---

## 3. Preparar o Projeto

Abre a Linha de Comandos (CMD) ou PowerShell, navega até à pasta principal do projeto (onde estão os ficheiros `app.py`, `main.py` e `requirements.txt`).

**1. Criar o Ambiente Virtual:**
```cmd
python -m venv .venv
```

**2. Ativar o Ambiente Virtual:**
```cmd
.venv\Scripts\activate
```
*(Deves reparar que vai aparecer `(.venv)` no início da linha do terminal)*.
> **Nota:** Se der um erro de "Execution of scripts is disabled" no PowerShell, corre este comando para dar permissão: `Set-ExecutionPolicy Unrestricted -Scope CurrentUser` e tenta ativar novamente.

**3. Instalar as Dependências:**
Com o ambiente ativado, instala todas as bibliotecas necessárias:
```cmd
pip install -r requirements.txt
```

---

## 4. Correr a Aplicação

Com tudo configurado e o ambiente virtual **ativado** `(.venv)`, podes iniciar a aplicação de duas formas:

### Opção A: Interface Web (Streamlit)
Ideal para uma visualização gráfica mais intuitiva.
```cmd
streamlit run app.py
```
*(Isto deve abrir automaticamente uma janela no teu browser. Caso não abra, copia o link `Local URL:` que aparece no terminal).*

### Opção B: Interface de Terminal Avançada
Ideal para quem prefere uma interação rápida e estilo chat via consola.
```cmd
python main.py
```

---

## Resumo Rápido para Próximas Utilizações
Sempre que quiseres voltar a ligar o projeto noutro dia, só precisas de:
1. Abrir o terminal na pasta do projeto.
2. Ativar o ambiente: `.venv\Scripts\activate`
3. Correr o projeto: `streamlit run app.py` ou `python main.py`
