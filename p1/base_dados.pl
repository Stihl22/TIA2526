% =============================================================
% SISD SNS24 - BASE DE DADOS (base_dados.pl)
% Todas as declaracoes dinamicas do sistema.
% Nenhum outro modulo declara :- dynamic.
% =============================================================

% --- Cache de respostas do utente (Fact Caching) ---
:- dynamic sim/1.              % sim(Atributo): utente confirmou o atributo
:- dynamic nao/1.              % nao(Atributo): utente negou o atributo
:- dynamic certeza_memoria/2.  % certeza_memoria(Atributo, Certeza): grau de certeza [0.0, 1.0]

% --- Estado da sessao ---
:- dynamic sintoma_principal/1.  % sintoma_principal(febre|dispneia|tosse)

% --- Motor de Explicacao (P1MAX) ---
% Cada regra que dispara regista uma justificacao aqui.
:- dynamic justificacao/3.
% justificacao(Ordem, Texto, Certeza)
% Ordem:   inteiro para imprimir as justificacoes na ordem correcta.
% Certeza: grau de certeza da regra (min das premissas afirmativas).

% Contador auxiliar para a ordem de justificacoes
:- dynamic contador_just/1.
contador_just(0).
