% =============================================================
% SISD SNS24 - INTERFACE (interface.pl)
% Versao ASCII-only: compativel com terminais Windows sem UTF-8.
% Toda a logica de I/O, limpeza de estado e menu do utilizador.
%
% DEPENDENCIAS: base_dados.pl, explicacao.pl, motor.pl
% =============================================================

% =============================================================
% SECCAO A: GESTAO DE ESTADO
% =============================================================

% limpar_tudo/0
% Limpa TODOS os factos dinamicos da sessao anterior.
limpar_tudo :-
    retractall(sim(_)),
    retractall(nao(_)),
    retractall(certeza_memoria(_, _)),
    retractall(sintoma_principal(_)),
    limpar_explicacao.

% =============================================================
% SECCAO B: MOTOR DE PERGUNTAS COM CACHE E GRAU DE CERTEZA
% =============================================================

% pergunta(+Atributo, +TextoDaPergunta, -Certeza)
%
% Sucede (com Certeza unificada) se o utente confirmou o atributo (certeza > 0.0).
% Falha se o utente negou o atributo (certeza == 0.0).
% Pergunta ao utilizador apenas se o atributo nao for conhecido.
%
% O utilizador introduz um valor decimal entre 0.0 e 1.0:
%   0.0       -> equivale a "Nao" (nega o atributo, fail)
%   ]0.0,1.0] -> equivale a "Sim" com esse grau de certeza
%
% NOTA: \+ pergunta(X, Txt, _) e SEGURO neste sistema porque
%   o assertz(nao(X)) e feito antes de fail -- a proxima chamada
%   a pergunta(X, _, _) falha imediatamente pelo cache, sem repetir
%   a pergunta ao utilizador.
pergunta(Atributo, _, Certeza) :-
    sim(Atributo), !,
    certeza_memoria(Atributo, Certeza).

pergunta(Atributo, _, _) :-
    nao(Atributo), !, fail.

pergunta(Atributo, Texto, Certeza) :-
    format('~n  [?] ~w~n', [Texto]),
    writeln('      (0.0 = Nao | 1.0 = Sim absoluto | ex: 0.8 = provavel)'),
    write('      Grau de certeza [0.0 a 1.0]: '),
    read_term(Valor, []),
    (   number(Valor), Valor >= 0.0, Valor =< 1.0
    ->  true
    ;   writeln('  [!] Valor invalido. Introduza um numero entre 0.0 e 1.0.'),
        pergunta(Atributo, Texto, Certeza)
    ),
    (   Valor > 0.0
    ->  assertz(sim(Atributo)),
        assertz(certeza_memoria(Atributo, Valor)),
        Certeza = Valor
    ;   assertz(nao(Atributo)),
        fail
    ).

% =============================================================
% SECCAO C: MENU E LOOP PRINCIPAL
% =============================================================

mostrar_cabecalho :-
    nl,
    writeln('+=========================================================+'),
    writeln('|    SISD SNS24 - Sistema de Triagem Clinica  v2.0        |'),
    writeln('|    Universidade do Minho  |  SIAD 2025/2026             |'),
    writeln('|    Projeto 1 - Parte B  (Incerteza / Graus de Certeza)  |'),
    writeln('+=========================================================+'),
    nl.

mostrar_menu :-
    writeln('+----------------------------------------------------------+'),
    writeln('|   Qual e o sintoma principal do utente?                  |'),
    writeln('|                                                          |'),
    writeln('|     1  ->  Febre                                         |'),
    writeln('|     2  ->  Falta de Ar / Dispneia                        |'),
    writeln('|     3  ->  Tosse                                         |'),
    writeln('|     0  ->  Sair                                          |'),
    writeln('+----------------------------------------------------------+'),
    write('  > Opcao (terminar com ponto): ').

% ler_opcao(-Sintoma)
ler_opcao(Sintoma) :-
    read(Opcao),
    (   opcao_para_sintoma(Opcao, Sintoma)
    ->  true
    ;   nl,
        writeln('  [!] Opcao invalida. Escolha 0, 1, 2 ou 3.'),
        nl,
        mostrar_menu,
        ler_opcao(Sintoma)
    ).

opcao_para_sintoma(1, febre).
opcao_para_sintoma(2, dispneia).
opcao_para_sintoma(3, tosse).
opcao_para_sintoma(0, sair).

% imprimir_resultado(+DisposicaoFinal, +CertezaFinal)
imprimir_resultado(DF, CF) :-
    PctF is round(CF * 100),
    nl,
    writeln('+==========================================================+'),
    format( '|  DISPOSICAO FINAL: ~w~n', [DF]),
    format( '|  CERTEZA DA DISPOSICAO: ~w%~n', [PctF]),
    writeln('+==========================================================+'),
    mostrar_explicacao.

% executar_sessao/0
executar_sessao :-
    nl,
    writeln('  [i] A Pre-Triagem ABC sera sempre efectuada primeiro.'),
    writeln('  [i] Responda com um valor entre 0.0 e 1.0 (com ponto final).'),
    writeln('  [i] Exemplo: 1.0. para Sim absoluto | 0.0. para Nao | 0.8. para provavel.'),
    nl,
    writeln('  --- FASE 1: PRE-TRIAGEM (Avaliacao ABC) ---'),
    nl,
    (   avaliar(DF, CF)
    ->  imprimir_resultado(DF, CF)
    ;   nl,
        writeln('  [ERRO] O motor de inferencia nao produziu resultado.'),
        writeln('  [ERRO] Verifique a consistencia das regras em conhecimento.pl.')
    ).

% iniciar_triagem/0
% Loop principal. Executa sessoes ate o utilizador escolher sair.
iniciar_triagem :-
    mostrar_cabecalho,
    repeat,
        limpar_tudo,
        nl,
        mostrar_menu,
        ler_opcao(Sintoma),
        (   Sintoma == sair
        ->  nl,
            writeln('  [*] Sistema encerrado. Obrigado.'),
            nl,
            !
        ;   assertz(sintoma_principal(Sintoma)),
            executar_sessao,
            nl,
            writeln('  --- Nova triagem? Pressione Enter e responda ao menu. ---'),
            fail
        ).
