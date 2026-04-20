% =============================================================
% SISD SNS24 - MODULO DE EXPLICACAO (explicacao.pl) [P1MAX]
% Versao ASCII-only: compativel com terminais Windows sem UTF-8.
%
% DEPENDENCIA: base_dados.pl
% =============================================================

% --- API de Registo (usada em conhecimento.pl) ---

assert_just(Texto) :-
    retract(contador_just(N)),
    N1 is N + 1,
    assertz(contador_just(N1)),
    assertz(justificacao(N1, Texto)).

% --- Impressao da Explicacao Completa ---

% mostrar_explicacao/0
% Dimensao HOW: que factos o utente confirmou?
% Dimensao WHY: que regra(s) clinica(s) dispararam e porque?
mostrar_explicacao :-
    nl,
    writeln('+=========================================================+'),
    writeln('|      MODULO DE EXPLICACAO P1MAX  -  Why / How           |'),
    writeln('+=========================================================+'),
    nl,
    writeln('  >> HOW - Factos confirmados pelo utente nesta sessao:'),
    findall(F, sim(F), Fs),
    (   Fs = []
    ->  writeln('      (nenhum sintoma confirmado)')
    ;   forall(member(F, Fs),
               format('      [OK] ~w~n', [F]))
    ),
    nl,
    writeln('  >> WHY - Raciocinio clinico aplicado (regras disparadas):'),
    findall(O-J, justificacao(O, J), OJs),
    msort(OJs, OJsSorted),
    (   OJsSorted = []
    ->  writeln('      (nenhuma justificacao registada)')
    ;   forall(member(_-J, OJsSorted),
               format('      [*] ~w~n', [J]))
    ),
    nl,
    writeln('+=========================================================+'),
    nl.

% --- Limpeza do modulo de explicacao ---
limpar_explicacao :-
    retractall(justificacao(_, _)),
    retractall(contador_just(_)),
    assertz(contador_just(0)).