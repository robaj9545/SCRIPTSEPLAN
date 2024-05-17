import requests
import pandas as pd

# Configurações da API Custom Search
API_KEY = "AIzaSyDbcp2QWm2Rqe2SaMZkD9hIKBKh1pzdaTQ"
SEARCH_ENGINE_ID = "a5173f1cf87d947e7"

# Função para buscar notebooks
def search_notebooks(query):
    url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={SEARCH_ENGINE_ID}&q={query}"
    response = requests.get(url)
    data = response.json()
    return data.get('items', [])

# Função para filtrar notebooks por preço
def filter_notebooks(notebooks, max_price):
    filtered_notebooks = []
    for notebook in notebooks:
        price = notebook.get('pagemap', {}).get('offer', [{}])[0].get('price', '').replace('$', '').replace(',', '')
        if price.isdigit() and float(price) <= max_price:
            filtered_notebooks.append({
                'title': notebook.get('title', ''),
                'link': notebook.get('link', ''),
                'price': float(price)
            })
    return filtered_notebooks

# Função para encontrar o notebook mais barato
def find_cheapest_notebook(notebooks):
    if notebooks:
        cheapest = min(notebooks, key=lambda x: x['price'])
        return cheapest
    return None

# Função para relatar notebooks encontrados
def report_notebooks(notebooks, query):
    print(f"Resultados para '{query}':")
    for notebook in notebooks:
        print(f"Nome: {notebook['title']}")
        print(f"Preço: ${notebook['price']:.2f}")
        print(f"Link: {notebook['link']}")
        print()

# Pesquisa por um notebook i5 de 10ª geração com 256 SSD, 8 GB de RAM e sistema Linux/Windows até $9200
query_i5 = "notebook i5 10th generation 256 ssd 8gb ram Linux OR Windows"
notebooks_i5 = search_notebooks(query_i5)
filtered_notebooks_i5 = filter_notebooks(notebooks_i5, 9200)
cheapest_i5 = find_cheapest_notebook(filtered_notebooks_i5)
report_notebooks(filtered_notebooks_i5, query_i5)

if cheapest_i5:
    print("O notebook mais barato encontrado:")
    print(f"Nome: {cheapest_i5['title']}")
    print(f"Preço: ${cheapest_i5['price']:.2f}")
    print(f"Link: {cheapest_i5['link']}")
    print()

# Pesquisa por um notebook i3 de 11ª geração com 256 SSD, 8 GB de RAM e sistema Linux/Windows até $9200
query_i3 = "notebook i3 11th generation 256 ssd 8gb ram Linux OR Windows"
notebooks_i3 = search_notebooks(query_i3)
filtered_notebooks_i3 = filter_notebooks(notebooks_i3, 9200)
cheapest_i3 = find_cheapest_notebook(filtered_notebooks_i3)
report_notebooks(filtered_notebooks_i3, query_i3)

# Extrair campos relevantes
dados_formatados = [{'title': item['title'], 'link': item['link'], 'snippet': item['snippet'], 'formattedUrl': item['formattedUrl']} for item in notebooks_i3]

# Criar DataFrame
df = pd.DataFrame(dados_formatados)

# Exibir DataFrame
print(df)

if cheapest_i3:
    print("O notebook mais barato encontrado:")
    print(f"Nome: {cheapest_i3['title']}")
    print(f"Preço: ${cheapest_i3['price']:.2f}")
    print(f"Link: {cheapest_i3['link']}")
    print()
