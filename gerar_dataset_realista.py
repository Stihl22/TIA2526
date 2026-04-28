import pandas as pd

# Atributos extraídos da base de conhecimento
booleans = [
    'consciencia', 'dificuldade_resp_grave', 'hemorragia_grave',
    'manchas_pele', 'cefaleia_rigidez', 'convulsao_febril', 'febre_gte_40',
    'duracao_gt_48h', 'agravamento_progressivo', 'criterios_gravidade',
    'desidratacao', 'comorbilidades', 'duracao_lt_48h', 'cede_antipireticos',
    'suporte_domicilio', 'cianose', 'incapacidade_falar', 'estridor',
    'dispneia_repouso', 'dor_toracica', 'pieira', 'asma_conhecida',
    'febre_assoc', 'hemoptises', 'dispneia_assoc', 'anosmia', 'ageusia'
]

def base_row():
    return {attr: 0 for attr in booleans}

casos = []

# --- CASOS DE PRÉ-TRIAGEM (EMERGÊNCIA ABSOLUTA) ---
# Caso 1: Paciente Inconsciente (Ex: Acidente Vascular Cerebral grave, Síncope)
for _ in range(5):
    r = base_row()
    r['consciencia'] = 0 # Não responde
    r['sintoma_principal'] = 'Qualquer'
    r['Classe_Desfecho'] = 'EMERGENCIA ABSOLUTA (Ligue 112 / INEM)'
    casos.append(r)

# Caso 2: Hemorragia Ativa Incontrolável (Ex: Acidente de viação)
for _ in range(5):
    r = base_row()
    r['consciencia'] = 1
    r['hemorragia_grave'] = 1
    r['sintoma_principal'] = 'Qualquer'
    r['Classe_Desfecho'] = 'EMERGENCIA ABSOLUTA (Ligue 112 / INEM)'
    casos.append(r)

# --- CASOS DE FEBRE ---
# Caso 3: Criança com Suspeita de Meningite Meningocócica
for _ in range(5):
    r = base_row()
    r['consciencia'] = 1
    r['sintoma_principal'] = 'Febre'
    r['manchas_pele'] = 1
    r['cefaleia_rigidez'] = 1
    r['Classe_Desfecho'] = 'EMERGENCIA (112 / INEM)'
    casos.append(r)

# Caso 4: Hiperpirexia (Febre > 40ºC)
for _ in range(5):
    r = base_row()
    r['consciencia'] = 1
    r['sintoma_principal'] = 'Febre'
    r['febre_gte_40'] = 1
    r['Classe_Desfecho'] = 'ADR-SU (Servico de Urgencia)'
    casos.append(r)

# Caso 5: Utente com Comorbilidades e Febre
for _ in range(5):
    r = base_row()
    r['consciencia'] = 1
    r['sintoma_principal'] = 'Febre'
    r['comorbilidades'] = 1
    r['Classe_Desfecho'] = 'CONSULTA CSP (Centro de Saude, nas proximas 24h)'
    casos.append(r)

# Caso 6: Gripe Normal / Febre Benigna (Autocuidado)
for _ in range(8):
    r = base_row()
    r['consciencia'] = 1
    r['sintoma_principal'] = 'Febre'
    r['duracao_lt_48h'] = 1
    r['cede_antipireticos'] = 1
    r['suporte_domicilio'] = 1
    r['Classe_Desfecho'] = 'AUTOCUIDADO COM VIGILANCIA'
    casos.append(r)

# --- CASOS DE DISPNEIA ---
# Caso 7: Ataque de Asma Agudo / Anafilaxia (Pieira inaugural)
for _ in range(5):
    r = base_row()
    r['consciencia'] = 1
    r['sintoma_principal'] = 'Dispneia'
    r['pieira'] = 1
    r['asma_conhecida'] = 0
    r['Classe_Desfecho'] = 'ADR-SU (Servico de Urgencia)'
    casos.append(r)

# Caso 8: EAM / Tromboembolismo Pulmonar (Dispneia + Dor Torácica)
for _ in range(5):
    r = base_row()
    r['consciencia'] = 1
    r['sintoma_principal'] = 'Dispneia'
    r['dor_toracica'] = 1
    r['Classe_Desfecho'] = 'ADR-SU (Servico de Urgencia)'
    casos.append(r)

# Caso 9: Dispneia Ligeira num contexto infeccioso c/ acompanhamento (Autocuidado)
for _ in range(6):
    r = base_row()
    r['consciencia'] = 1
    r['sintoma_principal'] = 'Dispneia'
    r['febre_assoc'] = 1
    r['suporte_domicilio'] = 1
    r['Classe_Desfecho'] = 'AUTOCUIDADO COM VIGILANCIA (24h)'
    casos.append(r)

# --- CASOS DE TOSSE ---
# Caso 10: Tuberculose / TEP (Tosse com Sangue e Falta de ar)
for _ in range(5):
    r = base_row()
    r['consciencia'] = 1
    r['sintoma_principal'] = 'Tosse'
    r['hemoptises'] = 1
    r['dispneia_assoc'] = 1
    r['Classe_Desfecho'] = 'EMERGENCIA (112 / INEM)'
    casos.append(r)

# Caso 11: Covid-19 Clássico (Tosse, febre, perda olfato)
for _ in range(6):
    r = base_row()
    r['consciencia'] = 1
    r['sintoma_principal'] = 'Tosse'
    r['febre_assoc'] = 1
    r['anosmia'] = 1
    r['suporte_domicilio'] = 1
    r['Classe_Desfecho'] = 'AUTOCUIDADO (Teste COVID + Isolamento 7 dias)'
    casos.append(r)

# Caso 12: Tosse Ligeira Isolada (Pós-viral)
for _ in range(6):
    r = base_row()
    r['consciencia'] = 1
    r['sintoma_principal'] = 'Tosse'
    # Tudo o resto a 0 reflecte a ausência de sinais de gravidade
    r['Classe_Desfecho'] = 'AUTOCUIDADO SEM TESTE COVID'
    casos.append(r)

import random

# Tornar o suporte_domicilio irrelevante para a divisão primária (quase todos têm, independentemente da gravidade)
random.seed(42)
for r in casos:
    r['suporte_domicilio'] = random.choices([0, 1], weights=[0.2, 0.8])[0]

# Construir DataFrame
df = pd.DataFrame(casos)

# Reordenar colunas
colunas = ['sintoma_principal'] + booleans + ['Classe_Desfecho']
df = df[colunas]

# Exportar
df.to_csv('dataset_triagem.csv', index=False)
print(f"Gerados {len(df)} casos clínicos realistas baseados em personas (não aleatórios).")
print("Dataset guardado como 'dataset_triagem.csv'.")
