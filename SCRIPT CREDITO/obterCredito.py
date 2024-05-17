import requests
import json
import pandas as pd
from IPython.display import display

token = "eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJBUEkgZGUgSW50ZWdyYcOnw6NvIExvZ3VzIiwic3ViIjoiNjIyNjUxMDgzODMiLCJpYXQiOjE3MDgwMDQzMTcsImV4cCI6MTcwODA5MDcxN30.HGBJtO1c0p045KByJ861puA3xc1O_vN0lDOMuDama90"

def obterCredito(exercicio: int, totalRegistroPagina=1, pagina_especifica=None):
    """
    Função para organizar a estrutura do JSON e salvar os dados em um arquivo Excel.
    """
    try:
        pagina = 1
        while True:
            if pagina_especifica is not None and pagina != pagina_especifica:
                break

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
                if resposta_dado is None:
                    print("Resposta_dado é None. Encerrando o loop.")
                    break
                
                registros_pai = []
                itens_filhos = []

                for registro in resposta_dado.get("registros", []):
                    id_pai = registro.get("id")
                    
                    registro_pai = extrairDadosPai(registro, id_pai)
                    registros_pai.append(registro_pai)
                    
                    extrairDadosFilho(registro, itens_filhos, id_pai)

                df_registros_pai = pd.DataFrame(registros_pai)
                df_itens_filhos = pd.DataFrame(itens_filhos)

                salvarEmExcel(df_registros_pai, df_itens_filhos, exercicio, pagina)

                if pagina_especifica is not None:
                    break  # Se uma página específica foi fornecida, saia do loop depois de processá-la

                pagina += 1
            else:
                break
    except requests.exceptions.HTTPError as err:
        print(f"Erro HTTP: {err}")
    except Exception as e:
        print(f"Ocorreu um erro durante a organização dos dados: {e}")


def extrairDadosPai(registro, id_pai):
    """
    Extrai os dados do registro pai.
    alguns campos comentados pois não se encontra, possivelmente excluidos! 
    """
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
        #"dataReferencia": registro.get("dataReferencia"),
        #"documentoReferencia": registro.get("documentoReferencia"),
        #"dataDiarioOficial": registro.get("dataDiarioOficial"),
        #"numeroDiarioOficial": registro.get("numeroDiarioOficial"),
        "observacao": registro.get("observacao"),
        "dataContabilizacao": registro.get("dataContabilizacao"),
        "codigoDocAlterado": registro.get("codigoDocAlterado"),
        "dataCancelamento": registro.get("dataCancelamento"),
        "justificativaCancelamento": registro.get("justificativaCancelamento"),
        "instancia": registro.get("instancia"),
        "semCobertura": registro.get("semCobertura"),
    }
    return registro_pai

def extrairDadosFilho(registro, itens_filhos, id_pai):
    """
    Extrai os dados dos itens de acréscimo e decréscimo.
    """
    for tipo_item, itens in {"Acréscimo": registro.get("itensAcrescimo", []), "Decréscimo": registro.get("itensDecrescimo", [])}.items():
        if itens is not None:  # Verifica se a lista de itens não é None
            for item in itens:
                item_data = {
                    "id_pai": id_pai,
                    "Tipo_Item": tipo_item
                }
                for classificador in item.get("classificadores", []):
                    classificador_temp = dict(classificador)
                    del classificador_temp["codigoTipoClassificador"]
                    del classificador_temp["nomeTipoClassificador"]
                    prefix = f"{classificador['nomeTipoClassificador']}"
                    for key, value in classificador_temp.items():
                        item_data[f"{prefix}"] = value

                item_data["Valor"] = item.get("valor")
                item_data["CodigoUGDeduzida"] = item.get("codigoUGDeduzida")
                itens_filhos.append(item_data)


def salvarEmExcel(df_registros_pai, df_itens_filhos, exercicio, pagina):
    """
    Salva os DataFrames em um arquivo Excel.
    """
    with pd.ExcelWriter(f"dados_solicitacao_credito_{exercicio}_pagina_{pagina}.xlsx") as writer:
        df_registros_pai.to_excel(writer, sheet_name="Registros_Pai", index=False)
        df_itens_filhos.to_excel(writer, sheet_name="Filhos", index=False)
    print(f"Dados da página {pagina} salvos com sucesso em um arquivo Excel.")
    

obterCredito(exercicio=2024, pagina_especifica=1)