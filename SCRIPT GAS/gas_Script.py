import openpyxl
import pandas as pd


# Carregar a planilha
caminho_planilha = 'SEEG11.1-DADOS-NACIONAIS.xlsx'
nome_aba = 'Dados'  # Altere para o nome da aba onde estão os dados

# Carregar a planilha em um DataFrame do pandas
df = pd.read_excel(caminho_planilha, sheet_name=nome_aba)

# Identificar a coluna onde os anos estão presentes
colunas_anos = df.columns[11:64]  # Colunas L1 a BL1 correspondem aos anos

# Selecionar apenas as colunas desejadas
colunas_desejadas = ['Gás', 'Categoria emissora', 'Estado']
colunas_desejadas.extend(colunas_anos)

df_selecionado = df[colunas_desejadas]

# Crie uma lista vazia para armazenar os dados filtrados
dados_filtrados = []

# Itere sobre as linhas do DataFrame df_selecionado
for indice, linha in df_selecionado.iterrows():
    # Verifique se o gás é CO2e (t) GWP-AR5
    if linha['Gás'] == 'CO2e (t) GWP-AR5':
        # Adicione os dados à lista de dados filtrados
        dados_filtrados.append(linha)

# Crie um novo DataFrame com os dados filtrados
df_filtrado = pd.DataFrame(dados_filtrados)

# Crie uma lista vazia para armazenar os dados reorganizados
dados_reorganizados = []

# Itere sobre as linhas do DataFrame df_selecionado
for indice, linha in df_filtrado.iterrows():
    # Itere sobre as colunas de anos
    for ano, emissao in linha[3:].items():
        # Se a emissão for diferente de 0, adicione uma entrada à lista de dados reorganizados
        if emissao != 0:
            dados_reorganizados.append({
                'indicador-gás': linha['Gás'],
                'ano': int(ano),
                'estado': linha['Estado'],
                'setor - Categoria emissora': linha['Categoria emissora'],
                'emissoes': emissao
            })

# Crie um novo DataFrame com os dados reorganizados
df_reorganizado = pd.DataFrame(dados_reorganizados)