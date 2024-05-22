import pandas as pd
import os
from datetime import datetime

from src.servicos_ufs.rpa import RPA, SC
from src.servicos_ufs.crud import BRONZE_FOLDER, SILVER_FOLDER, GOLD_FOLDER, salvar_dataframe


def extrair_servicos_action(uf: RPA):
    servicos = uf.extrair_servicos()
    if len(servicos) != 0:
        salvar_dataframe(pd.DataFrame(servicos), BRONZE_FOLDER, name=uf.obter_uf())


def unir_arquivos_action(folder, output_file):
    dfs = []
    for file_name in os.listdir(folder):
        file_path = os.path.join(folder, file_name)
        if file_name.lower().endswith(".xlsx"):
            dfs.append(pd.read_excel(file_path))
    if len(dfs) != 0:
        salvar_dataframe(pd.concat(dfs), SILVER_FOLDER, name=output_file)


if __name__ == "__main__":
    uf = SC()
    extrair_servicos_action(uf)
