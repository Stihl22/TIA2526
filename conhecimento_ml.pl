% =============================================================
% BASE DE CONHECIMENTO GERADA AUTOMATICAMENTE POR ML (Python)
% Algoritmo: Decision Tree Classifier
% =============================================================

:- discontiguous regra_ml/2.
:- discontiguous pre_triagem/2.

regra_ml('ADR-SU (Servico de Urgencia)', C) :-
    \+ pergunta(febre_assoc, 'Tem febre associada?', _),
    \+ pergunta(cede_antipireticos, 'A febre baixa apos tomar paracetamol ou ibuprofeno na dose correcta?', _),
    \+ sintoma_principal(tosse),
    \+ pergunta(cefaleia_rigidez, 'Tem dor de cabeca intensa, rigidez no pescoco ou dor com a luz (fotofobia)?', _),
    \+ pergunta(comorbilidades, 'Tem doencas cronicas graves (insuficiencia renal/cardiaca, imunossupressao, diabetes descompensada)?', _),
    C = 0.7,
    assert_just('Regra ML: [(''febre_assoc'', 0), (''sintoma_principal_Qualquer'', 0), (''cede_antipireticos'', 0), (''sintoma_principal_Tosse'', 0), (''cefaleia_rigidez'', 0), (''comorbilidades'', 0)]', C),
    !.

regra_ml('CONSULTA CSP (Centro de Saude, nas proximas 24h)', C) :-
    \+ pergunta(febre_assoc, 'Tem febre associada?', _),
    \+ pergunta(cede_antipireticos, 'A febre baixa apos tomar paracetamol ou ibuprofeno na dose correcta?', _),
    \+ sintoma_principal(tosse),
    \+ pergunta(cefaleia_rigidez, 'Tem dor de cabeca intensa, rigidez no pescoco ou dor com a luz (fotofobia)?', _),
    pergunta(comorbilidades, 'Tem doencas cronicas graves (insuficiencia renal/cardiaca, imunossupressao, diabetes descompensada)?', C1),
    C = C1,
    assert_just('Regra ML: [(''febre_assoc'', 0), (''sintoma_principal_Qualquer'', 0), (''cede_antipireticos'', 0), (''sintoma_principal_Tosse'', 0), (''cefaleia_rigidez'', 0), (''comorbilidades'', 1)]', C),
    !.

regra_ml('EMERGENCIA (112 / INEM)', C) :-
    \+ pergunta(febre_assoc, 'Tem febre associada?', _),
    \+ pergunta(cede_antipireticos, 'A febre baixa apos tomar paracetamol ou ibuprofeno na dose correcta?', _),
    \+ sintoma_principal(tosse),
    pergunta(cefaleia_rigidez, 'Tem dor de cabeca intensa, rigidez no pescoco ou dor com a luz (fotofobia)?', C1),
    C = C1,
    assert_just('Regra ML: [(''febre_assoc'', 0), (''sintoma_principal_Qualquer'', 0), (''cede_antipireticos'', 0), (''sintoma_principal_Tosse'', 0), (''cefaleia_rigidez'', 1)]', C),
    !.

regra_ml('AUTOCUIDADO SEM TESTE COVID', C) :-
    \+ pergunta(febre_assoc, 'Tem febre associada?', _),
    \+ pergunta(cede_antipireticos, 'A febre baixa apos tomar paracetamol ou ibuprofeno na dose correcta?', _),
    sintoma_principal(tosse),
    \+ pergunta(dispneia_assoc, 'Tem falta de ar associada a tosse?', _),
    C = 0.7,
    assert_just('Regra ML: [(''febre_assoc'', 0), (''sintoma_principal_Qualquer'', 0), (''cede_antipireticos'', 0), (''sintoma_principal_Tosse'', 1), (''dispneia_assoc'', 0)]', C),
    !.

regra_ml('EMERGENCIA (112 / INEM)', C) :-
    \+ pergunta(febre_assoc, 'Tem febre associada?', _),
    \+ pergunta(cede_antipireticos, 'A febre baixa apos tomar paracetamol ou ibuprofeno na dose correcta?', _),
    sintoma_principal(tosse),
    pergunta(dispneia_assoc, 'Tem falta de ar associada a tosse?', C1),
    C = C1,
    assert_just('Regra ML: [(''febre_assoc'', 0), (''sintoma_principal_Qualquer'', 0), (''cede_antipireticos'', 0), (''sintoma_principal_Tosse'', 1), (''dispneia_assoc'', 1)]', C),
    !.

regra_ml('AUTOCUIDADO COM VIGILANCIA', C) :-
    \+ pergunta(febre_assoc, 'Tem febre associada?', _),
    pergunta(cede_antipireticos, 'A febre baixa apos tomar paracetamol ou ibuprofeno na dose correcta?', C1),
    C = C1,
    assert_just('Regra ML: [(''febre_assoc'', 0), (''sintoma_principal_Qualquer'', 0), (''cede_antipireticos'', 1)]', C),
    !.

regra_ml('EMERGENCIA ABSOLUTA (Ligue 112 / INEM)', C) :-
    \+ pergunta(febre_assoc, 'Tem febre associada?', _),
    C = 0.7,
    assert_just('Regra ML: [(''febre_assoc'', 0), (''sintoma_principal_Qualquer'', 1)]', C),
    !.

regra_ml('AUTOCUIDADO COM VIGILANCIA (24h)', C) :-
    pergunta(febre_assoc, 'Tem febre associada?', C1),
    \+ pergunta(anosmia, 'Teve perda subita do olfacto nos ultimos 7 dias?', _),
    C = C1,
    assert_just('Regra ML: [(''febre_assoc'', 1), (''anosmia'', 0)]', C),
    !.

regra_ml('AUTOCUIDADO (Teste COVID + Isolamento 7 dias)', C) :-
    pergunta(febre_assoc, 'Tem febre associada?', C1),
    pergunta(anosmia, 'Teve perda subita do olfacto nos ultimos 7 dias?', C2),
    C is min(C1, C2),
    assert_just('Regra ML: [(''febre_assoc'', 1), (''anosmia'', 1)]', C),
    !.

% --- Fallbacks de seguranca ---
pre_triagem(_, _) :- fail.
regra_ml('TRANSFERENCIA -> Enfermeiro SNS24', 0.5) :- assert_just('Fallback ML (Sintomas nao discriminados)', 0.5).