import pandas as pd

def ler_excel_e_transformar_em_lista(nome_arquivo, nome_coluna):
    try:
        # Lê o arquivo Excel
        df = pd.read_excel(nome_arquivo)
        
        # Obtém os dados da coluna especificada
        dados_coluna = df[nome_coluna].tolist()
        
        return dados_coluna
    except Exception as e:
        print("Ocorreu um erro:", e)
        return None

# Nome do arquivo Excel e nome da coluna
nome_arquivo = "Arquivo2024.xlsx"
nome_coluna = "numero"

# Chama a função para ler o arquivo e transformar em lista
lista_numeros = ler_excel_e_transformar_em_lista(nome_arquivo, nome_coluna)

if lista_numeros:
    print("Lista de números obtida com sucesso:")
    print(lista_numeros)
else:
    print("Não foi possível obter a lista de números.")

# Se a lista de números foi obtida com sucesso, então continue com o restante do script
if lista_numeros:
    # Define a lista de chaves
    chaves = lista_numeros

    # Inicia a consulta SQL
    sql_query = 'SELECT *, concat("codigoUG", \'.\', "Nota de Empenho") as chave\nFROM orcamento.fato_saldo fs2\nWHERE concat("codigoUG", \'.\', "Nota de Empenho") IN (\n'

    # Adiciona cada chave à consulta SQL
    sql_query += ',\n'.join(f"  '{chave}'" for chave in chaves)

    # Finaliza a consulta SQL
    sql_query += '\n);'

    # Imprime a consulta SQL completa
    print("Consulta SQL gerada:")
    print(sql_query)
