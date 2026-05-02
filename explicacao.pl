% =============================================================
% SISD SNS24 - MODULO DE EXPLICACAO (explicacao.pl) [P1MAX]
% Versao ASCII-only: compativel com terminais Windows sem UTF-8.
%
% DEPENDENCIA: base_dados.pl
% =============================================================

% --- API de Registo (usada em conhecimento.pl) ---

% assert_just(+Texto, +CertezaRegra)
% Regista uma justificacao com a certeza calculada pela regra.
assert_just(Texto, CertezaRegra) :-
    retract(contador_just(N)),
    N1 is N + 1,
    assertz(contador_just(N1)),
    assertz(justificacao(N1, Texto, CertezaRegra)).

% --- Impressao da Explicacao Completa ---

% mostrar_explicacao/0
% Dimensao HOW: que factos o utente confirmou e com que certeza?
% Dimensao WHY: que regra(s) clinica(s) dispararam, porque, e com que certeza?
mostrar_explicacao :-
    nl,
    writeln('+=========================================================+'),
    writeln('|      MODULO DE EXPLICACAO P1MAX  -  Why / How           |'),
    writeln('+=========================================================+'),
    nl,
    writeln('  >> HOW - Factos confirmados pelo utente nesta sessao:'),
    findall(F-C, (sim(F), certeza_memoria(F, C)), FCs),
    (   FCs = []
    ->  writeln('      (nenhum sintoma confirmado)')
    ;   forall(member(F-C, FCs),
               (   Pct is round(C * 100),
                   format('      [OK] ~w  (certeza: ~w%)~n', [F, Pct])
               ))
    ),
    nl,
    writeln('  >> WHY - Raciocinio clinico aplicado (regras disparadas):'),
    findall(O-J-CR, justificacao(O, J, CR), OJCRs),
    msort(OJCRs, OJCRsSorted),
    (   OJCRsSorted = []
    ->  writeln('      (nenhuma justificacao registada)')
    ;   forall(member(_-J-CR, OJCRsSorted),
               (   PctR is round(CR * 100),
                   format('      [*] ~w~n          >> Certeza da regra: ~w%~n', [J, PctR])
               ))
    ),
    nl,
    writeln('+=========================================================+'),
    nl.

% --- Limpeza do modulo de explicacao ---
limpar_explicacao :-
    retractall(justificacao(_, _, _)),
    retractall(contador_just(_)),
    assertz(contador_just(0)).
    