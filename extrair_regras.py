import pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text

def main():
    # 1. Carregar o dataset
    try:
        df = pd.read_csv('dataset_triagem_sns24.csv')
    except FileNotFoundError:
        print("Erro: O ficheiro 'dataset_triagem_sns24.csv' não foi encontrado.")
        print("Corre primeiro o script 'triagem.py' para gerar os dados.")
        return

    # 2. Separar as features (X) do target (y)
    X = df.drop(columns=['Classe_Desfecho'])
    y = df['Classe_Desfecho']

    # 3. Pré-processamento
    # Como a DecisionTreeClassifier do scikit-learn não lida nativamente com strings de categorias,
    # vamos transformar a coluna 'sintoma_principal' (que tem 'Febre', 'Dispneia', 'Tosse') 
    # em colunas binárias através de One-Hot Encoding.
    if 'sintoma_principal' in X.columns:
        X = pd.get_dummies(X, columns=['sintoma_principal'], drop_first=False)

    # 4. Treinar a Árvore de Decisão
    # random_state=42 garante que a árvore gerada é sempre a mesma em várias execuções
    clf = DecisionTreeClassifier(max_depth=5 ,random_state=42)
    clf.fit(X, y)

    # 5. Extração e visualização das regras em texto (formato IF-THEN)
    # export_text cria uma string legível da estrutura da árvore
    feature_names = list(X.columns)
    regras = export_text(clf, feature_names=feature_names)
    
    print("================================================================")
    print(" REGRAS EXTRAÍDAS DA ÁRVORE DE DECISÃO (Formato Árvore/IF-THEN)")
    print("================================================================\n")
    print(regras)
    
    print("\n[!] DICA PARA PROLOG:")
    print("Podes ler estas regras da seguinte forma:")
    print("- '<= 0.5' significa Falso (ou Não) -> equivaleria a '\\+ pergunta(...)'")
    print("- '>  0.5' significa Verdadeiro (ou Sim) -> equivaleria a 'pergunta(...)'")
    print("Exemplo: se vires 'consciencia <= 0.50' significa utente SEM consciencia.")

if __name__ == "__main__":
    main()
