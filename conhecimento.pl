% =============================================================
% SISD SNS24 - BASE DE CONHECIMENTO (conhecimento.pl)
% Versao ASCII-only: todas as strings sao plain text.
% Regras de producao clinicas, ordenadas por gravidade.
%
% NOTA SOBRE \+ pergunta(X, Txt):
%   Seguro porque pergunta/2 usa cache (sim/1, nao/1).
%   Se X ja foi respondido com 'n', nao(X) esta assertado
%   e pergunta(X,_) falha sem voltar a perguntar ao utilizador.
%
% DEPENDENCIAS: base_dados.pl, explicacao.pl
%   (pergunta/2 definido em interface.pl - carregado antes)
% =============================================================

% =============================================================
% SECCAO A: PRE-TRIAGEM (Avaliacao ABC)
% Prioridade ABSOLUTA - avaliada SEMPRE antes do fluxo clinico.
% =============================================================

pre_triagem('EMERGENCIA ABSOLUTA (Ligue 112 / INEM)') :-
    \+ pergunta(consciencia,
        'O utente responde, fala e esta orientado no espaco e no tempo?'),
    assert_just('PRE-R1a: Ausencia de resposta ou consciencia. Compromisso neurologico grave (A do ABC). Activar INEM imediatamente.'),
    !.

pre_triagem('EMERGENCIA ABSOLUTA (Ligue 112 / INEM)') :-
    pergunta(dificuldade_resp_grave,
        'O utente tem dificuldade respiratoria intensa, cianose ou incapacidade de falar?'),
    assert_just('PRE-R1b: Compromisso respiratorio grave na pre-triagem (B do ABC). Activar INEM imediatamente.'),
    !.

pre_triagem('EMERGENCIA ABSOLUTA (Ligue 112 / INEM)') :-
    pergunta(hemorragia_grave,
        'O utente apresenta hemorragia activa e incontrolavel?'),
    assert_just('PRE-R1c: Hemorragia activa grave. Compromisso circulatorio (C do ABC). Activar INEM imediatamente.'),
    !.

% pre_triagem/1 falha se nao houver compromisso ABC.

% =============================================================
% SECCAO B: FLUXO DE FEBRE (F-Rx)
% Ordem: Emergencia -> Urgencia -> CSP -> Autocuidado -> Fallback
% =============================================================

regra_febre('EMERGENCIA (112 / INEM)') :-
    pergunta(manchas_pele,
        'Tem manchas vermelhas/purpuras na pele que NAO desaparecem ao pressionar com um copo?'),
    pergunta(cefaleia_rigidez,
        'Tem dor de cabeca intensa, rigidez no pescoco ou dor com a luz (fotofobia)?'),
    assert_just('F-R2: Purpura nao-branqueavel + sinais meningeos. Suspeita de Doenca Meningococica. EMERGENCIA - Ligue 112. (Corrigido de ADR-SU para 112 por criterio clinico.)'),
    !.

regra_febre('ADR-SU (Servico de Urgencia)') :-
    pergunta(convulsao_febril,
        'Teve alguma convulsao associada a febre, agora ou recentemente?'),
    assert_just('F-R3: Convulsao febril activa ou recente. Requer avaliacao medica urgente em SU.'),
    !.

regra_febre('ADR-SU (Servico de Urgencia)') :-
    pergunta(febre_gte_40,
        'A temperatura axilar medida e igual ou superior a 40 graus Celsius?'),
    assert_just('F-R4: Hiperpirexia (>= 40C). Risco de falencia organica e complicacoes neurologicas. Urgencia hospitalar.'),
    !.

regra_febre('ADR-SU (Servico de Urgencia)') :-
    pergunta(duracao_gt_48h,
        'A febre persiste ha MAIS de 48 horas sem melhoria?'),
    pergunta(agravamento_progressivo,
        'O estado geral esta a piorar progressivamente?'),
    pergunta(criterios_gravidade,
        'Tem falta de ar, vomitos incoerciveis, confusao mental ou dor toracica?'),
    assert_just('F-R7: Febre prolongada (> 48h) com agravamento do estado geral e criterios de gravidade. Urgencia hospitalar.'),
    !.

regra_febre('TRANSFERENCIA -> Enfermeiro SNS24') :-
    pergunta(desidratacao,
        'Tem sinais de desidratacao grave: boca muito seca, ausencia de urina, prostracao intensa?'),
    assert_just('F-R6: Desidratacao severa associada a febre. Requer avaliacao clinica - transferencia para enfermeiro SNS24.'),
    !.

regra_febre('CONSULTA CSP (Centro de Saude, nas proximas 24h)') :-
    pergunta(comorbilidades,
        'Tem doencas cronicas graves (insuficiencia renal/cardiaca, imunossupressao, diabetes descompensada)?'),
    assert_just('F-R8: Utente febril com comorbilidades de risco. Consulta medica obrigatoria nas proximas 24h.'),
    !.

regra_febre('AUTOCUIDADO COM VIGILANCIA') :-
    pergunta(duracao_lt_48h,
        'A febre comecou ha MENOS de 48 horas?'),
    pergunta(cede_antipireticos,
        'A febre baixa apos tomar paracetamol ou ibuprofeno na dose correcta?'),
    \+ pergunta(criterios_gravidade,
        'Tem falta de ar, vomitos persistentes, confusao mental ou dor toracica?'),
    \+ pergunta(comorbilidades,
        'Tem doencas cronicas graves?'),
    pergunta(suporte_domicilio,
        'Tem telemovel e pelo menos uma pessoa que o/a possa acompanhar em casa?'),
    assert_just('F-R11: Febre de curso benigno (< 48h, responsiva a antipireticos, sem criterios de gravidade, com suporte). Apto para vigilancia domiciliaria. Reavalie se agravar nas proximas 12-24h.'),
    !.

