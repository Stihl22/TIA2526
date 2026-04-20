% =================================================================
% PARTE B - REGRAS EXTRAÍDAS AUTOMATICAMENTE VIA DATA MINING
% =================================================================

% --- RAMO: NÃO É TOSSE (Febre ou Dispneia) ---

triagem_dm(transferencia_enfermeiro) :-
    \+ sintoma_principal(tosse),
    \+ dificuldade_resp_grave(sim),
    \+ hemorragia_grave(sim),
    \+ convulsao_febril(sim),
    \+ incapacidade_falar(sim).

triagem_dm(emergencia_112) :-
    \+ sintoma_principal(tosse),
    \+ dificuldade_resp_grave(sim),
    \+ hemorragia_grave(sim),
    \+ convulsao_febril(sim),
    incapacidade_falar(sim).

triagem_dm(adr_su) :-
    \+ sintoma_principal(tosse),
    \+ dificuldade_resp_grave(sim),
    \+ hemorragia_grave(sim),
    convulsao_febril(sim),
    \+ cede_antipireticos(sim).

triagem_dm(emergencia_112) :-
    \+ sintoma_principal(tosse),
    \+ dificuldade_resp_grave(sim),
    \+ hemorragia_grave(sim),
    convulsao_febril(sim),
    cede_antipireticos(sim).

triagem_dm(emergencia_absoluta_112) :-
    \+ sintoma_principal(tosse),
    \+ dificuldade_resp_grave(sim),
    hemorragia_grave(sim).

triagem_dm(emergencia_absoluta_112) :-
    \+ sintoma_principal(tosse),
    dificuldade_resp_grave(sim).

% --- RAMO: É TOSSE ---

triagem_dm(autocuidado_sem_teste_covid) :-
    sintoma_principal(tosse),
    \+ hemorragia_grave(sim),
    \+ comorbilidades(sim),
    \+ hemoptises(sim).

triagem_dm(transferencia_enfermeiro) :-
    sintoma_principal(tosse),
    \+ hemorragia_grave(sim),
    \+ comorbilidades(sim),
    hemoptises(sim).

triagem_dm(transferencia_enfermeiro) :-
    sintoma_principal(tosse),
    \+ hemorragia_grave(sim),
    comorbilidades(sim).

triagem_dm(emergencia_absoluta_112) :-
    sintoma_principal(tosse),
    hemorragia_grave(sim).