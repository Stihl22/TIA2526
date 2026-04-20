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
    retractall(sintoma_principal(_)),
    limpar_explicacao.

% =============================================================
% SECCAO B: MOTOR DE PERGUNTAS COM CACHE
% =============================================================

% pergunta(+Atributo, +TextoDaPergunta)
% Sucede se o utente confirmou o atributo (sim).
% Falha se o utente negou o atributo (nao).
% Pergunta ao utilizador apenas se o atributo nao for conhecido.
%
% NOTA: \+ pergunta(X, Txt) e SEGURO neste sistema porque
% o assertz(nao(X)) e feito antes de fail -- a proxima chamada
% a pergunta(X,_) falha imediatamente pelo cache, sem repetir
% a pergunta ao utilizador.
pergunta(Atributo, _) :-
    sim(Atributo), !.
pergunta(Atributo, _) :-
    nao(Atributo), !, fail.
pergunta(Atributo, Texto) :-
    format('~n  [?] ~w~n      Resposta (s/n): ', [Texto]),
    read_term(Resposta, []),
    (   Resposta == s
    ->  assertz(sim(Atributo))
    ;   assertz(nao(Atributo)),
        fail
    ).

% =============================================================
% SECCAO C: MENU E LOOP PRINCIPAL
% =============================================================

mostrar_cabecalho :-
    nl,
    writeln('+=========================================================+'),
    writeln('|    SISD SNS24 - Sistema de Triagem Clinica  v1.0        |'),
    writeln('|    Universidade do Minho  |  SIAD 2025/2026             |'),
    writeln('|    Projeto 1 - Parte A  (Aquisicao Manual de Conhec.)   |'),
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

% imprimir_resultado(+DisposicaoFinal)
imprimir_resultado(DF) :-
    nl,
    writeln('+==========================================================+'),
    format( '|  DISPOSICAO FINAL: ~w~n', [DF]),
    writeln('+==========================================================+'),
    mostrar_explicacao.

% executar_sessao/0
executar_sessao :-
    nl,
    writeln('  [i] A Pre-Triagem ABC sera sempre efectuada primeiro.'),
    writeln('  [i] Responda com "s." para Sim, ou "n." para Nao (com ponto).'),
    nl,
    writeln('  --- FASE 1: PRE-TRIAGEM (Avaliacao ABC) ---'),
    nl,
    (   avaliar(DF)
    ->  imprimir_resultado(DF)
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