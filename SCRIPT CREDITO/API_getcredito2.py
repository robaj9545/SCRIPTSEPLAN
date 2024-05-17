import requests
import json
import pandas as pd

token = "eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJBUEkgZGUgSW50ZWdyYcOnw6NvIExvZ3VzIiwic3ViIjoiNjIyNjUxMDgzODMiLCJpYXQiOjE3MDc0Nzc1NDAsImV4cCI6MTcwNzU2Mzk0MH0.eVvBb66PwgzQaLk4TIDvI_GzX-GUgEdflth1KScMxRs"

def getCredito(exercicio: int, pagina: int, totalRegistroPagina=5000):
    """
    Função para organizar a estrutura do JSON e salvar os dados em um arquivo Excel.
    """
    try:
        url = f"https://tesouro.sefaz.pi.gov.br/siafe-api/solicitacao-credito/{exercicio}/{pagina}/{totalRegistroPagina}"
        headers = {"Content-Type": "application/json", "Authorization": token}
        data = {
            "codigo": "",
            "codigoUG": "190101",
            "dataInicio": "2024-01-01",
            "dataFim": "2024-12-31",
            "dataAnulacaoInicio": "",
            "dataAnulacaoFim": ""
        }
        data = json.dumps(data)

        resposta = requests.post(url=url, headers=headers, data=data)
        resposta.raise_for_status()  # Lança uma exceção se o status code não for bem-sucedido

        if resposta.status_code == 200:
            resposta_dado = resposta.json()
            
            # Criar listas vazias para armazenar os dados dos registros pai e dos filhos
            registros_pai = []
            itens_filhos = []

            # Iterar sobre os registros do JSON
            for registro in resposta_dado.get("registros", []):
                id_pai = registro.get("id")
                
                # Extrair os dados dos registros pai
                registro_pai = {
                    "id": id_pai,
                    "codigo": registro.get("codigo"),
                    "dataEmissao": registro.get("dataEmissao"),
                    "codigoUGEmitente": registro.get("codigoUGEmitente"),
                    "codigoUGAcrescida": registro.get("codigoUGAcrescida"),
                    "statusDocumento": registro.get("statusDocumento"),
                    "assunto": registro.get("assunto"),
                    "tipoAbertura": registro.get("tipoAbertura"),
                    "tipoCredito": registro.get("tipoCredito"),
                    "origem": registro.get("origem"),
                    "dataReferencia": registro.get("dataReferencia"),
                    "documentoReferencia": registro.get("documentoReferencia"),
                    "dataDiarioOficial": registro.get("dataDiarioOficial"),
                    "numeroDiarioOficial": registro.get("numeroDiarioOficial"),
                    "observacao": registro.get("observacao"),
                    "dataContabilizacao": registro.get("dataContabilizacao"),
                    "codigoDocAlterado": registro.get("codigoDocAlterado"),
                    "dataCancelamento": registro.get("dataCancelamento"),
                    "justificativaCancelamento": registro.get("justificativaCancelamento")
                }
                registros_pai.append(registro_pai)
                
                # Extrair os dados dos itens de acréscimo e decréscimo
                for tipo_item, itens in {"Acréscimo": registro.get("itensAcrescimo", []), "Decréscimo": registro.get("itensDecrescimo", [])}.items():
                    for item in itens:
                        item_data = {
                            "id_pai": id_pai,
                            "Tipo_Item": tipo_item
                        }
                        
                        # Adicionar os campos dos classificadores
                        for classificador in item.get("classificadores", []):
                            prefix = f"Classificador_{classificador['nomeTipoClassificador']}"
                            for key, value in classificador.items():
                                item_data[f"{prefix}_{key}"] = value

                        item_data["Valor"] = item.get("valor")
                        item_data["CodigoUGDeduzida"] = item.get("codigoUGDeduzida")
                        itens_filhos.append(item_data)

            # Criar DataFrames a partir das listas de dados
            df_registros_pai = pd.DataFrame(registros_pai)
            df_itens_filhos = pd.DataFrame(itens_filhos)

            # Salvar os DataFrames em um arquivo Excel
            with pd.ExcelWriter(f"dados_solicitacao_credito_{exercicio}_{pagina}.xlsx") as writer:
                df_registros_pai.to_excel(writer, sheet_name="Registros_Pai", index=False)
                df_itens_filhos.to_excel(writer, sheet_name="Filhos", index=False)

            print("Dados salvos com sucesso em um arquivo Excel.")
    except requests.exceptions.HTTPError as err:
        print(f"Erro HTTP: {err}")
    except Exception as e:
        print(f"Ocorreu um erro durante a organização dos dados: {e}")

# Exemplo de utilização da função
getCredito(2024, 1)
