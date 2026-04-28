% =============================================================
% SISD SNS24 - PONTO DE ENTRADA ML (main_ml.pl)
% Carrega a versao baseada em Machine Learning:
% =============================================================

:- [base_dados].    
:- [explicacao].    
:- [interface].     
:- [conhecimento_ml].  % <--- Regras geradas por arvore de decisao
:- [motor_ml].         % <--- Motor adaptado

% Inicializacao automatica ao correr: swipl -g iniciar_triagem main_ml.pl
:- initialization(iniciar_triagem, main).
