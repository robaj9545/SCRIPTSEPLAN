import requests
import pandas as pd
import json
import sys
import os

sys.path.append(os.getcwd())
file_path = os.getcwd() + '\\Archives'
url_base = "https://tesouro.sefaz.pi.gov.br"


#
def get_token():
    url = f"{url_base}/siafe-api/auth"

    headers = {"accept": "*/*", "Content-Type": "application/json"}
    data = json.dumps({"usuario": "62265108383", "senha": "deadzera1"})
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        resposta_json = response.json()
        token = resposta_json.get("token")
        return token
    
    else:
        print("Erro ao obter o token de acesso:", response.text)
        return None


#
def get_fontes_detalhamento(api_token: str, exercicio: int):
    url = f"{url_base}/siafe-api/apoio-geral/fonte-recurso-detalhe/{exercicio}"
    api_token = get_token()
    headers = {"Authorization": api_token}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print("Erro ao obter fontes detalhadas:", response.text)
        return None


#
def get_nota_empenho(api_token: str, exercicio: int, pagina: int, totalRegistroPagina=5000):
    url = f"{url_base}/siafe-api/nota-empenho/{exercicio}/{pagina}/{totalRegistroPagina}"
    headers = {"Authorization": api_token, "Content-Type": "application/json"}

    data = json.dumps({
        "codigoUG": "",
        "dataAnulacaoInicio": "",
        "dataInicio": "2023-01-01",
        "dataAnulacaoFim": "",
        "dataFim": "2023-31-12",
        "codigoNE": ""
    })

    response = requests.post(url, headers=headers, data=data) 

    if response.status_code == 200:
        response_data = response.json()
        print(f"Página {pagina} deu certo!")

        # Verificar se há mais páginas disponíveis na resposta da API
        if "numeroProximaPagina" in response_data and response_data["numeroProximaPagina"] > 0:
            return response_data["registros"]
        else:
            return None
    else:
        print("Erro ao obter as notas de empenho:", response.text)
        return None
    
#
def get_credor(api_token: str, exercicio: int, pagina: int, totalRegistroPagina: int = 5000):
    url = f"{url_base}/siafe-api/apoio-geral/credor/{exercicio}/{pagina}/{totalRegistroPagina}"
    headers = {"accept": "application/json", "Authorization": api_token}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Lança uma exceção para códigos de status diferentes de 200

        if "maisPaginas" in response.text and response.get["maisPaginas"] != False:
            print(f"A resposta da página {pagina} está correta.")
            return response.json()
        else:
            return None
        

    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter informações dos credores: {e}")
        return None


#
def execute_fonte_recurso():
    linhas = []
    api_token = get_token()
    anos = list(range(2017, 2024))

    for ano in anos:
        fontes = get_fontes_detalhamento(api_token, ano)

        if fontes is not None:
            for fonte in fontes:
                linha = {
                    "Fonte": fonte["codigoFonte"],
                    "Detalhamento": fonte["codigo"],
                    "Descrição_fonte": fonte["tituloFonte"],
                    "Descrição_detalhamento": fonte["titulo"],
                    "ID - Fonte": f"{fonte['codigoFonte'][0]}.{fonte['codigoFonte'][1:3]}.{fonte['codigo']}"
                }
                linhas.append(linha)

    df = pd.DataFrame(linhas)
    df.drop_duplicates(subset="ID - Fonte", inplace=True)
    print(df)


    df.to_excel(file_path + "\Detalhamento_fontes.xlsx")

token = get_token()
print(token)
# Exemplo de uso
if False:
    linhas = []
    pagina = 1
    api_token = get_token()

    while True:
        empenhos = get_nota_empenho(api_token, 2023, pagina)
        
        if empenhos is not None:
            linhas.append(empenhos)
            pagina += 1
        else:
            # Se a resposta for None, não há mais páginas disponíveis
            break

    df = pd.DataFrame(linhas)
    df.to_excel("notas_empenho.xlsx", index=False)

# Exemplo de uso
if False:
    linhas = []
    pagina = 1
    api_token = get_token()

    while True:
        empenhos = get_credor(api_token, 2023, pagina)
        
        if empenhos is not None:
            linhas.append(empenhos)
            pagina += 1
        else:
            break

    df = pd.DataFrame(linhas)
    df.to_excel("credores.xlsx", index=False)

