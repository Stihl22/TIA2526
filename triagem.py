import pandas as pd
import random
import numpy as np

# Definir os atributos extraídos do Prolog (todos booleanos 0 ou 1)
booleans = [
    'consciencia', 'dificuldade_resp_grave', 'hemorragia_grave', # ABC / Pré-triagem
    'manchas_pele', 'cefaleia_rigidez', 'convulsao_febril', 'febre_gte_40',
    'duracao_gt_48h', 'agravamento_progressivo', 'criterios_gravidade',
    'desidratacao', 'comorbilidades', 'duracao_lt_48h', 'cede_antipireticos',
    'suporte_domicilio', 'cianose', 'incapacidade_falar', 'estridor',
    'dispneia_repouso', 'dor_toracica', 'pieira', 'asma_conhecida',
    'febre_assoc', 'hemoptises', 'dispneia_assoc', 'anosmia', 'ageusia'
]

# Lógica Clínica baseada no SISD SNS24 em Prolog
def classificar_utente(row):
    # PRE-TRIAGEM (Avaliação ABC - Máxima Prioridade)
    if row['consciencia'] == 0:
        return 'EMERGENCIA ABSOLUTA (Ligue 112 / INEM)'
    if row['dificuldade_resp_grave'] == 1:
        return 'EMERGENCIA ABSOLUTA (Ligue 112 / INEM)'
    if row['hemorragia_grave'] == 1:
        return 'EMERGENCIA ABSOLUTA (Ligue 112 / INEM)'
    
    # Avaliação conforme o fluxo (Sintoma Principal)
    sintoma = row['sintoma_principal']
    
    if sintoma == 'Febre':
        if row['manchas_pele'] == 1 and row['cefaleia_rigidez'] == 1:
            return 'EMERGENCIA (112 / INEM)'
        if row['convulsao_febril'] == 1:
            return 'ADR-SU (Servico de Urgencia)'
        if row['febre_gte_40'] == 1:
            return 'ADR-SU (Servico de Urgencia)'
        if row['duracao_gt_48h'] == 1 and row['agravamento_progressivo'] == 1 and row['criterios_gravidade'] == 1:
            return 'ADR-SU (Servico de Urgencia)'
        if row['desidratacao'] == 1:
            return 'TRANSFERENCIA -> Enfermeiro SNS24'
        if row['comorbilidades'] == 1:
            return 'CONSULTA CSP (Centro de Saude, nas proximas 24h)'
        if row['duracao_lt_48h'] == 1 and row['cede_antipireticos'] == 1 and row['criterios_gravidade'] == 0 and row['comorbilidades'] == 0 and row['suporte_domicilio'] == 1:
            return 'AUTOCUIDADO COM VIGILANCIA'
        
        # Fallback de Febre (se nenhuma regra explícita disparar)
        return 'TRANSFERENCIA -> Enfermeiro SNS24'
        
    elif sintoma == 'Dispneia':
        if row['cianose'] == 1 or row['incapacidade_falar'] == 1 or row['estridor'] == 1:
            return 'EMERGENCIA (112 / INEM)'
        if row['dispneia_repouso'] == 1:
            return 'ADR-SU (Servico de Urgencia)'
        if row['dor_toracica'] == 1:
            return 'ADR-SU (Servico de Urgencia)'
        if row['pieira'] == 1 and row['asma_conhecida'] == 0:
            return 'ADR-SU (Servico de Urgencia)'
        if row['febre_assoc'] == 1 and row['criterios_gravidade'] == 0 and row['suporte_domicilio'] == 1:
            return 'AUTOCUIDADO COM VIGILANCIA (24h)'
            
        # Fallback Dispneia
        return 'TRANSFERENCIA -> Enfermeiro SNS24'
        
    elif sintoma == 'Tosse':
        if row['hemoptises'] == 1 and row['dispneia_assoc'] == 1:
            return 'EMERGENCIA (112 / INEM)'
        if row['dispneia_assoc'] == 1 and row['criterios_gravidade'] == 1:
            return 'ADR-SU (Servico de Urgencia)'
        if row['febre_assoc'] == 1 and row['criterios_gravidade'] == 0 and (row['anosmia'] == 1 or row['ageusia'] == 1) and row['suporte_domicilio'] == 1:
            return 'AUTOCUIDADO (Teste COVID + Isolamento 7 dias)'
        if row['febre_assoc'] == 0 and row['criterios_gravidade'] == 0 and row['comorbilidades'] == 0:
            return 'AUTOCUIDADO SEM TESTE COVID'
            
        # Fallback Tosse
        return 'TRANSFERENCIA -> Enfermeiro SNS24'

# Inicialização 
random.seed(42) # Para reprodutibilidade
numero_pacientes = 60
dados = []

for _ in range(numero_pacientes):
    # Gerar os boolenos maioritariamente falsos (saudável na maior parte do tempo)
    row = {attr: random.choices([0, 1], weights=[0.8, 0.2])[0] for attr in booleans}
    
    # Ajustes lógicos de pré-triagem (a maioria das pessoas TEM consciência e NÃO TEM hemorragia)
    row['consciencia'] = random.choices([0, 1], weights=[0.05, 0.95])[0]
    row['dificuldade_resp_grave'] = random.choices([0, 1], weights=[0.95, 0.05])[0]
    row['hemorragia_grave'] = random.choices([0, 1], weights=[0.95, 0.05])[0]
    
    # Prevenir contradições biológicas
    if row['duracao_gt_48h'] == 1:
        row['duracao_lt_48h'] = 0
    elif row['duracao_lt_48h'] == 1:
        row['duracao_gt_48h'] = 0
        
    # Atribuir o algoritmo/fluxo avaliado
    row['sintoma_principal'] = random.choice(['Febre', 'Dispneia', 'Tosse'])
    
    # Preencher a Classe de Desfecho baseada na Árvore/Regras
    row['Classe_Desfecho'] = classificar_utente(row)
    dados.append(row)

# Construir o Pandas DataFrame
df = pd.DataFrame(dados)

# Ordenar colunas para que o Desfecho final seja a última
colunas_finais = ['sintoma_principal'] + booleans + ['Classe_Desfecho']
df = df[colunas_finais]

# Exportar para CSV
df.to_csv('dataset_triagem_sns24.csv', index=False)
print("Ficheiro gerado com sucesso!")
print(df.head())
