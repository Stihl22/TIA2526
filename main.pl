% =============================================================
% SISD SNS24 - PONTO DE ENTRADA (main.pl)
% Carrega todos os modulos pela ordem correcta de dependencias:
%   base_dados -> explicacao -> interface -> conhecimento -> motor
%
% Para iniciar: swipl -g iniciar_triagem main.pl
%         ou dentro do SWI-Prolog: ?- [main]. ?- iniciar_triagem.
% =============================================================

:- [base_dados].    % 1o: declaracoes dinamicas (sem dependencias)
:- [explicacao].    % 2o: assert_just/2, mostrar_explicacao/0
:- [interface].     % 3o: pergunta/3, limpar_tudo/0 (usado em conhecimento)
:- [conhecimento].  % 4o: pre_triagem/2, regra_febre/2, regra_dispneia/2, regra_tosse/2
:- [motor].         % 5o: avaliar/2 (usa conhecimento + base_dados)

% Inicializacao automatica ao correr: swipl -g iniciar_triagem main.pl
:- initialization(iniciar_triagem, main).
