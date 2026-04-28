import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.tree import _tree

def get_text_pergunta(feature):
    textos = {
        'consciencia': 'O utente responde, fala e esta orientado no espaco e no tempo?',
        'dificuldade_resp_grave': 'O utente tem dificuldade respiratoria intensa, cianose ou incapacidade de falar?',
        'hemorragia_grave': 'O utente apresenta hemorragia activa e incontrolavel?',
        'manchas_pele': 'Tem manchas vermelhas/purpuras na pele que NAO desaparecem ao pressionar com um copo?',
        'cefaleia_rigidez': 'Tem dor de cabeca intensa, rigidez no pescoco ou dor com a luz (fotofobia)?',
        'convulsao_febril': 'Teve alguma convulsao associada a febre, agora ou recentemente?',
        'febre_gte_40': 'A temperatura axilar medida e igual ou superior a 40 graus Celsius?',
        'duracao_gt_48h': 'A febre persiste ha MAIS de 48 horas sem melhoria?',
        'agravamento_progressivo': 'O estado geral esta a piorar progressivamente?',
        'criterios_gravidade': 'Tem criterios de gravidade (ex: imunossuprimido, oncologico, etc)?',
        'desidratacao': 'Tem sinais de desidratacao grave: boca muito seca, ausencia de urina, prostracao intensa?',
        'comorbilidades': 'Tem doencas cronicas graves (insuficiencia renal/cardiaca, imunossupressao, diabetes descompensada)?',
        'duracao_lt_48h': 'A febre/sintoma comecou ha MENOS de 48 horas?',
        'cede_antipireticos': 'A febre baixa apos tomar paracetamol ou ibuprofeno na dose correcta?',
        'suporte_domicilio': 'Tem telemovel e pelo menos uma pessoa que o/a possa acompanhar em casa?',
        'cianose': 'Tem coloracao azulada (cianose) nos labios ou nas unhas?',
        'incapacidade_falar': 'Tem incapacidade de completar uma frase inteira devido a falta de ar?',
        'estridor': 'Ouve um som agudo e rude ao respirar (estridor)?',
        'dispneia_repouso': 'Sente falta de ar estando completamente em repouso (sem qualquer esforco)?',
        'dor_toracica': 'Tem dor no peito associada a falta de ar?',
        'pieira': 'Ouve sons tipo sibilos ou pieira ao respirar?',
        'asma_conhecida': 'Tem diagnostico medico previo de asma bronquica?',
        'febre_assoc': 'Tem febre associada?',
        'hemoptises': 'Esta a tossir sangue (expectoracao visivelmente hematica)?',
        'dispneia_assoc': 'Tem falta de ar associada a tosse?',
        'anosmia': 'Teve perda subita do olfacto nos ultimos 7 dias?',
        'ageusia': 'Teve perda subita do paladar nos ultimos 7 dias?'
    }
    return textos.get(feature, f'Tem o sintoma {feature}?')


def tree_to_prolog(tree, feature_names, classes):
    tree_ = tree.tree_
    feature_name = [
        feature_names[i] if i != _tree.TREE_UNDEFINED else "undefined!"
        for i in tree_.feature
    ]
    
    regras_prolog = []
    
    regras_prolog.append("% =============================================================")
    regras_prolog.append("% BASE DE CONHECIMENTO GERADA AUTOMATICAMENTE POR ML (Python)")
    regras_prolog.append("% Algoritmo: Decision Tree Classifier")
    regras_prolog.append("% =============================================================\n")
    regras_prolog.append(":- discontiguous regra_ml/2.")
    regras_prolog.append(":- discontiguous pre_triagem/2.\n")

    def recurse(node, path):
        if tree_.feature[node] != _tree.TREE_UNDEFINED:
            name = feature_name[node]
            threshold = tree_.threshold[node]
            recurse(tree_.children_left[node], path + [(name, 0)])
            recurse(tree_.children_right[node], path + [(name, 1)])
        else:
            counts = tree_.value[node][0]
            class_idx = counts.argmax()
            class_name = classes[class_idx]
            
            # Verificar se é regra de pré-triagem (ABC)
            is_pre_triagem = False
            for feat, val in path:
                if (feat == 'consciencia' and val == 0) or \
                   (feat == 'dificuldade_resp_grave' and val == 1) or \
                   (feat == 'hemorragia_grave' and val == 1):
                    is_pre_triagem = True
            
            if is_pre_triagem:
                regra_head = f"pre_triagem('{class_name}', C) :-"
            else:
                regra_head = f"regra_ml('{class_name}', C) :-"

            corpo = []
            afirmativas = []
            idx_certeza = 1
            
            for feat, val in path:
                if feat.startswith('sintoma_principal_'):
                    if val == 1:
                        sintoma = feat.split('_')[2].lower()
                        if sintoma != 'qualquer':
                            corpo.append(f"    sintoma_principal({sintoma})")
                    else:
                        # Se val == 0, significa que sintoma_principal != X
                        sintoma = feat.split('_')[2].lower()
                        if sintoma != 'qualquer':
                            corpo.append(f"    \\+ sintoma_principal({sintoma})")
                    continue
                
                texto = get_text_pergunta(feat)
                if val == 1:
                    corpo.append(f"    pergunta({feat}, '{texto}', C{idx_certeza})")
                    afirmativas.append(f"C{idx_certeza}")
                    idx_certeza += 1
                else:
                    corpo.append(f"    \\+ pergunta({feat}, '{texto}', _)")
            
            # Cálculo de Certeza
            if len(afirmativas) == 0:
                calc_certeza = "    C = 0.7"
            elif len(afirmativas) == 1:
                calc_certeza = f"    C = {afirmativas[0]}"
            else:
                eq = afirmativas[-1]
                for c_var in reversed(afirmativas[:-1]):
                    eq = f"min({c_var}, {eq})"
                calc_certeza = f"    C is {eq}"
                
            corpo.append(calc_certeza)
            
            path_str = str(path).replace("'", "''")
            corpo.append(f"    assert_just('Regra ML: {path_str}', C)")
            
            if len(corpo) > 0:
                regras_prolog.append(regra_head)
                regras_prolog.append(",\n".join(corpo) + ",\n    !.\n")

    recurse(0, [])
    
    regras_prolog.append("% --- Fallbacks de seguranca ---")
    regras_prolog.append("pre_triagem(_, _) :- fail.")
    regras_prolog.append("regra_ml('TRANSFERENCIA -> Enfermeiro SNS24', 0.5) :- assert_just('Fallback ML (Sintomas nao discriminados)', 0.5).")
    
    return "\n".join(regras_prolog)


def main():
    print("A treinar modelo para gerar conhecimento_ml.pl...")
    df = pd.read_csv('dataset_triagem.csv')
    df = pd.get_dummies(df, columns=['sintoma_principal'])
    
    X = df.drop('Classe_Desfecho', axis=1)
    y = df['Classe_Desfecho']
    
    clf = DecisionTreeClassifier(criterion='entropy', random_state=42)
    clf.fit(X, y)
    
    prolog_code = tree_to_prolog(clf, X.columns, clf.classes_)
    
    with open('conhecimento_ml.pl', 'w') as f:
        f.write(prolog_code)
    print("Sucesso!")

if __name__ == '__main__':
    main()
