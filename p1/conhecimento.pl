% =============================================================
% SISD SNS24 - BASE DE CONHECIMENTO (conhecimento.pl)
% Versao ASCII-only: todas as strings sao plain text.
% Regras de producao clinicas com suporte a graus de certeza.
% =============================================================
% SECCAO A: PRE-TRIAGEM (Avaliacao ABC)
% Prioridade ABSOLUTA - avaliada SEMPRE antes do fluxo clinico.
% Assinatura: pre_triagem(-Disposicao, -Certeza)
% =============================================================

pre_triagem('EMERGENCIA ABSOLUTA (Ligue 112 / INEM)', C) :-
    \+ pergunta(consciencia,
        'O utente responde, fala e esta orientado no espaco e no tempo?', _),
    % Negacao confirmada => assumimos certeza maxima da ausencia de consciencia.
    % Como nao capturamos certeza de negacoes, usamos 1.0 (sinal de alarme absoluto).
    C = 1.0,
    assert_just('PRE-R1a: Ausencia de resposta ou consciencia. Compromisso neurologico grave (A do ABC). Activar INEM imediatamente.', C),
    !.

pre_triagem('EMERGENCIA ABSOLUTA (Ligue 112 / INEM)', C) :-
    pergunta(dificuldade_resp_grave,
        'O utente tem dificuldade respiratoria intensa, cianose ou incapacidade de falar?', C1),
    C = C1,
    assert_just('PRE-R1b: Compromisso respiratorio grave na pre-triagem (B do ABC). Activar INEM imediatamente.', C),
    !.

pre_triagem('EMERGENCIA ABSOLUTA (Ligue 112 / INEM)', C) :-
    pergunta(hemorragia_grave,
        'O utente apresenta hemorragia activa e incontrolavel?', C1),
    C = C1,
    assert_just('PRE-R1c: Hemorragia activa grave. Compromisso circulatorio (C do ABC). Activar INEM imediatamente.', C),
    !.

% pre_triagem/2 falha se nao houver compromisso ABC.

% =============================================================
% SECCAO B: FLUXO DE FEBRE (F-Rx)
% Assinatura: regra_febre(-Disposicao, -Certeza)
% Ordem: Emergencia -> Urgencia -> CSP -> Autocuidado -> Fallback
% =============================================================

regra_febre('EMERGENCIA (112 / INEM)', C) :-
    pergunta(manchas_pele,
        'Tem manchas vermelhas/purpuras na pele que NAO desaparecem ao pressionar com um copo?', C1),
    pergunta(cefaleia_rigidez,
        'Tem dor de cabeca intensa, rigidez no pescoco ou dor com a luz (fotofobia)?', C2),
    C is min(C1, C2),
    assert_just('F-R2: Purpura nao-branqueavel + sinais meningeos. Suspeita de Doenca Meningococica. EMERGENCIA - Ligue 112.', C),
    !.

regra_febre('ADR-SU (Servico de Urgencia)', C) :-
    pergunta(convulsao_febril,
        'Teve alguma convulsao associada a febre, agora ou recentemente?', C1),
    C = C1,
    assert_just('F-R3: Convulsao febril activa ou recente. Requer avaliacao medica urgente em SU.', C),
    !.

regra_febre('ADR-SU (Servico de Urgencia)', C) :-
    pergunta(febre_gte_40,
        'A temperatura axilar medida e igual ou superior a 40 graus Celsius?', C1),
    C = C1,
    assert_just('F-R4: Hiperpirexia (>= 40C). Risco de falencia organica e complicacoes neurologicas. Urgencia hospitalar.', C),
    !.

regra_febre('ADR-SU (Servico de Urgencia)', C) :-
    pergunta(duracao_gt_48h,
        'A febre persiste ha MAIS de 48 horas sem melhoria?', C1),
    pergunta(agravamento_progressivo,
        'O estado geral esta a piorar progressivamente?', C2),
    pergunta(criterios_gravidade,
        'Tem falta de ar, vomitos incoerciveis, confusao mental ou dor toracica?', C3),
    C is min(C1, min(C2, C3)),
    assert_just('F-R7: Febre prolongada (> 48h) com agravamento do estado geral e criterios de gravidade. Urgencia hospitalar.', C),
    !.

