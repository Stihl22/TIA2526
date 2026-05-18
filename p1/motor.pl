% =============================================================
% SISD SNS24 - MOTOR DE INFERENCIA (motor.pl)
% Versao ASCII-only.
% Implementa encadeamento em frente (Forward Chaining).
% Suporta propagacao de graus de certeza (Aula 6 - Incerteza).
% E completamente agnostico a UI - nao imprime nada.
% O Projeto 2 (Chatbot) chamara avaliar/2 directamente.
%
% DEPENDENCIAS: base_dados.pl, conhecimento.pl
% =============================================================

% avaliar(-DisposicaoFinal, -CertezaFinal)
% Ponto de entrada do motor.
% FASE 1: Pre-triagem ABC (prioridade absoluta).
% FASE 2: Fluxo especifico do sintoma principal.
avaliar(DF, CF) :-
    (   pre_triagem(DF_Pre, CF_Pre)
    ->  DF = DF_Pre,
        CF = CF_Pre
    ;   (   sintoma_principal(S)
        ->  avaliar_fluxo(S, DF, CF)
        ;   assert_just('SISTEMA: Nenhum sintoma principal foi registado antes de chamar o motor.', 0.0),
            DF = 'ERRO DE CONFIGURACAO - Contacte o Administrador do Sistema',
            CF = 0.0
        )
    ).

% avaliar_fluxo(+Sintoma, -DisposicaoFinal, -CertezaFinal)
% Router para os predicados de regras por sintoma.
avaliar_fluxo(febre,    DF, CF) :- regra_febre(DF, CF),    !.
avaliar_fluxo(dispneia, DF, CF) :- regra_dispneia(DF, CF), !.
avaliar_fluxo(tosse,    DF, CF) :- regra_tosse(DF, CF),    !.
avaliar_fluxo(Outro,    DF, CF) :-
    format(atom(Msg),
        'SISTEMA: Sintoma "~w" nao tem fluxo definido na base de conhecimento.', [Outro]),
    assert_just(Msg, 0.0),
    DF = 'TRANSFERENCIA -> Enfermeiro SNS24',
    CF = 0.0.
