% =============================================================
% BASE DE CONHECIMENTO GERADA AUTOMATICAMENTE POR ML (Python)
% Algoritmo: Decision Tree Classifier
% =============================================================

:- discontiguous regra_ml/2.
:- discontiguous pre_triagem/2.

% Helper para lidar com respostas '0.0' que causam fail no pergunta/3 original
pergunta_cf(Atributo, Texto, Certeza) :-
    ( pergunta(Atributo, Texto, C) -> Certeza = C ; Certeza = 0.0 ).

regra_ml('ADR-SU (Servico de Urgencia)', C) :-
    pergunta_cf(febre_assoc, 'Tem febre associada?', Tmp1),
    C1 is 1.0 - Tmp1,
    pergunta_cf(cede_antipireticos, 'A febre baixa apos tomar paracetamol ou ibuprofeno na dose correcta?', Tmp2),
    C2 is 1.0 - Tmp2,
    \+ sintoma_principal(tosse),
    pergunta_cf(cefaleia_rigidez, 'Tem dor de cabeca intensa, rigidez no pescoco ou dor com a luz (fotofobia)?', Tmp3),
    C3 is 1.0 - Tmp3,
    C_Premissas is min(C1, min(C2, C3)),
    C is C_Premissas * 0.85,
    C > 0.0,
    assert_just('Regra ML: [(''febre_assoc'', 0), (''sintoma_principal_Qualquer'', 0), (''cede_antipireticos'', 0), (''sintoma_principal_Tosse'', 0), (''cefaleia_rigidez'', 0)]', C).

regra_ml('EMERGENCIA (112 / INEM)', C) :-
    pergunta_cf(febre_assoc, 'Tem febre associada?', Tmp1),
    C1 is 1.0 - Tmp1,
    pergunta_cf(cede_antipireticos, 'A febre baixa apos tomar paracetamol ou ibuprofeno na dose correcta?', Tmp2),
    C2 is 1.0 - Tmp2,
    \+ sintoma_principal(tosse),
    pergunta_cf(cefaleia_rigidez, 'Tem dor de cabeca intensa, rigidez no pescoco ou dor com a luz (fotofobia)?', C3),
    C_Premissas is min(C1, min(C2, C3)),
    C is C_Premissas * 0.95,
    C > 0.0,
    assert_just('Regra ML: [(''febre_assoc'', 0), (''sintoma_principal_Qualquer'', 0), (''cede_antipireticos'', 0), (''sintoma_principal_Tosse'', 0), (''cefaleia_rigidez'', 1)]', C).

regra_ml('AUTOCUIDADO SEM TESTE COVID', C) :-
    pergunta_cf(febre_assoc, 'Tem febre associada?', Tmp1),
    C1 is 1.0 - Tmp1,
    pergunta_cf(cede_antipireticos, 'A febre baixa apos tomar paracetamol ou ibuprofeno na dose correcta?', Tmp2),
    C2 is 1.0 - Tmp2,
    sintoma_principal(tosse),
    pergunta_cf(hemoptises, 'Esta a tossir sangue (expectoracao visivelmente hematica)?', Tmp3),
    C3 is 1.0 - Tmp3,
    C_Premissas is min(C1, min(C2, C3)),
    C is C_Premissas * 0.75,
    C > 0.0,
    assert_just('Regra ML: [(''febre_assoc'', 0), (''sintoma_principal_Qualquer'', 0), (''cede_antipireticos'', 0), (''sintoma_principal_Tosse'', 1), (''hemoptises'', 0)]', C).

regra_ml('EMERGENCIA (112 / INEM)', C) :-
    pergunta_cf(febre_assoc, 'Tem febre associada?', Tmp1),
    C1 is 1.0 - Tmp1,
    pergunta_cf(cede_antipireticos, 'A febre baixa apos tomar paracetamol ou ibuprofeno na dose correcta?', Tmp2),
    C2 is 1.0 - Tmp2,
    sintoma_principal(tosse),
    pergunta_cf(hemoptises, 'Esta a tossir sangue (expectoracao visivelmente hematica)?', C3),
    C_Premissas is min(C1, min(C2, C3)),
    C is C_Premissas * 0.95,
    C > 0.0,
    assert_just('Regra ML: [(''febre_assoc'', 0), (''sintoma_principal_Qualquer'', 0), (''cede_antipireticos'', 0), (''sintoma_principal_Tosse'', 1), (''hemoptises'', 1)]', C).

regra_ml('AUTOCUIDADO COM VIGILANCIA', C) :-
    pergunta_cf(febre_assoc, 'Tem febre associada?', Tmp1),
    C1 is 1.0 - Tmp1,
    pergunta_cf(cede_antipireticos, 'A febre baixa apos tomar paracetamol ou ibuprofeno na dose correcta?', C2),
    C_Premissas is min(C1, C2),
    C is C_Premissas * 0.75,
    C > 0.0,
    assert_just('Regra ML: [(''febre_assoc'', 0), (''sintoma_principal_Qualquer'', 0), (''cede_antipireticos'', 1)]', C).

regra_ml('EMERGENCIA ABSOLUTA (Ligue 112 / INEM)', C) :-
    pergunta_cf(febre_assoc, 'Tem febre associada?', Tmp1),
    C1 is 1.0 - Tmp1,
    C_Premissas = C1,
    C is C_Premissas * 0.95,
    C > 0.0,
    assert_just('Regra ML: [(''febre_assoc'', 0), (''sintoma_principal_Qualquer'', 1)]', C).

regra_ml('AUTOCUIDADO COM VIGILANCIA (24h)', C) :-
    pergunta_cf(febre_assoc, 'Tem febre associada?', C1),
    \+ sintoma_principal(tosse),
    C_Premissas = C1,
    C is C_Premissas * 0.75,
    C > 0.0,
    assert_just('Regra ML: [(''febre_assoc'', 1), (''sintoma_principal_Tosse'', 0)]', C).

regra_ml('AUTOCUIDADO (Teste COVID + Isolamento 7 dias)', C) :-
    pergunta_cf(febre_assoc, 'Tem febre associada?', C1),
    sintoma_principal(tosse),
    C_Premissas = C1,
    C is C_Premissas * 0.75,
    C > 0.0,
    assert_just('Regra ML: [(''febre_assoc'', 1), (''sintoma_principal_Tosse'', 1)]', C).

% --- Fallbacks de seguranca ---
pre_triagem(_, _) :- fail.
regra_ml('TRANSFERENCIA -> Enfermeiro SNS24', 0.5) :- assert_just('Fallback ML (Sintomas nao discriminados)', 0.5).