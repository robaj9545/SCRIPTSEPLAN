import pandas as pd


url = r"https://docs.google.com/spreadsheets/d/e/2PACX-1vTtfa9NbIDftQ2fN_kALu6ewiw8LM3L9aHs7xErp24tlzXpDSG4Mbxi4f7AYcXEoiBmpwxLnLYQsvhQ/pubhtml"
tables = pd.read_html(url,
                      header=1,
                      encoding='utf-8')

df_indicadores = tables[0].iloc[:,1:]
print(df_indicadores)