import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import pandas as pd
from IPython.display import display

def search_notebook(processor, generation, storage, ram, os, store):
    if store == "Amazon":
        url = f"https://www.amazon.com.br/s?k=notebook+{processor}+{generation}+{storage}+{ram}GB+{os}&_encoding=UTF8"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        notebooks = []

        for item in soup.find_all("div", class_="s-result-item"):
            try:
                title = item.find("span", class_="a-size-base-plus a-color-base a-text-normal").text.strip()
                price = float(item.find("span", class_="a-offscreen").text.replace("R$", "").replace(",", ".").strip())
                link = "https://www.amazon.com.br" + item.find("a", class_="a-link-normal a-text-normal").get("href")

                notebooks.append({"Modelo": title, "Preço": price, "Link": link, "Loja": store})
            except:
                pass

        return notebooks

def generate_pdf(notebooks):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for notebook in notebooks:
        pdf.cell(200, 10, txt=f"Modelo: {notebook['Modelo']}", ln=True)
        pdf.cell(200, 10, txt=f"Preço: R$ {notebook['Preço']:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Link: {notebook['Link']}", ln=True)
        pdf.cell(200, 10, txt=f"Loja: {notebook['Loja']}", ln=True)
        pdf.cell(200, 10, txt="", ln=True)  # Espaço entre os notebooks

    pdf.output("notebooks.pdf")

if __name__ == "__main__":
    processor_i5 = "i5"
    generation_10 = "10ª"
    storage_256 = "256GB"
    ram_8 = "8"
    os_windows = "Windows"
    os_linux = "Linux"
    max_price = 8000.00

    stores = ["Amazon"]  # Adicione mais lojas aqui

    notebooks = []

    for store in stores:
        notebooks += search_notebook(processor_i5, generation_10, storage_256, ram_8, os_windows, store)
        notebooks += search_notebook(processor_i5, generation_10, storage_256, ram_8, os_linux, store)

    #generate_pdf(notebooks)

    df = pd.DataFrame(notebooks)
    display(df)
