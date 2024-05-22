import pandas as pd
import os

dag_folder = "servicos_ufs"

BRONZE_FOLDER = os.path.join(
    os.path.dirname(__file__), "..", "..", "dados", "bronze", dag_folder
)
SILVER_FOLDER = os.path.join(
    os.path.dirname(__file__), "..", "..", "dados", "silver", dag_folder
)
GOLD_FOLDER = os.path.join(
    os.path.dirname(__file__), "..", "..", "dados", "gold", dag_folder
)


def ler_json(folder: str, name="extratos"):
    file_path = os.path.join(folder, f"{name}.json")
    try:
        return pd.read_json(file_path, orient="records")
    except FileNotFoundError:
        return pd.DataFrame()


def ler_csv(folder: str, name="extratos"):
    file_path = os.path.join(folder, f"{name}.csv")
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        return pd.DataFrame()


def salvar_dataframe(df: pd.DataFrame, folder: str, name="servicos_ufs"):
    if not os.path.exists(folder):
        os.makedirs(folder)
    file_path = os.path.join(folder, f"{name}.json")

    df.to_json(file_path, orient="records")
