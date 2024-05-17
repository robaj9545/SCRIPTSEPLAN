import json
import requests
import pandas as pd
import re

def obterNota(token, exercicio: int, pagina: int, totalRegistroPagina=5000):
    try:
        dados_totais = []  # Lista para armazenar os dados de todas as páginas

        while True:
            url = f"https://tesouro.sefaz.pi.gov.br/siafe-api/nota-empenho/{exercicio}/{pagina}/{totalRegistroPagina}"
            headers = {"Content-Type": "application/json", "Authorization": token}
            
            data = {
                "dataInicio": "2024-01-01",
                "dataFim": "2024-12-31",
            }
            data = json.dumps(data)
                    
            resposta = requests.post(url=url, headers=headers, data=data)
            resposta.raise_for_status()
    
            if resposta.status_code == 200:
                dados_resposta = resposta.json()
            
                
                # Listas para armazenar os dados
                dados_classificadores = []
                dados = []
                
                # Palavras-chave para filtragem
                palavras_chave = ["primeira infância", "pacto pelas crianças", "infância", "infantil", "criança", "creche", "carretinha", "primeira infancia", "pacto pelas criancas", "infancia", "crianca"]
                
                for dado in dados_resposta.get('registros', []):
                    if isinstance(dado, dict):
                        campopalavras = dado.get('observacao', '-').lower()
                        if any(re.search(re.escape(palavra), campopalavras) for palavra in palavras_chave):
                            # Coletando dados dos classificadores
                            classificadores_dict = {'id': dado['id']}
                            for classificador in dado['classificadores']:
                                classificadornome = classificador['nomeTipoClassificador']
                                if classificadornome == 'Unidade Orçamentária':
                                    classificadores_dict[classificador['nomeTipoClassificador']] = classificador['nomeClassificador']
                            dados_classificadores.append(classificadores_dict)
                            
                            # Coletando dados da ação
                            dados.append({
                                'id': dado['id'],
                                'codigo': dado['codigo'],
                                'codContrato': dado['codContrato'],
                                'observacao': dado['observacao'],
                            })
                    else:
                        print("NENHUMA PALAVRA CHAVE ENCONTRADA")
                            
                # Criando DataFrames
                df_classificadores = pd.DataFrame(dados_classificadores)
                df_dados = pd.DataFrame(dados)
    
                # Mesclando os DataFrames
                df_merged = pd.merge(df_classificadores, df_dados, on='id')
                
                # Adicionando os dados da página atual à lista de dados totais
                dados_totais.append(df_merged)
                
                if not dados_resposta.get("possuiProximaPagina"):
                    break
                
                pagina += 1
                print(f'pagina atual: {pagina}')
                    
        # Concatenando todos os DataFrames em um único DataFrame
        df_final = pd.concat(dados_totais, ignore_index=True)
        
        # Salvar o DataFrame geral em um arquivo Excel
        nome_arquivo = f"Arquivo{exercicio}.xlsx"
        df_final.to_excel(nome_arquivo, index=False)
        print(f"Arquivo '{nome_arquivo}' foi criado com sucesso!")
        
    except requests.exceptions.HTTPError as err:
        print(f"Erro HTTP: {err}")
    except Exception as e:
        print(f"Ocorreu um erro durante a organização dos dados: {e}")
        
if __name__ == "__main__":
    token = 'eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJBUEkgZGUgSW50ZWdyYcOnw6NvIExvZ3VzIiwic3ViIjoiNjIyNjUxMDgzODMiLCJpYXQiOjE3MTQ0Nzk1NjcsImV4cCI6MTcxNDU2NTk2N30.Zriog08Fj3piMnO2lNcHhGimxoTTeiKT7C8YDfNUYe4'
    exercicio = 2024
    pagina = 1

    obterNota(token, exercicio=exercicio, pagina=pagina)
    