regra_febre('TRANSFERENCIA -> Enfermeiro SNS24', C) :-
    pergunta(desidratacao,
        'Tem sinais de desidratacao grave: boca muito seca, ausencia de urina, prostracao intensa?', C1),
    C = C1,
    assert_just('F-R6: Desidratacao severa associada a febre. Requer avaliacao clinica - transferencia para enfermeiro SNS24.', C),
    !.

regra_febre('CONSULTA CSP (Centro de Saude, nas proximas 24h)', C) :-
    pergunta(comorbilidades,
        'Tem doencas cronicas graves (insuficiencia renal/cardiaca, imunossupressao, diabetes descompensada)?', C1),
    C = C1,
    assert_just('F-R8: Utente febril com comorbilidades de risco. Consulta medica obrigatoria nas proximas 24h.', C),
    !.

regra_febre('AUTOCUIDADO COM VIGILANCIA', C) :-
    pergunta(duracao_lt_48h,
        'A febre comecou ha MENOS de 48 horas?', C1),
    pergunta(cede_antipireticos,
        'A febre baixa apos tomar paracetamol ou ibuprofeno na dose correcta?', C2),
    \+ pergunta(criterios_gravidade,
        'Tem falta de ar, vomitos persistentes, confusao mental ou dor toracica?', _),
    \+ pergunta(comorbilidades,
        'Tem doencas cronicas graves?', _),
    pergunta(suporte_domicilio,
        'Tem telemovel e pelo menos uma pessoa que o/a possa acompanhar em casa?', C3),
    C is min(C1, min(C2, C3)),
    assert_just('F-R11: Febre de curso benigno (< 48h, responsiva a antipireticos, sem criterios de gravidade, com suporte). Apto para vigilancia domiciliaria. Reavalie se agravar nas proximas 12-24h.', C),
    !.

regra_febre('TRANSFERENCIA -> Enfermeiro SNS24', 0.5) :-
    assert_just('F-R15 (Fallback): Quadro febril sem criterios claros. Transferencia para avaliacao clinica adicional.', 0.5).

% =============================================================
% SECCAO C: FLUXO DE DISPNEIA (D-Rx)
% Assinatura: regra_dispneia(-Disposicao, -Certeza)
% =============================================================

regra_dispneia('EMERGENCIA (112 / INEM)', C) :-
    (   pergunta(cianose,
            'Tem coloracao azulada (cianose) nos labios ou nas unhas?', C1)
    ;   pergunta(incapacidade_falar,
            'Tem incapacidade de completar uma frase inteira devido a falta de ar?', C1)
    ;   pergunta(estridor,
            'Ouve um som agudo e rude ao respirar (estridor)?', C1)
    ),
    C = C1,
    assert_just('D-R1/D-R3: Compromisso respiratorio iminente (cianose / incapacidade de falar / estridor). EMERGENCIA - Ligue 112.', C),
    !.

regra_dispneia('ADR-SU (Servico de Urgencia)', C) :-
    pergunta(dispneia_repouso,
        'Sente falta de ar estando completamente em repouso (sem qualquer esforco)?', C1),
    C = C1,
    assert_just('D-R5: Dispneia em repouso. Criterio directo de encaminhamento urgente para SU hospitalar.', C),
    !.

regra_dispneia('ADR-SU (Servico de Urgencia)', C) :-
    pergunta(dor_toracica,
        'Tem dor no peito associada a falta de ar?', C1),
    C = C1,
    assert_just('D-R6: Dispneia com dor toracica. Despiste urgente de SCA (sindrome coronaria aguda) ou TEP (tromboembolismo pulmonar).', C),
    !.

regra_dispneia('ADR-SU (Servico de Urgencia)', C) :-
    pergunta(pieira,
        'Ouve sons tipo sibilos ou pieira ao respirar?', C1),
    \+ pergunta(asma_conhecida,
        'Tem diagnostico medico previo de asma bronquica?', _),
    C = C1,
    assert_just('D-R8: Pieira inaugural sem historico de asma. Possivel broncoespasmo severo ou reaccao anafilatica. Urgencia hospitalar.', C),
    !.

