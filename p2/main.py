import sys
import os

# Definições de cores ANSI para o terminal
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def print_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(Colors.CYAN + Colors.BOLD + "╔" + "═" * 68 + "╗" + Colors.RESET)
    print(Colors.CYAN + Colors.BOLD + "║   SIAD — Assistente de Triagem SNS24 (Interface Avançada)      ║" + Colors.RESET)
    print(Colors.CYAN + Colors.BOLD + "║   Sistema Inteligente de Apoio à Decisão Clínica                ║" + Colors.RESET)
    print(Colors.CYAN + Colors.BOLD + "╚" + "═" * 68 + "╝" + Colors.RESET)
    print()

def print_help():
    print(Colors.YELLOW + "Comandos do Sistema:" + Colors.RESET)
    print(f"  {Colors.BOLD}sair{Colors.RESET}      → Encerra a aplicação.")
    print(f"  {Colors.BOLD}ajuda{Colors.RESET}     → Mostra esta mensagem de comandos.")
    print(f"  {Colors.BOLD}debug{Colors.RESET}     → Liga/desliga a exibição dos blocos de contexto RAG.")
    print(f"  {Colors.BOLD}historico{Colors.RESET} → Mostra as perguntas guardadas em memória.")
    print(f"  {Colors.BOLD}reset{Colors.RESET}     → Limpa a memória clínica atual para um novo utente.")
    print()

def colorize_answer(text: str) -> str:
    """Aplica cores às palavras-chave críticas de triagem."""
    text = text.replace("EMERGÊNCIA", f"{Colors.RED}{Colors.BOLD}EMERGÊNCIA{Colors.RESET}")
    text = text.replace("112", f"{Colors.RED}{Colors.BOLD}112{Colors.RESET}")
    text = text.replace("URGÊNCIA", f"{Colors.YELLOW}{Colors.BOLD}URGÊNCIA{Colors.RESET}")
    text = text.replace("URGENTE", f"{Colors.YELLOW}{Colors.BOLD}URGENTE{Colors.RESET}")
    text = text.replace("CONSULTA", f"{Colors.BLUE}{Colors.BOLD}CONSULTA{Colors.RESET}")
    text = text.replace("AUTO-CUIDADO", f"{Colors.GREEN}{Colors.BOLD}AUTO-CUIDADO{Colors.RESET}")
    text = text.replace("AUTOCUIDADO", f"{Colors.GREEN}{Colors.BOLD}AUTOCUIDADO{Colors.RESET}")
    return text

def main():
    print_header()
    
    # Importar backend (apenas quando o programa arranca)
    print(f"{Colors.MAGENTA}[*] A iniciar Motor de IA... Por favor aguarde.{Colors.RESET}")
    try:
        from rag_engine import SIADRagEngine
    except ImportError as e:
        print(f"{Colors.RED}[!] Erro ao carregar o backend (rag_engine.py): {e}{Colors.RESET}")
        sys.exit(1)

    # Inicializar bot
    bot = SIADRagEngine()
    try:
        bot.inicializar()
    except Exception as e:
        print(f"{Colors.RED}[!] Falha Crítica na Base de Conhecimento: {e}{Colors.RESET}")
        sys.exit(1)

    debug_mode = False
    
    print_header()
    print_help()
    print(f"{Colors.GREEN}✔ Motor preparado! Descreva a queixa do utente ou use 'ajuda'.{Colors.RESET}\n")

    # Loop principal
    while True:
        try:
            user_input = input(f"{Colors.BOLD}👤 Utente:{Colors.RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{Colors.YELLOW}👋 Desligamento forçado. Cuide-se!{Colors.RESET}")
            break
            
        if not user_input:
            continue

        cmd = user_input.lower()
        
        if cmd in ("sair", "exit", "quit"):
            print(f"\n{Colors.GREEN}👋 A encerrar sistema seguro. Bom turno!{Colors.RESET}")
            break
            
        if cmd == "ajuda":
            print_help()
            continue
            
        if cmd == "reset":
            bot.nova_sessao()
            print(f"\n{Colors.CYAN}🔄 Memória Clínica apagada. Preparado para novo utente.{Colors.RESET}\n")
            continue
            
        if cmd == "historico":
            hist = bot.get_history()
            if not hist:
                print(f"\n{Colors.YELLOW}[Memória Vazia] Nenhuma conversa ativa.{Colors.RESET}\n")
            else:
                print(f"\n{Colors.CYAN}=== HISTÓRICO DE SESSÃO ==={Colors.RESET}")
                for msg in hist:
                    role_color = Colors.BOLD if msg['role'] == 'utente' else Colors.GREEN
                    print(f"{role_color}{msg['role'].capitalize()}:{Colors.RESET} {msg['content']}")
                print(f"{Colors.CYAN}==========================={Colors.RESET}\n")
            continue
            
        if cmd == "debug":
            debug_mode = not debug_mode
            status = "LIGADO" if debug_mode else "DESLIGADO"
            print(f"\n{Colors.YELLOW}⚙️  Modo Debug (Fontes RAG): {status}{Colors.RESET}\n")
            continue

        # Invocação da Inteligência Artificial
        print(f"\n{Colors.MAGENTA}🤖 A processar triagem com Llama 3.2...{Colors.RESET}")
        
        try:
            resposta, fontes = bot.chat_with_bot(user_input)
            
            # Formatar cores
            resposta_colorida = colorize_answer(resposta)
            
            print(f"\n{Colors.GREEN}=== DECISÃO CLÍNICA ==={Colors.RESET}")
            print(resposta_colorida)
            print(f"{Colors.GREEN}======================={Colors.RESET}\n")
            
            if debug_mode:
                print(f"{Colors.YELLOW}=== CHUNKS (RAG SOURCES) ==={Colors.RESET}")
                for i, chunk in enumerate(fontes, 1):
                    print(f"{Colors.YELLOW}Fonte {i}:{Colors.RESET} {chunk.page_content.strip()[:150]}...")
                print(f"{Colors.YELLOW}============================{Colors.RESET}\n")
                
        except Exception as e:
            print(f"\n{Colors.RED}❌ ERRO INTERNO: {e}{Colors.RESET}\n")

if __name__ == "__main__":
    main()
