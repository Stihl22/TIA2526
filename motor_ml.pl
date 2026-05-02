% =============================================================
% SISD SNS24 - MOTOR DE INFERENCIA (VERSAO ML) (motor_ml.pl)
% Motor de Inferencia adaptado para consumir regras da Arvore
% com suporte a acumulacao de Fatores de Certeza (CFs)
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

% avaliar_fluxo_ml/2: Recolhe TODAS as regras que ativam (sem cuts) e acumula os CFs
avaliar_fluxo_ml(DF_Final, CF_Final) :-
    findall((D, C), regra_ml(D, C), TodasAsRegras),
    ( TodasAsRegras = [] ->
        DF_Final = 'SEM DIAGNOSTICO', CF_Final = 0.0
    ;
        agrupar_por_diagnostico(TodasAsRegras, Agrupados),
        maior_diagnostico(Agrupados, DF_Final, CF_Final)
    ).

% --- Logica de Agrupamento e Acumulacao de CFs ---

% agrupar_por_diagnostico/2: Junta todos os CFs do mesmo diagnostico
agrupar_por_diagnostico([], []).
agrupar_por_diagnostico([(D, C)|T], [(D, C_Combinado)|Result]) :-
    filtrar_diag(D, T, CFs_Mesmo_D, T_Resto),
    combinar_cfs([C|CFs_Mesmo_D], C_Combinado),
    agrupar_por_diagnostico(T_Resto, Result).

% filtrar_diag/4: Extrai os CFs que pertencem ao diagnostico D e devolve o Resto
filtrar_diag(_, [], [], []).
filtrar_diag(D, [(D, C)|T], [C|CFs], Resto) :- 
    !, filtrar_diag(D, T, CFs, Resto).
filtrar_diag(D, [H|T], CFs, [H|Resto]) :- 
    filtrar_diag(D, T, CFs, Resto).

% combinar_cfs/2: Aplica a formula de Evidencia Incremental (CF = CF1 + CF2 - (CF1 * CF2))
combinar_cfs([], 0.0).
combinar_cfs([CF], CF) :- !.
combinar_cfs([CF1, CF2 | T], Result) :-
    CF_Parcial is CF1 + CF2 - (CF1 * CF2),
    combinar_cfs([CF_Parcial | T], Result).

% maior_diagnostico/3: Encontra o diagnostico com o maior CF_Combinado
maior_diagnostico([(D, C)], D, C).
maior_diagnostico([(D1, C1), (D2, C2) | T], D_Max, C_Max) :-
    (C1 >= C2 ->
        maior_diagnostico([(D1, C1) | T], D_Max, C_Max)
    ;
        maior_diagnostico([(D2, C2) | T], D_Max, C_Max)
    ).
