import requests
from IPython.display import display
import pandas as pd
import json
import sys
import os
import errno

sys.path.append(os.getcwd())
file_path = os.getcwd() + '\\Archives'
url_base = "https://tesouro.sefaz.pi.gov.br/siafe-api"


#
def get_token(user, passw):
    url = f"{url_base}/auth"

    headers = {"accept": "*/*", "Content-Type": "application/json"}
    data = json.dumps({"usuario": user, "senha": passw})
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        resposta_json = response.json()
        token = resposta_json.get("token")
        return token
    
    else:
        print("Erro ao obter o token de acesso:", response.text)
        return None
    
#
def get_contratos(api_token: str, pagina: int = 1, exercicio: int = 2024, totalRegistroPagina = 2):
    url = f"{url_base}/contrato/{exercicio}/{pagina}/{totalRegistroPagina}"
    headers = {"accept": "application/json", "Authorization": api_token}

    data = {
        "numeroContrato": "",
        "nomeContrato": "",
        "numeroOriginal": ""
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()  # Isso fará com que uma exceção seja lançada para respostas de erro HTTP

        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"Erro de HTTP ao obter contratos: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"Erro na requisição ao obter contratos: {req_err}")
    except Exception as e:
        print(f"Erro inesperado: {e}")

    return None


def get_contratos_num_automatico(api_token, exercicio, numeroAutomatico=None):
    url = f"{url_base}/contrato/{exercicio}/{numeroAutomatico}"
    headers = {"Authorization": api_token}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # erro 400/500 e pula
        if response.status_code in [400, 500]:
            return None

        #print("Contrato " + numeroAutomatico)
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        #if http_err.response.status_code not in [400, 500]:
        print(f"Erro de HTTP ao obter contratos: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"Erro na requisição ao obter contratos: {req_err}")
    except Exception as e:
        print(f"Erro inesperado: {e}")

    return None

if __name__ == "__main__":
    token = "eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJBUEkgZGUgSW50ZWdyYcOnw6NvIExvZ3VzIiwic3ViIjoiNjIyNjUxMDgzODMiLCJpYXQiOjE3MDg0Mjk3ODIsImV4cCI6MTcwODUxNjE4Mn0.5_XJJJYF_rQUSTDkkrW_tPVspBpTQ-5EBIH7pbc1Xco"# get_token("02960260341", "af32215310")

    ls_contratos = []

    pagina = 1

    while True:

        response = get_contratos(token, pagina=pagina)

        if response is None or not response.get("registros"):
            break
    
        contratos = response.get("registros", [])

        for contrato in contratos: 
            num_contrato = contrato["numeroContrato"]
            ls_contratos.append(num_contrato)
            #print(num_contrato)

        if not response.get("possuiProximaPagina"):
            break

        pagina += 1

    #ls_contratos = ls_contratos[7:] # COMEÇAR APARTIR DO 7 ELEMENTO


    df_contratos = []
    #ct_24 = [item for item in ls_contratos if (isinstance(item, str) and item.startswith('24')) or (isinstance(item, int) and str(item).startswith('24'))]
    for contrato in ls_contratos:
        ano = contrato[:2]
        ct = get_contratos_num_automatico(token, exercicio=f'20{ano}', numeroAutomatico=str(contrato))

        if ct is not None:
            dict = {
                "Número do Contrato": ct.get("codigo"),
                "Situação": ct.get("situacao"),
                "Número Original": ct.get("numeroOriginal"),
                "Número do Processo": ct.get("numProcesso"),
                "Objeto": ct.get("objeto"),
                "Natureza": ct.get("natureza"),
                "Tipo do Contratante": ct.get("tipoContratante"),
                "Código do Contratante": ct.get("codigoContratante"),
                "Nome do Contratante": ct.get("nomeContratante"),
                "Tipo do Contratado": ct.get("tipoContratado"),
                "Código do Contratado": ct.get("codigoContratado"),
                "Nome do Contratado": ct.get("nomeContratado"),
                "Código do Banco Favorecido": ct.get("codigoBancoFavorecido"),
                "Código da Agência": ct.get("codigoAgencia"),
                "Código da Conta": ct.get("codigoConta"),
                "Valor": ct.get("valor"),
                "Valor Total": ct.get("valorTotal"),
                "Garantia": ct.get("garantia"),
                "Valor da Garantia": ct.get("valorGarantia"),
                "Data da Proposta": ct.get("dataProposta"),
                "Data de Celebração": ct.get("dataCelebracao"),
                "Data de Publicação": ct.get("dataPublicacao"),
                "Data de Início da Vigência": ct.get("dataInicioVigencia"),
                "Data de Fim da Vigência": ct.get("dataFimVigencia"),
                "Código da Modalidade de Licitação": ct.get("codigoModalidadeLicitacao"),
                "Nome da Modalidade de Licitação": ct.get("nomeModalidadeLicitacao"),
                "Vínculo PPA": ct.get("vinculoPPA"),
                "Regime de Execução": ct.get("regimeExecucao"),
                "Modalidade": ct.get("modalidade"),
                "Percentual de Terceiro": ct.get("percentualTerceiro"),
                "Objetivo": ct.get("objetivo"),
                "Fundamentação Legal": ct.get("fundamentacaoLegal"),
                "Data de Conclusão": ct.get("dataConclusao"),
                "Status": ct.get("status"),
                "Responsáveis do Contrato": ct.get("responsaveisContrato"),
                "Tipo de Rescisão": ct.get("tipoRescisao"),
                "Data de Rescisão": ct.get("dataRescisao"),
                "Data de Publicação da Rescisão": ct.get("dataPublicacaoRescisao"),
                "Valor da Multa": ct.get("valorMulta"),
                "Aditivos": ct.get("aditivos"),
                "Etapas": ct.get("etapas"),
                "Reajustes": ct.get("reajustes"),
                "Data de Fim da Vigência Total": ct.get("dataFimVigenciaTotal"),
                "Códigos UGs Permitidas": ct.get("codUgsPermitidas")
            }

            df_contratos.append(dict)

    df = pd.DataFrame(df_contratos)
    #display(df)
    #df.to_excel("teste.xlsx", index=False)
