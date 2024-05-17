from API_siafe import get_token
import requests
import json
import pandas as pd

token = get_token()


def getCredito(exercicio:int, pagina:int, totalRegistroPagina = 5000):
    """
    função para obter dados solicitação de credito
    """

    url = f"https://tesouro.sefaz.pi.gov.br/siafe-api/solicitacao-credito/{exercicio}/{pagina}/{totalRegistroPagina}"
    headers = {"Content-Type": "application/json", "Authorization": token} 
    data = {"codigo": "",
            "codigoUG": "",
            "dataInicio": "2023-01-01",
            "dataFim": "2023-12-31",
            "dataAnulacaoInicio": "",
            "dataAnulacaoFim": ""}
    data = json.dumps(data)

    resposta = requests.post(url = url, headers = headers, data = data)

    if resposta.status_code == 200:
        resposta_dado = resposta.json()

        return resposta_dado
    else:
        print("erro na solicitação:", resposta.text)
        return None
    
    

def getEstruturaCredito():
    paginaInicial = 1
    exercicio = 2023
    linhas = []

    while True:
        credito = getCredito(exercicio, paginaInicial)

        # Verifica se a resposta é None
        if credito is None:
            break

        registros = credito.get("registros", [])

        if registros is not None:

            for registro in registros:
                linha = {}

                for chave, valor in registro.items():
                    if chave == "itensAcrescimo" or chave == "itensDecrescimo":
                        subregistros = valor
                        for subregistro in subregistros:
                            for classificador in subregistro.get("classificadores", []):
                                for i, v in classificador.items():
                                    linha[f"{chave}_{i}"] = v
                            linha[f"{chave}_valor"] = subregistro.get("valor")
                            linha[f"{chave}_codigoUGDeduzida"] = subregistro.get("codigoUGDeduzida")
                    else:
                        linha[chave] = valor

                linhas.append(linha)
                paginaInicial += 1

            if credito["totalPaginasRestantes"] == 0:
                break

    return pd.DataFrame(linhas)

df = getEstruturaCredito()