regra_dispneia('AUTOCUIDADO COM VIGILANCIA (24h)', C) :-
    pergunta(febre_assoc,
        'Tem febre associada a esta falta de ar?', C1),
    \+ pergunta(criterios_gravidade,
        'Tem criterios de risco acrescido (oncologico, dialise, imunossuprimido)?', _),
    pergunta(suporte_domicilio,
        'Tem telemovel e acompanhamento disponivel em casa?', C2),
    C is min(C1, C2),
    assert_just('D-R10: Dispneia ligeira no contexto de febre/infeccao sem criterios de gravidade. Monitorizar em casa nas proximas 24h. Reavalie urgentemente se agravar.', C),
    !.

regra_dispneia('TRANSFERENCIA -> Enfermeiro SNS24', 0.5) :-
    assert_just('D-R11 (Fallback): Dispneia sem criterios claros de triagem. Avaliacao clinica adicional necessaria.', 0.5).

% =============================================================
% SECCAO D: FLUXO DE TOSSE (T-Rx)
% Assinatura: regra_tosse(-Disposicao, -Certeza)
% =============================================================

regra_tosse('EMERGENCIA (112 / INEM)', C) :-
    pergunta(hemoptises,
        'Esta a tossir sangue (expectoracao visivelmente hematica)?', C1),
    pergunta(dispneia_assoc,
        'Tem tambem falta de ar intensa associada a tosse?', C2),
    C is min(C1, C2),
    assert_just('T-R2: Hemoptises com dispneia. Sugestivo de TEP ou pneumonia necrotizante. EMERGENCIA - Ligue 112.', C),
    !.

regra_tosse('ADR-SU (Servico de Urgencia)', C) :-
    pergunta(dispneia_assoc,
        'Tem falta de ar associada a tosse?', C1),
    pergunta(criterios_gravidade,
        'Tem comorbilidade grave (DPOC severo, oncologico activo, imunossuprimido)?', C2),
    C is min(C1, C2),
    assert_just('T-R4: Tosse com dispneia num utente com factor de risco grave. Urgencia hospitalar.', C),
    !.

regra_tosse('AUTOCUIDADO (Teste COVID + Isolamento 7 dias)', C) :-
    pergunta(febre_assoc,
        'Tem febre associada a tosse?', C1),
    \+ pergunta(criterios_gravidade,
        'Tem criterios de gravidade?', _),
    (   pergunta(anosmia,
            'Teve perda subita do olfacto nos ultimos 7 dias?', C2)
    ;   pergunta(ageusia,
            'Teve perda subita do paladar nos ultimos 7 dias?', C2)
    ),
    pergunta(suporte_domicilio,
        'Tem telemovel e apoio em casa para isolamento?', C3),
    C is min(C1, min(C2, C3)),
    assert_just('T-R9: Quadro sugestivo de infeccao por SARS-CoV-2 (febre + anosmia/ageusia, sem criterios de gravidade). Realizar teste rapido e isolar 7 dias. Reavalie se agravar.', C),
    !.

regra_tosse('AUTOCUIDADO SEM TESTE COVID', C) :-
    \+ pergunta(febre_assoc,
        'Tem febre associada a tosse?', _),
    \+ pergunta(criterios_gravidade,
        'Tem criterios de gravidade?', _),
    \+ pergunta(comorbilidades,
        'Tem doencas cronicas respiratorias (DPOC, asma, fibrose)?', _),
    % Todas as premissas sao negacoes; sem premissas afirmativas para calcular min.
    % Certeza de fallback conservadora: 0.7 (ausencia de factores de risco e relativamente certa).
    C = 0.7,
    assert_just('T-R11: Tosse ligeira e isolada, sem febre, sem sinais de gravidade, sem comorbilidades. Etiologia provavelmente benigna (viral/pos-viral). Vigilancia domiciliaria.', C),
    !.

regra_tosse('TRANSFERENCIA -> Enfermeiro SNS24', 0.5) :-
    assert_just('T-R13 (Fallback): Quadro de tosse sem criterios claros de triagem. Avaliacao clinica adicional necessaria.', 0.5).
