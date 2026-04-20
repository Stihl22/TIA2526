% =============================================================
% SISD SNS24 - MOTOR DE INFERENCIA (motor.pl)
% Versao ASCII-only.
% Implementa encadeamento em frente (Forward Chaining).
% E completamente agnostico a UI - nao imprime nada.
% O Projeto 2 (Chatbot) chamara avaliar/1 directamente.
%
% DEPENDENCIAS: base_dados.pl, conhecimento.pl
% =============================================================

% avaliar(-DisposicaoFinal)
% Ponto de entrada do motor.
% FASE 1: Pre-triagem ABC (prioridade absoluta).
% FASE 2: Fluxo especifico do sintoma principal.
avaliar(DF) :-
    (   pre_triagem(DF_Pre)
    ->  DF = DF_Pre
    ;   (   sintoma_principal(S)
        ->  avaliar_fluxo(S, DF)
        ;   assert_just('SISTEMA: Nenhum sintoma principal foi registado antes de chamar o motor.'),
            DF = 'ERRO DE CONFIGURACAO - Contacte o Administrador do Sistema'
        )
    ).

% avaliar_fluxo(+Sintoma, -DisposicaoFinal)
% Router para os predicados de regras por sintoma.
avaliar_fluxo(febre,    DF) :- regra_febre(DF),    !.
avaliar_fluxo(dispneia, DF) :- regra_dispneia(DF), !.
avaliar_fluxo(tosse,    DF) :- regra_tosse(DF),    !.
avaliar_fluxo(Outro,    DF) :-
    format(atom(Msg),
        'SISTEMA: Sintoma "~w" nao tem fluxo definido na base de conhecimento.', [Outro]),
    assert_just(Msg),
    DF = 'TRANSFERENCIA -> Enfermeiro SNS24'.