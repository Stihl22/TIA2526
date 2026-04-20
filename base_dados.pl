% =============================================================
% SISD SNS24 - BASE DE DADOS (base_dados.pl)
% Todas as declarações dinâmicas do sistema.
% Nenhum outro módulo declara :- dynamic.
% =============================================================

% --- Cache de respostas do utente (Fact Caching) ---
:- dynamic sim/1.   % sim(Atributo): utente confirmou o atributo
:- dynamic nao/1.   % nao(Atributo): utente negou o atributo

% --- Estado da sessão ---
:- dynamic sintoma_principal/1.  % sintoma_principal(febre|dispneia|tosse)

% --- Motor de Explicação (P1MAX) ---
% Cada regra que dispara regista uma justificação aqui.
:- dynamic justificacao/2.
% justificacao(Ordem, Texto)
% Ordem: inteiro para imprimir as justificações na ordem correcta.

% Contador auxiliar para a ordem de justificações
:- dynamic contador_just/1.
contador_just(0).