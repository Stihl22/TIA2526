% =============================================================
% SISD SNS24 - PONTO DE ENTRADA (main.pl)
% Carrega todos os módulos pela ordem correcta de dependências:
%   base_dados → explicacao → conhecimento → motor → interface
%
% Para iniciar: swipl -g iniciar_triagem main.pl
%         ou dentro do SWI-Prolog: ?- [main]. ?- iniciar_triagem.
% =============================================================

:- [base_dados].    % 1º: declarações dinâmicas (sem dependências)
:- [explicacao].    % 2º: assert_just/1, mostrar_explicacao/0
:- [interface].     % 3º: pergunta/2, limpar_tudo/0 (usado em conhecimento)
:- [conhecimento].  % 4º: pre_triagem/1, regra_febre/1, regra_dispneia/1, regra_tosse/1
:- [motor].         % 5º: avaliar/1 (usa conhecimento + base_dados)

% Inicialização automática ao correr: swipl -g iniciar_triagem main.pl
:- initialization(iniciar_triagem, main).