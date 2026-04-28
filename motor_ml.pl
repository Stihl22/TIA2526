% =============================================================
% SISD SNS24 - MOTOR DE INFERENCIA (VERSAO ML) (motor_ml.pl)
% Motor de Inferencia adaptado para consumir regras da Arvore
% =============================================================

avaliar(DF, CF) :-
    (   pre_triagem(DF_Pre, CF_Pre)
    ->  DF = DF_Pre,
        CF = CF_Pre
    ;   (   sintoma_principal(_)
        ->  avaliar_fluxo_ml(DF, CF)
        ;   assert_just('SISTEMA: Nenhum sintoma principal foi registado antes de chamar o motor.', 0.0),
            DF = 'ERRO DE CONFIGURACAO',
            CF = 0.0
        )
    ).

avaliar_fluxo_ml(DF, CF) :- regra_ml(DF, CF), !.