regra_febre('TRANSFERENCIA -> Enfermeiro SNS24') :-
    assert_just('F-R15 (Fallback): Quadro febril sem criterios claros. Transferencia para avaliacao clinica adicional.').

% =============================================================
% SECCAO C: FLUXO DE DISPNEIA (D-Rx)
% =============================================================

regra_dispneia('EMERGENCIA (112 / INEM)') :-
    (   pergunta(cianose,
            'Tem coloracao azulada (cianose) nos labios ou nas unhas?')
    ;   pergunta(incapacidade_falar,
            'Tem incapacidade de completar uma frase inteira devido a falta de ar?')
    ;   pergunta(estridor,
            'Ouve um som agudo e rude ao respirar (estridor)?')
    ),
    assert_just('D-R1/D-R3: Compromisso respiratorio iminente (cianose / incapacidade de falar / estridor). EMERGENCIA - Ligue 112.'),
    !.

regra_dispneia('ADR-SU (Servico de Urgencia)') :-
    pergunta(dispneia_repouso,
        'Sente falta de ar estando completamente em repouso (sem qualquer esforco)?'),
    assert_just('D-R5: Dispneia em repouso. Criterio directo de encaminhamento urgente para SU hospitalar.'),
    !.

regra_dispneia('ADR-SU (Servico de Urgencia)') :-
    pergunta(dor_toracica,
        'Tem dor no peito associada a falta de ar?'),
    assert_just('D-R6: Dispneia com dor toracica. Despiste urgente de SCA (sindrome coronaria aguda) ou TEP (tromboembolismo pulmonar).'),
    !.

regra_dispneia('ADR-SU (Servico de Urgencia)') :-
    pergunta(pieira,
        'Ouve sons tipo sibilos ou pieira ao respirar?'),
    \+ pergunta(asma_conhecida,
        'Tem diagnostico medico previo de asma bronquica?'),
    assert_just('D-R8: Pieira inaugural sem historico de asma. Possivel broncoespasmo severo ou reaccao anafilatica. Urgencia hospitalar.'),
    !.

regra_dispneia('AUTOCUIDADO COM VIGILANCIA (24h)') :-
    pergunta(febre_assoc,
        'Tem febre associada a esta falta de ar?'),
    \+ pergunta(criterios_gravidade,
        'Tem criterios de risco acrescido (oncologico, dialise, imunossuprimido)?'),
    pergunta(suporte_domicilio,
        'Tem telemovel e acompanhamento disponivel em casa?'),
    assert_just('D-R10: Dispneia ligeira no contexto de febre/infeccao sem criterios de gravidade. Monitorizar em casa nas proximas 24h. Reavalie urgentemente se agravar.'),
    !.

regra_dispneia('TRANSFERENCIA -> Enfermeiro SNS24') :-
    assert_just('D-R11 (Fallback): Dispneia sem criterios claros de triagem. Avaliacao clinica adicional necessaria.').

% =============================================================
% SECCAO D: FLUXO DE TOSSE (T-Rx)
% =============================================================

regra_tosse('EMERGENCIA (112 / INEM)') :-
    pergunta(hemoptises,
        'Esta a tossir sangue (expectoracao visivelmente hematica)?'),
    pergunta(dispneia_assoc,
        'Tem tambem falta de ar intensa associada a tosse?'),
    assert_just('T-R2: Hemoptises com dispneia. Sugestivo de TEP ou pneumonia necrotizante. EMERGENCIA - Ligue 112.'),
    !.

regra_tosse('ADR-SU (Servico de Urgencia)') :-
    pergunta(dispneia_assoc,
        'Tem falta de ar associada a tosse?'),
    pergunta(criterios_gravidade,
        'Tem comorbilidade grave (DPOC severo, oncologico activo, imunossuprimido)?'),
    assert_just('T-R4: Tosse com dispneia num utente com factor de risco grave. Urgencia hospitalar.'),
    !.

regra_tosse('AUTOCUIDADO (Teste COVID + Isolamento 7 dias)') :-
    pergunta(febre_assoc,
        'Tem febre associada a tosse?'),
    \+ pergunta(criterios_gravidade,
        'Tem criterios de gravidade?'),
    (   pergunta(anosmia,
            'Teve perda subita do olfacto nos ultimos 7 dias?')
    ;   pergunta(ageusia,
            'Teve perda subita do paladar nos ultimos 7 dias?')
    ),
    pergunta(suporte_domicilio,
        'Tem telemovel e apoio em casa para isolamento?'),
    assert_just('T-R9: Quadro sugestivo de infeccao por SARS-CoV-2 (febre + anosmia/ageusia, sem criterios de gravidade). Realizar teste rapido e isolar 7 dias. Reavalie se agravar.'),
    !.

regra_tosse('AUTOCUIDADO SEM TESTE COVID') :-
    \+ pergunta(febre_assoc,
        'Tem febre associada a tosse?'),
    \+ pergunta(criterios_gravidade,
        'Tem criterios de gravidade?'),
    \+ pergunta(comorbilidades,
        'Tem doencas cronicas respiratorias (DPOC, asma, fibrose)?'),
    assert_just('T-R11: Tosse ligeira e isolada, sem febre, sem sinais de gravidade, sem comorbilidades. Etiologia provavelmente benigna (viral/pos-viral). Vigilancia domiciliaria.'),
    !.

regra_tosse('TRANSFERENCIA -> Enfermeiro SNS24') :-
    assert_just('T-R13 (Fallback): Quadro de tosse sem criterios claros de triagem. Avaliacao clinica adicional necessaria.').