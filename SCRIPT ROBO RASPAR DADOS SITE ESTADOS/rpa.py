from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import re
import time
from unidecode import unidecode

import pandas as pd
import sys
sys.path.insert(0, "./airflow")  # "./airflow"
from src.servicos_ufs.crud import BRONZE_FOLDER, salvar_dataframe, ler_csv


TEXT_CONTENT = "textContent"
H_REF = "href"
LINE_BREAK = "\n"
URL_SUFIX = "_url"

TIMEOUT = 20
WAIT_TIME = 1
CHROME_OPTIONS = Options()
# CHROME_OPTIONS.add_argument("--headless")
CHROME_OPTIONS.add_argument("--no-sandbox")
CHROME_OPTIONS.add_argument("--disable-dev-shm-usage")
CHROME_OPTIONS.add_argument("--log-level=3")

REMOTE_WEBDRIVER = "remote_chromedriver"

"""
https://docs.google.com/spreadsheets/d/1099knrexxnzQjXti7cIa5SKHAjc_tSGPhWZiVYGmWRg/edit?usp=drivesdk
"""


class RPA(ABC):
    ESTADO = "Estado"
    SERVICO = "Serviço"
    DESCRICAO = "Descrição"
    CATEGORIA = "Categoria"
    SUBCATEGORIA = "Sub Categoria"
    DIGITAL = "Digital"
    LINK = "Link"
    ORGAO = "Órgão"

    def __init__(self) -> None:
        # self.driver = webdriver.Remote(f"{REMOTE_WEBDRIVER}:4444/wd/hub", options=CHROME_OPTIONS)
        self.driver = webdriver.Chrome(
            options=CHROME_OPTIONS,
            service=Service(executable_path=ChromeDriverManager().install()),
        )
        # self.driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=CHROME_OPTIONS)
        self.wait = WebDriverWait(self.driver, TIMEOUT, ignored_exceptions=(NoSuchElementException, StaleElementReferenceException))
        self.action = ActionChains(self.driver)

    def clicar_em_elemento(self, element, sleep=0):
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        time.sleep(sleep)
        self.action.move_to_element(element)
        self.action.click()
        self.action.perform()

    def montar_descricao_de_paragrafos(self, identifier, by=By.CSS_SELECTOR):
        paragrafos = self.driver.find_element(by=by, value=identifier)
        paragrafos = paragrafos.find_elements(by=By.TAG_NAME, value="p")
        descricao = ""
        for paragrafo in paragrafos:
            descricao += paragrafo.get_attribute(TEXT_CONTENT) + LINE_BREAK
        return descricao

    def montar_descricao_do_elemento(self, element, css):
        paragrafos = element.find_elements(by=By.CSS_SELECTOR, value=css)
        descricao = ""
        for paragrafo in paragrafos:
            descricao += paragrafo.get_attribute(TEXT_CONTENT) + LINE_BREAK
        return descricao

    def montar_descricao_de_todos_os_filhos(self, identifier, by=By.CSS_SELECTOR):
        descricao = self.driver.find_element(by=by, value=identifier).get_attribute("innerText")
        return descricao

    def definir_digital_por_elemento(elements: list):
        digital = "Não"
        if len(elements):
            digital = "Sim"
        return digital

    def obter_lista_de_as(self, identifier, by=By.CSS_SELECTOR):
        container = self.wait.until(EC.presence_of_element_located((by, identifier)))
        return container.find_elements(by=By.TAG_NAME, value="a")

    def converter_texto_para_link(self, text):
        text = text.replace('-', ' ')  # Remova os hífens originais do texto
        text = text.replace('–', ' ')  # Remova os hífens originais do texto
        text = text.replace(',', ' ')  # Remova as vírgulas originais do texto
        text = text.replace('/', '')  # Remova as barras originais do texto
        text = unidecode(text)  # Remova os acentos
        text = text.lower()  # Converta para minúscula
        text = re.sub(r'\s+', '-', text)  # Substitua espaços e afins por "-"
        return text

    @abstractmethod
    def obter_uf(self) -> str:
        return ""

    @abstractmethod
    def extrair_servicos(self) -> pd.DataFrame:
        return []


class SC(RPA):
    def __init__(self) -> None:
        super().__init__()

    def obter_uf(self) -> str:
        return "SC"

    def extrair_servicos(self) -> pd.DataFrame:
        url = "https://www.sc.gov.br/todos-os-servicos"
        self.driver.get(url)

        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        CARREGANDO = "carregando"
        self.wait.until(EC.invisibility_of_element((By.CLASS_NAME, CARREGANDO)))

        urls = []

        ultima_pagina = False
        while not ultima_pagina:
            # Adicionar URLs
            identifier = "#conteudo-site > div > div > div > div > app-servicos > div > div > div > div.col-lg-8.order-lg-1.barra-principal"
            element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, identifier))
            )

            servicos = element.find_elements(by=By.TAG_NAME, value="a")
            for servico in servicos:
                url = servico.get_attribute("href")
                urls.append(url)

            # Ir para a próxima página
            identifier = "#conteudo-site > div > div > div > div > app-servicos > div > div > div > div.col-lg-8.order-lg-1.barra-principal > app-paginacao > div > div"
            paginacao = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier)
            paginas = paginacao.find_elements(by=By.TAG_NAME, value="button")
            numero_de_paginas = len(paginas)

            for i, pagina in enumerate(paginas):
                classe = pagina.get_attribute("class")
                if classe == "atual":
                    if i + 1 < numero_de_paginas:
                        # self.driver.execute_script("arguments[0].scrollIntoView();", paginas[i + 1])
                        # time.sleep(1)
                        # self.wait.until(EC.visibility_of(pagina))
                        # self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, first_identifier)))

                        self.clicar_em_elemento(paginas[i + 1])
                        self.wait.until(EC.invisibility_of_element((By.CLASS_NAME, CARREGANDO)))
                        break
                    else:
                        ultima_pagina = True
                        break

        output = []
        for url in urls:
            self.driver.get(url)
            self.wait.until(EC.invisibility_of_element((By.CLASS_NAME, CARREGANDO)))

            servico_output = {}
            servico_output[self.LINK] = url
            servico_output[self.ESTADO] = self.obter_uf()

            try:
                identifier = "#titulo-pagina"
                servico = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier))).get_attribute(TEXT_CONTENT)
                servico_output[self.SERVICO] = servico
            except Exception:
                print(f"Erro no Serviço: {url}")
            try:
                identifier = "#conteudo-site > div > div > div > div > app-detalhes-servico > div > div.container > div:nth-child(1) > div.col-lg-4.barra-lateral-container > div > section.secao-tema > div > a"
                categoria = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier).get_attribute(TEXT_CONTENT)
                servico_output[self.CATEGORIA] = categoria
            except Exception:
                print(f"Erro na Categoria: {url}")
            try:
                identifier = "#conteudo-site > div > div > div > div > app-detalhes-servico > div > div.container > div:nth-child(1) > div.col-lg-4.barra-lateral-container > div > section:nth-child(4) > div"
                sub_categoria = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier).get_attribute(TEXT_CONTENT)
                servico_output[self.SUBCATEGORIA] = sub_categoria
            except Exception:
                print(f"Erro na Sub-Categoria: {url}")
            try:
                identifier = "#conteudo-site > div > div > div > div > app-detalhes-servico > div > div.container > div:nth-child(1) > div.col-lg-8.barra-principal > section:nth-child(1) > div"
                descricao = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier).get_attribute(TEXT_CONTENT)
                servico_output[self.DESCRICAO] = descricao
            except Exception:
                print(f"Erro na Descrição: {url}")
            try:
                identifier = "#conteudo-site > div > div > div > div > app-detalhes-servico > div > div.container > div:nth-child(1) > div.col-lg-4.barra-lateral-container > div > section:nth-child(3) > div"
                digital = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier).get_attribute(TEXT_CONTENT)
                servico_output[self.DIGITAL] = digital
            except Exception:
                print(f"Erro no Digital: {url}")
            try:
                identifier = "#conteudo-site > div > div > div > div > app-detalhes-servico > div > div.container > div:nth-child(1) > div.col-lg-4.barra-lateral-container > div > section.secao-orgao > div > a"
                orgao = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier).get_attribute(TEXT_CONTENT)
                servico_output[self.ORGAO] = orgao
            except Exception:
                print(f"Erro no Órgão: {url}")

            output.append(servico_output)

            df = pd.DataFrame(output)
            salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())

        return pd.DataFrame(output)


class CE(RPA):
    def __init__(self) -> None:
        super().__init__()

    def obter_uf(self) -> str:
        return "CE"

    def extrair_servicos(self) -> pd.DataFrame:
        url = "https://cearadigital.ce.gov.br/"
        self.driver.get(url)

        # Busca por categorias
        identifier = "#categories > div"
        container = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier)))
        time.sleep(WAIT_TIME)

        # Busca de URLs de serviços
        output = []
        categorias = container.find_elements(by=By.TAG_NAME, value="article")
        for categoria in categorias:
            self.clicar_em_elemento(categoria, WAIT_TIME)

            identifier = "#areaContainer"
            container = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier)))

            nome_categoria = container.find_element(by=By.CLASS_NAME, value="level").find_element(by=By.TAG_NAME, value="p").get_attribute(TEXT_CONTENT)
            sub_categorias = container.find_elements(by=By.CLASS_NAME, value="collapse")
            for sub_categoria in sub_categorias:
                nome_sub_categoria = sub_categoria.find_element(by=By.CSS_SELECTOR, value="div.collapse-trigger > section > p").get_attribute(TEXT_CONTENT)
                servicos = sub_categoria.find_elements(by=By.TAG_NAME, value="a")
                for servico in servicos:
                    servico_output = {}
                    servico_output[self.CATEGORIA] = nome_categoria
                    servico_output[self.SUBCATEGORIA] = nome_sub_categoria
                    servico_output[self.LINK] = servico.get_attribute("href")
                    servico_output[self.ESTADO] = self.obter_uf()
                    output.append(servico_output)

        for i, row in enumerate(output):
            self.driver.get(row[self.LINK])
            time.sleep(WAIT_TIME)

            identifier = "#accordion-service-1-id > h2"
            servico = self.wait.until(EC.text_to_be_present_in_element_attribute((By.CSS_SELECTOR, identifier), TEXT_CONTENT, '\n          O que é?\n        '))

            try:
                identifier = "#__layout > div > main > div > div.container > main > header > div:nth-child(1) > h1"
                servico = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier).get_attribute(TEXT_CONTENT)
                output[i][self.SERVICO] = servico
            except Exception:
                print(f"Erro no Serviço: {row}")
            try:
                identifier = "#sect-service-1 > p"
                descricao = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier).get_attribute(TEXT_CONTENT)
                output[i][self.DESCRICAO] = descricao
            except Exception:
                print(f"Erro na descrição: {row}")
            try:
                identifier = "#__layout > div > main > div > div.container > main > header > div:nth-child(1) > div > span > span"
                digital = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier).get_attribute(TEXT_CONTENT)
                output[i][self.DIGITAL] = digital
            except Exception:
                print(f"Erro no digital: {row}")
            try:
                identifier = "#__layout > div > main > div > div.container > main > div > div > div:nth-child(5) > p.subcopy"
                orgao = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier).get_attribute(TEXT_CONTENT)
                output[i][self.ORGAO] = orgao
            except Exception:
                print(f"Erro no orgao: {row}")

            df = pd.DataFrame(output)
            salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())

        return pd.DataFrame(output)


class GO(RPA):
    def __init__(self) -> None:
        super().__init__()

    def obter_uf(self) -> str:
        return "GO"

    def encontrar_lista_de_servicos(self):
        identifier = "body > app-root > app-main > div > div > app-sidenav > div > div > div.content-sidenav > app-servicos > p"
        self.wait.until(EC.invisibility_of_element((By.CSS_SELECTOR, identifier)))

        identifier = "body > app-root > app-main > div > div > app-sidenav > div > div > div.content-sidenav > app-servicos > div"
        container = self.driver.find_element(By.CSS_SELECTOR, identifier)

        itens = container.find_elements(by=By.TAG_NAME, value="app-card-servico")
        return itens

    def extrair_servicos(self) -> pd.DataFrame:
        url = "https://www.go.gov.br/servicos/todos-os-servicos"
        self.driver.get(url)

        identifier = "#servicos > pagination-template > ul > li.small-screen"
        pagina_atual = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier))).get_attribute(TEXT_CONTENT)
        pagina_atual = re.search(r"(\d+) / (\d+)", pagina_atual)

        output = []
        pagina = 1
        while True:
            itens = self.encontrar_lista_de_servicos()

            for i in range(len(itens)):
                servico_output = {}

                itens = self.encontrar_lista_de_servicos()

                try:
                    element = itens[i].find_element(by=By.TAG_NAME, value="img")
                    sub_categoria = element.get_attribute("alt")
                    servico_output[self.SUBCATEGORIA] = sub_categoria

                    imagem = element.get_attribute("src")
                    categoria = re.search(r"([^/]+)\.svg", imagem).group(1) if imagem is not None else ""
                    servico_output[self.CATEGORIA] = categoria
                except Exception:
                    print(f"Erro na Categoria ou Sub-Categoria: Item {i}")
                try:
                    acessar = itens[i].find_elements(by=By.TAG_NAME, value="app-botao-acessar")
                    servico_output[self.DIGITAL] = self.definir_digital_por_elemento(acessar)
                except Exception:
                    print(f"Erro no Digital: Item {i}")

                identifier = "div > div.link-wrap-card > div > div > h3 > a"
                itens[i].find_element(by=By.CSS_SELECTOR, value=identifier).click()

                servico_output[self.LINK] = self.driver.current_url
                servico_output[self.ESTADO] = self.obter_uf()

                try:
                    identifier = "#content > div:nth-child(1) > h1"
                    servico = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier))).get_attribute(TEXT_CONTENT)
                    servico_output[self.SERVICO] = servico
                except Exception:
                    print(f"Erro no serviço: {servico_output[self.LINK]}")
                try:
                    identifier = "#content > div.info-servico > div"
                    servico_output[self.DESCRICAO] = self.montar_descricao_de_paragrafos(identifier)
                except Exception:
                    print(f"Erro na descrição: {servico_output[self.LINK]}")
                try:

                    identifier = "#content > div.o-inf-servico > div > accordion > expansion-panel:nth-child(3) > div > div.expansion-panel.closed > div > div > p > p"
                    orgao = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier).get_attribute(TEXT_CONTENT)
                    servico_output[self.ORGAO] = orgao
                except Exception:
                    print(f"Erro no órgão: {servico_output[self.LINK]}")

                output.append(servico_output)

                df = pd.DataFrame(output)
                salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())

                self.driver.back()

            if pagina_atual:
                if pagina_atual.group(1) == pagina_atual.group(2):
                    break

            # Paginação
            for _ in range(pagina):
                identifier = "#servicos > pagination-template > ul > li.pagination-next.ng-star-inserted > a"
                next_button = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier)))
                next_button.click()

            identifier = "#servicos > pagination-template > ul > li.small-screen"
            pagina_atual = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier))).get_attribute(TEXT_CONTENT)
            pagina_atual = re.search(r"(\d+) / (\d+)", pagina_atual)

            pagina += 1

        return pd.DataFrame(output)


class RJ(RPA):
    def __init__(self) -> None:
        super().__init__()

    def obter_uf(self) -> str:
        return "RJ"

    def encontrar_lista_de_categorias(self):
        identifier = "#root > div:nth-child(2) > div:nth-child(5) > div > div"
        container = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier)))
        itens = container.find_elements(by=By.TAG_NAME, value="button")
        return itens

    def encontrar_lista_de_paginas(self):
        identifier = "#root > div:nth-child(2) > div:nth-child(4) > div:nth-child(4) > nav > ul"
        container = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier)))
        paginas = container.find_elements(by=By.TAG_NAME, value="button")
        return paginas

    def encontrar_lista_de_servicos(self):
        itens = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="root"]/div[2]/div[4]/div[3]/div/div')))
        # itens = self.driver.find_elements(by=By.XPATH, value='//*[@id="root"]/div[2]/div[4]/div[3]/div/div')
        return itens

    def extrair_servicos(self) -> pd.DataFrame:
        urls = {
            "Cidadão": "https://www.rj.gov.br/cidadao/servicos",
            "Servidor": "https://www.rj.gov.br/servidor/servicos",
            "Empresa": "https://www.rj.gov.br/empresa/servicos",
            "Gestão Pública": "https://www.rj.gov.br/gestao_publica/servicos"
        }

        output = []
        for _, url in urls.items():
            self.driver.get(url)

            start_buttons = self.encontrar_lista_de_categorias()

            # Listar categorias
            for i in range(len(start_buttons)):
                buttons = self.encontrar_lista_de_categorias()
                print(f"{i+1}/{len(buttons)} categoria")

                buttons[i].click()

                identifier = "#root > div:nth-child(2) > div:nth-child(5) > div > h5"
                categoria = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier))).get_attribute(TEXT_CONTENT)
                print("\t", categoria)

                # Listar sub-categorias
                start_sub_buttons = self.encontrar_lista_de_categorias()
                for j in range(len(start_sub_buttons)):
                    sub_buttons = self.encontrar_lista_de_categorias()
                    print(f"{j+1}/{len(sub_buttons)} sub-categoria")
                    sub_buttons[j].click()

                    identifier = "#root > div:nth-child(2) > div:nth-child(4) > div:nth-child(2) > div > div > h5"
                    sub_categoria = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier))).get_attribute(TEXT_CONTENT)
                    print("\t", sub_categoria)

                    paginas = self.encontrar_lista_de_paginas()
                    n_paginas = int(paginas[-2].get_attribute(TEXT_CONTENT))

                    # Paginação
                    for p in range(n_paginas):
                        print(f"{p+1}/{n_paginas} página\n==============")

                        start_servicos_da_pagina = self.encontrar_lista_de_servicos()
                        print(f"{len(start_servicos_da_pagina)} servicos da página")
                        # Listar serviços
                        ultimo_servico = False
                        k = 0
                        while not ultimo_servico:
                            # Alcançar página
                            for _ in range(p):
                                attribute = "aria-current"

                                paginas = self.encontrar_lista_de_paginas()
                                elemento_atual = paginas[0]
                                for n in range(len(paginas)):
                                    if paginas[n].get_attribute(attribute):
                                        elemento_atual = paginas[n]
                                        pagina_atual = elemento_atual.get_attribute(TEXT_CONTENT)
                                        break
                                paginas[-1].click()
                                while elemento_atual.get_attribute(attribute) and elemento_atual.get_attribute(TEXT_CONTENT) == pagina_atual:
                                    time.sleep(0.01 * WAIT_TIME)

                            servicos_da_pagina = self.encontrar_lista_de_servicos()
                            print(f"{k+1}/{len(servicos_da_pagina)} servico da página")

                            self.clicar_em_elemento(servicos_da_pagina[k])

                            servico_output = {}
                            servico_output[self.CATEGORIA] = categoria
                            servico_output[self.SUBCATEGORIA] = sub_categoria
                            servico_output[self.LINK] = self.driver.current_url
                            servico_output[self.ESTADO] = self.obter_uf()
                            servico_output[self.DIGITAL] = ""

                            try:
                                identifier = "#root > div:nth-child(2) > div:nth-child(4) > div:nth-child(2)"
                                header = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier)))

                                textos = header.find_elements(by=By.TAG_NAME, value="p")

                                servico = textos[0].get_attribute(TEXT_CONTENT)
                                servico_output[self.SERVICO] = servico
                                print("\t", servico)
                                orgao = textos[1].get_attribute(TEXT_CONTENT)
                                servico_output[self.ORGAO] = orgao
                            except Exception:
                                print(f"Erro no serviço ou orgao: categoria {categoria}, subcategoria {sub_categoria}, item {k}")
                            try:
                                identifier = "#root > div:nth-child(2) > div:nth-child(4) > div:nth-child(3) > div > div:nth-child(1) > div:nth-child(2) > div > div > div > div > p"
                                descricao = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier).get_attribute(TEXT_CONTENT)

                                servico_output[self.DESCRICAO] = descricao
                            except Exception:
                                print(f"Erro na descrição: categoria {categoria}, subcategoria {sub_categoria}, item {k}")

                            output.append(servico_output)

                            df = pd.DataFrame(output)
                            salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())

                            k += 1
                            if k >= len(servicos_da_pagina):
                                ultimo_servico = True

                            self.driver.back()
                            # print("Voltou para serviços")

                    self.driver.back()
                    time.sleep(WAIT_TIME)
                    # print("Voltou para sub-categorias")

                self.driver.back()
                time.sleep(WAIT_TIME)
                # print("Voltou para categorias")

        return pd.DataFrame(output)


class DF(RPA):
    def __init__(self) -> None:
        super().__init__()

    def obter_uf(self) -> str:
        return "DF"

    def obter_url_e_nome(self, element, class_value):
        url = element.get_attribute(H_REF)
        nome = element.find_element(by=By.CLASS_NAME, value=class_value).get_attribute(TEXT_CONTENT)
        return url, nome

    def extrair_servicos(self) -> pd.DataFrame:

        url = "https://servicos.df.gov.br/"
        self.driver.get(url)

        elements = self.obter_lista_de_as("#categorias")
        categorias = []
        for element in elements:
            url, nome = self.obter_url_e_nome(element, "category__title")
            servico_output = {}
            servico_output[self.CATEGORIA] = nome
            servico_output[self.CATEGORIA + URL_SUFIX] = url
            categorias.append((servico_output))

        listas_servicos = []
        for categoria in categorias:
            self.driver.get(categoria[self.CATEGORIA + URL_SUFIX])

            elements = self.obter_lista_de_as("#personas > div:nth-child(2)")

            for element in elements:
                url, nome = self.obter_url_e_nome(element, "persona__title")
                servico_output = {}
                servico_output[self.CATEGORIA] = categoria[self.CATEGORIA]
                servico_output[self.SUBCATEGORIA] = nome
                servico_output[self.SUBCATEGORIA + URL_SUFIX] = url
                listas_servicos.append((servico_output))

        output = []
        for i in range(len(listas_servicos)):
            self.driver.get(listas_servicos[i][self.SUBCATEGORIA + URL_SUFIX])

            identifier = "#servicos"
            container = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier)))
            sub_categorias = container.find_elements(by=By.CLASS_NAME, value="service-list__categories")
            for sub_categoria in sub_categorias:
                item_clicavel = sub_categoria.find_element(by=By.CLASS_NAME, value="category__title")
                listas_servicos[i][self.SUBCATEGORIA] = item_clicavel.get_attribute(TEXT_CONTENT)

                self.clicar_em_elemento(item_clicavel, sleep=WAIT_TIME)
                ver_mais = sub_categoria.find_elements(by=By.CLASS_NAME, value="category__see-all")
                for v in ver_mais:
                    v.click()

                elements = sub_categoria.find_elements(by=By.TAG_NAME, value="a")

                for element in elements:
                    url = element.get_attribute(H_REF)

                    servico_output = {}
                    servico_output[self.ESTADO] = self.obter_uf()
                    servico_output[self.CATEGORIA] = listas_servicos[i][self.CATEGORIA]
                    servico_output[self.SUBCATEGORIA] = listas_servicos[i][self.SUBCATEGORIA]
                    servico_output[self.LINK] = url
                    output.append((servico_output))

        for i, row in enumerate(output):
            self.driver.get(row[self.LINK])

            try:
                identifier = "#app > div:nth-child(1) > main > div > div.row > div.col-lg-9.pl-lg-5 > h1"
                output[i][self.SERVICO] = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier))).get_attribute(TEXT_CONTENT)
            except Exception as e:
                print(f"Erro no servico: {output[i][self.LINK]}", e)
            try:
                identifier = "#app > div:nth-child(1) > main > div > div.row > div.col-lg-9.pl-lg-5"
                container = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier)
                sections = container.find_elements(by=By.CLASS_NAME, value="service__section")
                output[i][self.DESCRICAO] = self.montar_descricao_do_elemento(sections[0], "div")
            except Exception as e:
                print(f"Erro na descrição: {output[i][self.LINK]}", e)
            try:
                identifier = "#app > div:nth-child(1) > main > div > div.row > div.col-lg-3.row.justify-content-lg-start.justify-content-center.d-lg-none > div > div"
                container = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier)
                info_boxes = container.find_elements(by=By.CLASS_NAME, value="info-box__container")
                output[i][self.ORGAO] = info_boxes[-1].find_element(by=By.TAG_NAME, value="p").get_attribute(TEXT_CONTENT)
            except Exception as e:
                print(f"Erro no órgão: {output[i][self.LINK]}", e)
            try:
                identifier = "#app > div:nth-child(1) > main > div > div.row > div.col-lg-9.pl-lg-5 > div.service__badges"
                container = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier)
                badges = container.find_elements(by=By.TAG_NAME, value="span")
                output[i][self.DIGITAL] = "Não"
                for badge in badges:
                    if "Digital" in badge.get_attribute(TEXT_CONTENT):
                        output[i][self.DIGITAL] = "Sim"
                        break
            except Exception as e:
                print(f"Erro no digital: {output[i][self.LINK]}", e)

            df = pd.DataFrame(output)
            salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())

        return pd.DataFrame(output)


class RS(RPA):
    def __init__(self) -> None:
        super().__init__()

    def obter_uf(self) -> str:
        return "RS"

    def extrair_servicos(self) -> pd.DataFrame:

        url = "https://www.rs.gov.br/inicial"
        self.driver.get(url)

        identifier = "#bodyPrincipal > div:nth-child(16) > div > div > div > section > div.panel-body"
        elements = self.obter_lista_de_as(identifier)

        categorias = []
        for element in elements:
            categoria = element.find_element(by=By.TAG_NAME, value="div").get_attribute(TEXT_CONTENT)
            url = element.get_attribute(H_REF)
            servico_output = {}
            servico_output[self.CATEGORIA] = categoria
            servico_output[self.CATEGORIA + URL_SUFIX] = url
            categorias.append((servico_output))

        output = []
        for categoria in categorias:
            self.driver.get(categoria[self.CATEGORIA + URL_SUFIX])

            identifier = '//*[@id="component_result_search"]/p/a'
            mais_resultados = self.wait.until(EC.presence_of_element_located((By.XPATH, identifier)))
            while mais_resultados.get_attribute("style") == "":
                self.clicar_em_elemento(mais_resultados)
                time.sleep(WAIT_TIME)
                mais_resultados = self.driver.find_element(by=By.XPATH, value=identifier)

            identifier = "#component_result_search > div.resultado-busca"
            servicos = self.obter_lista_de_as(identifier)

            for servico in servicos:
                servico_output = {}
                servico_output[self.ESTADO] = self.obter_uf()
                servico_output[self.CATEGORIA] = categoria[self.CATEGORIA]
                servico_output[self.SUBCATEGORIA] = ""
                servico_output[self.DIGITAL] = ""
                servico_output[self.LINK] = servico.get_attribute(H_REF)
                output.append((servico_output))

        for i, row in enumerate(output):
            self.driver.get(row[self.LINK])
            time.sleep(WAIT_TIME)

            try:
                identifier = "#bodyPrincipal > div.wrapper__corpo > div > div:nth-child(1) > article > header > h1"
                output[i][self.SERVICO] = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier))).get_attribute(TEXT_CONTENT)
                # print("serviço: ", output[i][self.SERVICO])
            except Exception:
                print(f"Erro no servico: {output[i][self.LINK]}")
            try:
                identifier = "#bodyPrincipal > div.wrapper__corpo > div > div:nth-child(1) > article > div.bloco > div"
                container = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier)
                elements = container.find_elements(by=By.CSS_SELECTOR, value="*")
                descricao = ""
                headers = 0
                max_headers = 2
                for paragrafo in elements:
                    if paragrafo.tag_name == "p":
                        descricao += paragrafo.get_attribute(TEXT_CONTENT) + LINE_BREAK
                    elif paragrafo.tag_name == "h4":
                        headers += 1
                        if headers == max_headers:
                            break
                output[i][self.DESCRICAO] = descricao
                # print("descrição: ", output[i][self.DESCRICAO])
            except Exception:
                print(f"Erro na descrição: {output[i][self.LINK]}")
            try:
                identifier = "#bodyPrincipal > div.wrapper__corpo > div > div:nth-child(1) > article > header > h2 > a"
                output[i][self.ORGAO] = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier).get_attribute(TEXT_CONTENT)
                # print("Órgão: ", output[i][self.ORGAO])
            except Exception:
                print(f"Erro no órgão: {output[i][self.LINK]}")

            df = pd.DataFrame(output)
            salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())

        return pd.DataFrame(output)


class PR(RPA):
    def __init__(self) -> None:
        super().__init__()

    def obter_uf(self) -> str:
        return "PR"

    def extrair_servicos(self) -> pd.DataFrame:
        url = "https://pia.paas.pr.gov.br/guia"
        self.driver.get(url)

        # Remover Cookie
        identifier = "#cookie-msg > div > div > div:nth-child(2) > div > button"
        cookies = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier)))
        cookies.click()

        # Encontra categorias
        identifier = "#main-content > div > div > div > div > div:nth-child(4)"
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier)))
        start_categorias = self.obter_lista_de_as(identifier)

        output = []
        for i in range(len(start_categorias)):
            identifier = "#main-content > div > div > div > div > div:nth-child(4)"
            categorias = self.obter_lista_de_as(identifier)
            nome_categoria = categorias[i].get_attribute(TEXT_CONTENT)
            categorias[i].click()
            # self.clicar_em_elemento(categorias[i])

            # Abre Sub Categorias
            identifier = "#servico-selecionado > div > ul > li > ul"
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier)))
            time.sleep(WAIT_TIME)
            start_sub_categorias = self.obter_lista_de_as(identifier)
            for j in range(len(start_sub_categorias)):
                start_sub_categorias[j].click()

            # Encontra Sub Categorias
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier)))
            container = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier)
            sub_categorias = container.find_elements(by=By.XPATH, value='//*[@id="servico-selecionado"]/div/ul/li/ul/li')
            for sub_categoria in sub_categorias:
                nome_sub_categoria = sub_categoria.find_element(by=By.TAG_NAME, value="a").get_attribute(TEXT_CONTENT)
                container = sub_categoria.find_element(by=By.TAG_NAME, value="ul")
                servicos = container.find_elements(by=By.TAG_NAME, value="a")
                # Encontrar servicos
                for servico in servicos:
                    servico_output = {}
                    servico_output[self.ESTADO] = self.obter_uf()
                    servico_output[self.CATEGORIA] = nome_categoria
                    servico_output[self.SUBCATEGORIA] = nome_sub_categoria
                    servico_output[self.DIGITAL] = ""
                    servico_output[self.LINK] = servico.get_attribute(H_REF)
                    output.append((servico_output))

        # Detalhes de servicos
        for i, row in enumerate(output):
            self.driver.get(row[self.LINK])

            try:
                identifier = "#servico-detail > div > div > div > div:nth-child(2) > div > h1"
                output[i][self.SERVICO] = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier))).get_attribute(TEXT_CONTENT)
            except Exception:
                print(f"Erro no servico: {output[i][self.LINK]}")
            try:
                identifier = "#servico-detail > div > div > div > div:nth-child(4) > div:nth-child(2) > div:nth-child(1) > div > p"
                output[i][self.DESCRICAO] = self.montar_descricao_de_todos_os_filhos(identifier)
            except Exception as e:
                print(f"Erro na descrição: {output[i][self.LINK]}", e)
            try:
                identifier = "#servico-detail > div > div > div > div:nth-child(4) > div.col-sm-12.col-xl-4 > div:nth-child(1) > div > div:nth-child(3) > div.orgao-responsavel"
                container = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier)
                elements = container.find_elements(by=By.TAG_NAME, value="strong")
                orgao = ""
                for element in elements:
                    orgao += element.get_attribute(TEXT_CONTENT) + LINE_BREAK
                output[i][self.ORGAO] = orgao
            except Exception:
                print(f"Erro no órgão: {output[i][self.LINK]}")

            df = pd.DataFrame(output)
            salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())

        return pd.DataFrame(output)


class MG(RPA):
    def __init__(self) -> None:
        super().__init__()

    def obter_uf(self) -> str:
        return "MG"

    def extrair_servicos(self) -> pd.DataFrame:
        urls = ["https://www.mg.gov.br/cidadao", "https://www.mg.gov.br/empresa", "https://www.mg.gov.br/municipio"]

        # self.driver.get(urls[0])

        # identifier = "#popup-buttons > button"
        # cookies = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier)))
        # cookies.click()

        output_urls = []
        for url in urls:
            self.driver.get(url)
            time.sleep(WAIT_TIME)

            identifier = '//*[@id="block-govmg-barrio-sass-content"]/div/div/div/div[2]/div/div'
            start_categorias = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, identifier)))

            output = []
            # Acessar categorias
            for i in range(len(start_categorias)):
                categorias = self.driver.find_elements(by=By.XPATH, value=identifier)
                self.clicar_em_elemento(categorias[i], WAIT_TIME)

                nome_categoria = categorias[i].find_element(by=By.CSS_SELECTOR, value="div:nth-child(1) > div").get_attribute(TEXT_CONTENT)
                container = self.wait.until(EC.presence_of_element_located((By.XPATH, identifier + f"[{i+1}]/div[2]/div/span/div[2]/div/div")))

                # Servicos sem sub categoria
                element = container.find_elements(by=By.CSS_SELECTOR, value="div.attachment.attachment-before")
                if len(element):
                    servicos = element[0].find_elements(by=By.TAG_NAME, value="a")
                    nome_sub_categoria = ""
                    for servico in servicos:
                        servico_output = {}
                        servico_output[self.ESTADO] = self.obter_uf()
                        servico_output[self.CATEGORIA] = nome_categoria
                        servico_output[self.SUBCATEGORIA] = nome_sub_categoria
                        servico_output[self.DIGITAL] = ""
                        servico_output[self.LINK] = servico.get_attribute(H_REF)
                        output.append((servico_output))

                # Servicos com Sub Categoria
                element = container.find_elements(by=By.CSS_SELECTOR, value="div.view-content.ui-accordion.ui-widget.ui-helper-reset")
                if len(element):
                    elements = element[0].find_elements(by=By.CSS_SELECTOR, value="*")
                    nome_sub_categoria = ""
                    for element in elements:
                        if element.tag_name == "h3":
                            nome_sub_categoria = element.find_element(by=By.TAG_NAME, value="span").get_attribute(TEXT_CONTENT)
                        elif element.tag_name == "div":
                            servicos = element.find_elements(by=By.TAG_NAME, value="a")

                            for servico in servicos:
                                servico_output = {}
                                servico_output[self.ESTADO] = self.obter_uf()
                                servico_output[self.CATEGORIA] = nome_categoria
                                servico_output[self.SUBCATEGORIA] = nome_sub_categoria
                                servico_output[self.DIGITAL] = ""
                                servico_output[self.LINK] = servico.get_attribute(H_REF)
                                output.append((servico_output))

            # Detalhes dos serviços
            for i, row in enumerate(output):
                self.driver.get(row[self.LINK])

                try:
                    identifier = "#block-govmg-barrio-sass-page-title > div > h1 > span"
                    output[i][self.SERVICO] = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier))).get_attribute(TEXT_CONTENT)
                except Exception:
                    print(f"Erro no servico: {output[i][self.LINK]}")
                try:
                    identifier = "#ui-id-3 > div.clearfix.text-formatted.field.field--name-field-descricao.field--type-text-long.field--label-hidden.field__item"
                    # output[i][self.DESCRICAO] = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier).get_attribute(TEXT_CONTENT)
                    output[i][self.DESCRICAO] = self.montar_descricao_de_todos_os_filhos(identifier)
                except Exception:
                    print(f"Erro na descrição: {output[i][self.LINK]}")
                try:
                    identifier = "#ui-id-3 > div.field.field--name-field-filiacao.field--type-entity-reference.field--label-above > div.field__item > a"
                    output[i][self.ORGAO] = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier).get_attribute(TEXT_CONTENT)
                except Exception:
                    print(f"Erro no órgão: {output[i][self.LINK]}")

                df = pd.DataFrame(output_urls + output)
                salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())

            output_urls = output_urls + output
        return pd.DataFrame(output_urls)


class MT(RPA):
    URL_PREFIX = "https://portal.mt.gov.br/app/catalog/"

    def __init__(self) -> None:
        super().__init__()

    def obter_uf(self) -> str:
        return "MT"

    def selecionar_categorias(self):
        # Localize o elemento select usando o xpath fornecido
        select_identifier = "//*[@id='root']/div[1]/div[2]/div/div[1]/div[1]/div/div[2]/select"
        select_element = self.wait.until(EC.presence_of_element_located((By.XPATH, select_identifier)))

        # Crie um objeto Select a partir do elemento encontrado
        select = Select(select_element)

        # Lista para armazenar os textos das opções
        option_texts = []
        # Percorra todas as opções e obtenha o texto, pulando opções sem valor
        for option in select.options:
            # Verifica se a opção tem um valor associado
            if option.get_attribute("value"):

                # Armazene o texto da opção
                option_texts.append((option.text, option.get_attribute("value")))
        return select, option_texts

    def listar_servicos_da_pagina(self, option_text, option_value, output):
        # Aguarde o carregamento da página e encontre os elementos
        container_identifier = "//*[@id='root']/div[1]/div[2]/div/div[2]/div[2]/div"
        services_elements = self.driver.find_elements(by=By.XPATH, value=container_identifier)
        # Itere sobre os elementos h5 e processe o texto
        for s in range(len(services_elements)):
            title_identifier = f"//*[@id='root']/div[1]/div[2]/div/div[2]/div[2]/div[{s+1}]/button/div/h5"
            text = self.wait.until(EC.presence_of_element_located((By.XPATH, title_identifier))).text
            text = self.converter_texto_para_link(text)

            servico_output = {}
            servico_output[self.ESTADO] = self.obter_uf()
            servico_output[self.CATEGORIA] = option_text
            servico_output[self.SUBCATEGORIA] = ""
            servico_output[self.LINK] = self.URL_PREFIX + f"{option_value}/{text}"
            try:
                digital_identifier = f"//*[@id='root']/div[1]/div[2]/div/div[2]/div[2]/div[{s+1}]/button/div/div[3]/p/span/span"
                servico_output[self.DIGITAL] = self.wait.until(EC.presence_of_element_located((By.XPATH, digital_identifier))).text
            except Exception as e:
                print(f"Erro no digital: {servico_output[self.LINK]}", e)
            output.append((servico_output))
        return output

    def extrair_servicos(self) -> pd.DataFrame:
        BASE_URL = "https://portal.mt.gov.br/app/catalog/list/"
        url = BASE_URL + "administracao-publica/"

        self.driver.get(url)

        _, option_texts = self.selecionar_categorias()

        output = []
        for option_text, option_value in option_texts:
            self.driver.get(BASE_URL + option_value)

            while True:
                output = self.listar_servicos_da_pagina(option_text, option_value, output)

                next_identifier = "//*[@id='root']/div[1]/div[2]/div/div[2]/ul/li"
                next_button = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, next_identifier)))[-1]
                if next_button.get_attribute("aria-disabled") == "true":
                    break
                next_button.find_element(by=By.TAG_NAME, value="button").click()
                time.sleep(WAIT_TIME)

        # Detalhes dos serviços
        for i, row in enumerate(output):
            self.driver.get(row[self.LINK])

            identifier = "//*[@id='root']/div/div[1]/div[2]/div[1]/div/div/div[1]/div/div[1]/h4"
            text = self.wait.until(EC.presence_of_element_located((By.XPATH, identifier))).get_attribute(TEXT_CONTENT)
            if text == "":
                self.driver.get(row[self.LINK][:-1])  # Remove ponto do final

            text = self.wait.until(EC.presence_of_element_located((By.XPATH, identifier))).get_attribute(TEXT_CONTENT)
            if text == "":
                self.driver.get(row[self.LINK].replace("(", "").replace(")", ""))  # Remove parênteses

            try:
                identifier = "//*[@id='root']/div/div[1]/div[2]/div[1]/div/div/div[1]/div/div[1]/h4"
                output[i][self.SERVICO] = self.wait.until(EC.presence_of_element_located((By.XPATH, identifier))).get_attribute(TEXT_CONTENT)
            except Exception as e:
                print(f"Erro no servico: {output[i][self.LINK]}", e)
            try:
                identifier = "//*[@id='root']/div/div[1]/div[2]/div[2]/div[1]/div[1]/p"
                output[i][self.DESCRICAO] = self.driver.find_element(by=By.XPATH, value=identifier).get_attribute(TEXT_CONTENT)
            except Exception as e:
                print(f"Erro na descrição: {output[i][self.LINK]}", e)
            try:
                identifier = "//*[@id='root']/div/div[1]/div[2]/div[2]/div[2]/div"
                container = self.driver.find_elements(by=By.XPATH, value=identifier)[-1]
                paragraphs = container.find_elements(by=By.TAG_NAME, value="p")[1:]
                orgaos = ""
                for paragraph in paragraphs:
                    orgaos += paragraph.get_attribute(TEXT_CONTENT)
                output[i][self.ORGAO] = orgaos
            except Exception as e:
                print(f"Erro no órgão: {output[i][self.LINK]}", e)

            df = pd.DataFrame(output)
            salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())

        return pd.DataFrame(output)


class AC(RPA):
    def __init__(self) -> None:
        super().__init__()

    def obter_uf(self) -> str:
        return "AC"

    def obter_url_e_nome(self, element, tag_value):
        url = element.get_attribute(H_REF)
        nome = element.find_element(by=By.TAG_NAME, value=tag_value).get_attribute(TEXT_CONTENT)
        return url, nome

    def extrair_servicos(self) -> pd.DataFrame:
        url = "https://www.ac.gov.br/categorias"
        self.driver.get(url)

        identifier = "body > div.container.principal > div.container.mb-5 > div:nth-child(3)"
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier)))

        # Lista categorias
        elements = self.obter_lista_de_as(identifier)
        categorias = []
        for element in elements:
            url, nome = self.obter_url_e_nome(element, "span")
            servico_output = {}
            servico_output[self.CATEGORIA] = nome
            servico_output[self.CATEGORIA + URL_SUFIX] = url
            categorias.append((servico_output))

        output = []
        for categoria in categorias:
            self.driver.get(categoria[self.CATEGORIA + URL_SUFIX])
            # print(categoria[self.CATEGORIA])

            # Filtra serviços estaduais
            identifier = "/html/body/div[5]/div[2]/div[3]/div[2]/div[2]/div"
            self.wait.until(EC.presence_of_element_located((By.XPATH, identifier))).click()

            while True:
                # Espera carregar
                try:
                    identifier = "body > div.container.principal > div.container.mb-5 > div.row.lista_servicos > div:nth-child(1) > a > div.card-footer.d-flex.flex-row"
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier)))
                except Exception:  # Não há serviços estaduais
                    break

                # Lista de serviços
                identifier = "body > div.container.principal > div.container.mb-5 > div.row.lista_servicos"
                servicos = self.obter_lista_de_as(identifier)
                for servico in servicos:
                    servico_output = {}
                    servico_output[self.ESTADO] = self.obter_uf()
                    servico_output[self.CATEGORIA] = categoria[self.CATEGORIA]
                    servico_output[self.SUBCATEGORIA] = ""
                    servico_output[self.LINK] = servico.get_attribute(H_REF)

                    servico_output[self.SERVICO] = servico.find_element(by=By.TAG_NAME, value="h5").get_attribute(TEXT_CONTENT)
                    servico_output[self.DESCRICAO] = servico.find_element(by=By.TAG_NAME, value="p").get_attribute(TEXT_CONTENT)

                    tags = servico.find_elements(by=By.TAG_NAME, value="button")
                    presencial = False
                    digital = False
                    orgaos = []
                    for tag in tags:
                        text = tag.get_attribute(TEXT_CONTENT)
                        if text == "Presencial":
                            presencial = True
                        elif text == "Digital":
                            digital = True
                        elif text not in ["Agendável", "Externo"]:
                            orgaos.append(text)

                    if presencial & digital:
                        servico_output[self.DIGITAL] = "Ambos"
                    elif presencial:
                        servico_output[self.DIGITAL] = "Presencial"
                    elif digital:
                        servico_output[self.DIGITAL] = "Digital"
                    servico_output[self.ORGAO] = "\n".join(orgaos)

                    # print(servico_output[self.SERVICO])
                    output.append(servico_output)
                    df = pd.DataFrame(output)
                    salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())

                # Vai para a próxima página
                identifier = "/html/body/div[5]/div[2]/div[5]/div/div"
                paginacao = self.driver.find_element(by=By.XPATH, value=identifier)
                proxima_pagina = paginacao.find_elements(by=By.XPATH, value="./*")[-1]
                if proxima_pagina.tag_name == "a":
                    self.clicar_em_elemento(proxima_pagina, 2 * WAIT_TIME)
                elif proxima_pagina.tag_name == "button":
                    break

        return pd.DataFrame(output)


class AL(RPA):
    def __init__(self) -> None:
        super().__init__()

    def obter_uf(self) -> str:
        return "AL"

    def extrair_servicos(self) -> pd.DataFrame:
        urls = [("https://alagoasdigital.al.gov.br/servicos-digitais", "Sim"), ("https://alagoasdigital.al.gov.br/guia-de-servicos", "Não")]

        output = []
        for url, digital in urls:
            self.driver.get(url)

            container_identifier = "#root > div.content-welcome > div.servicos > div"
            pagination_identifier = "#root > div.content-welcome > div.servicos > nav > ul > nav > ul"
            # Lista todos os serviços da página
            while True:
                container = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, container_identifier)))

                services = container.find_elements(by=By.CLASS_NAME, value="nome-servico")
                for service in services:
                    service_output = {}
                    service_output[self.ESTADO] = self.obter_uf()
                    service_output[self.CATEGORIA] = ""
                    service_output[self.SUBCATEGORIA] = ""
                    service_output[self.LINK] = service.find_element(by=By.TAG_NAME, value="a").get_attribute(H_REF)
                    service_output[self.DIGITAL] = digital
                    output.append(service_output)

                # Tenta clicar na próxima página
                pagination = self.driver.find_element(by=By.CSS_SELECTOR, value=pagination_identifier)
                next_page = pagination.find_elements(by=By.TAG_NAME, value="*")[-1]
                if next_page.tag_name == "a":
                    # next_page.click()
                    self.clicar_em_elemento(next_page, WAIT_TIME)
                elif next_page.tag_name == "span":
                    break

            # Acessa detalhes do serviço
            for i, row in enumerate(output):
                self.driver.get(row[self.LINK])

                try:
                    identifier = "#borda-texto > div > h1"
                    output[i][self.SERVICO] = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier))).get_attribute(TEXT_CONTENT)
                except Exception as e:
                    print(f"Erro no servico: {output[i][self.LINK]}", e)
                try:
                    identifier = "#borda-texto > div"
                    container = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier)
                    elements = container.find_elements(by=By.CSS_SELECTOR, value="*")
                    for element in elements:
                        if element.get_attribute("class") == "resp":
                            paragraphs = element.find_elements(by=By.TAG_NAME, value="p")
                            description = ""
                            for p in paragraphs:
                                description += p.get_attribute(TEXT_CONTENT) + LINE_BREAK
                            break
                    output[i][self.DESCRICAO] = description
                except Exception as e:
                    print(f"Erro na descrição: {output[i][self.LINK]}", e)
                try:
                    identifier = "#Servico_informacoes > div.div-content > strong"
                    output[i][self.ORGAO] = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier).get_attribute(TEXT_CONTENT)
                except Exception as e:
                    print(f"Erro no órgão: {output[i][self.LINK]}", e)

                df = pd.DataFrame(output)
                salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())
        return pd.DataFrame(output)


class BA(RPA):
    def __init__(self) -> None:
        super().__init__()

    def obter_uf(self) -> str:
        return "BA"

    def obter_url_e_nome(self, element):
        url = element.get_attribute(H_REF)
        nome = element.get_attribute(TEXT_CONTENT)
        return url, nome

    def extrair_servicos(self) -> pd.DataFrame:
        url = "http://servicos.ba.gov.br/mais/categorias"
        self.driver.get(url)

        identifier = "#body > main > div.container > div > div > div > ul"
        container = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier)))
        categories = container.find_elements(by=By.TAG_NAME, value="a")

        categories_output = []
        for category in categories:
            url, nome = self.obter_url_e_nome(category)

            service_output = {}
            service_output[self.CATEGORIA] = nome
            service_output[self.CATEGORIA + URL_SUFIX] = url
            categories_output.append(service_output)

        output = []
        for category in categories_output:
            self.driver.get(category[self.CATEGORIA + URL_SUFIX])

            identifier = "#servicos_encontrados > div > div > div"
            container = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier)))

            elements = container.find_elements(by=By.TAG_NAME, value="a")
            urls = []
            for element in elements:
                urls.append(element.get_attribute(H_REF))

            # Pula as urls de imagens e acessa os serviços
            for i in range(1, len(urls), 2):
                url = urls[i]
                self.driver.get(url)

                service_output = {}
                service_output[self.ESTADO] = self.obter_uf()
                service_output[self.CATEGORIA] = category[self.CATEGORIA]
                service_output[self.SUBCATEGORIA] = ""
                service_output[self.LINK] = url
                service_output[self.DIGITAL] = ""

                try:
                    identifier = "#secondary_nav > div > ul > div > div.col-md-8 > li:nth-child(1) > a"
                    service_output[self.SERVICO] = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, identifier))).get_attribute(TEXT_CONTENT)
                except Exception as e:
                    print(f"Erro no servico: {service_output[self.LINK]}", e)
                try:
                    identifier = "#section_1 > div:nth-child(1) > div:nth-child(2)"
                    container = self.driver.find_element(by=By.CSS_SELECTOR, value=identifier)
                    elements = container.find_elements(by=By.CSS_SELECTOR, value="*")
                    description = ""
                    header_descricao = False
                    header_orgao = False
                    text_descricao = False
                    text_orgao = False
                    for element in elements:
                        if element.get_attribute(TEXT_CONTENT) == "Descrição":
                            header_descricao = True
                        elif element.get_attribute(TEXT_CONTENT) == "Órgão responsável":
                            header_orgao = True

                        if header_descricao and element.tag_name == "li":
                            description += element.get_attribute(TEXT_CONTENT) + LINE_BREAK
                            text_descricao = True
                        elif header_orgao and element.tag_name == "p":
                            service_output[self.ORGAO] = element.get_attribute(TEXT_CONTENT)
                            text_orgao = True

                        if text_descricao and text_orgao:
                            break
                    service_output[self.DESCRICAO] = description
                except Exception as e:
                    print(f"Erro na descrição ou órgão: {service_output[self.LINK]}", e)

                output.append(service_output)
                df = pd.DataFrame(output)
                salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())
        return pd.DataFrame(output)


class MS(RPA):
    def __init__(self) -> None:
        super().__init__()

    def obter_uf(self) -> str:
        return "MS"

    def extrair_servicos(self) -> pd.DataFrame:
        BASE_URL = "https://portal-unico.msdigital.ms.gov.br/categoria/"
        url = "https://portal-unico.msdigital.ms.gov.br/"
        self.driver.get(url)

        # Listar Categorias
        identifier = "//*[@id='categoria']/div/div[2]/div"
        container = self.wait.until(EC.presence_of_element_located((By.XPATH, identifier)))
        headers = container.find_elements(by=By.TAG_NAME, value="h3")
        categories = []
        for header in headers:
            category_output = {}
            text = header.get_attribute(TEXT_CONTENT)
            category_output[self.CATEGORIA] = text
            category_output[self.CATEGORIA + URL_SUFIX] = BASE_URL + self.converter_texto_para_link(text)
            categories.append(category_output)

        # Listar Serviços
        output = []
        for category in categories:
            self.driver.get(category[self.CATEGORIA + URL_SUFIX])
            identifier = "//*[@id='root']/div[3]/div[4]/div/div/a"
            services = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, identifier)))
            for service in services:
                service_output = {}
                service_output[self.ESTADO] = self.obter_uf()
                service_output[self.CATEGORIA] = category[self.CATEGORIA]
                service_output[self.SUBCATEGORIA] = ""
                service_output[self.LINK] = service.get_attribute(H_REF)
                service_output[self.DIGITAL] = ""
                output.append(service_output)

        # Acessa detalhes do serviço
        for i, row in enumerate(output):
            self.driver.get(row[self.LINK])
            # self.driver.refresh()
            try:
                identifier = "//*[@id='root']/div[3]/div[2]/div[1]/div/div[1]/h1"
                output[i][self.SERVICO] = self.wait.until(EC.presence_of_element_located((By.XPATH, identifier))).get_attribute(TEXT_CONTENT)
            except Exception as e:
                print(f"Erro no servico: {output[i][self.LINK]}", e)
            try:
                identifier = "//*[@id='oquee']/div[2]/p"
                description = self.montar_descricao_de_todos_os_filhos(identifier, by=By.XPATH)
                output[i][self.DESCRICAO] = description
            except Exception as e:
                print(f"Erro na descrição: {output[i][self.LINK]}", e)
            try:
                identifier = "//*[@id='root']/div[3]/div[2]/div[1]/div/div[1]/h3"
                output[i][self.ORGAO] = self.driver.find_element(by=By.XPATH, value=identifier).get_attribute(TEXT_CONTENT)
            except Exception as e:
                print(f"Erro no órgão: {output[i][self.LINK]}", e)

            df = pd.DataFrame(output)
            salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())
        return pd.DataFrame(output)


class AP(RPA):
    def __init__(self) -> None:
        super().__init__()

    def obter_uf(self) -> str:
        return "AP"

    def extrair_servicos(self) -> pd.DataFrame:
        BASE_URL = "https://servicos.portal.ap.gov.br/categorias/"
        url = "https://servicos.portal.ap.gov.br/"
        self.driver.get(url)

        identifier = "//*[@id='__next']/div/div[5]/section/div/div[2]/div/div/div"
        container = self.wait.until(EC.presence_of_element_located((By.XPATH, identifier)))

        headers = container.find_elements(by=By.TAG_NAME, value="h4")

        categories = []
        for header in headers:
            name = header.get_attribute(TEXT_CONTENT)
            categories.append(name)
        categories = list(set(categories))  # Remove duplicados

        output = []
        for category in categories:
            url = BASE_URL + self.converter_texto_para_link(category)
            self.driver.get(url)

            identifier = "//*[@id='__next']/div/div[3]/div/div[2]/div"
            start_services = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, identifier)))

            for i in range(len(start_services)):
                identifier = "//*[@id='__next']/div/div[3]/div/div[2]/div"
                services = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, identifier)))

                self.clicar_em_elemento(services[i], WAIT_TIME)
                time.sleep(WAIT_TIME)

                service_output = {}
                service_output[self.ESTADO] = self.obter_uf()
                service_output[self.CATEGORIA] = category
                service_output[self.SUBCATEGORIA] = ""
                service_output[self.LINK] = self.driver.current_url
                service_output[self.ORGAO] = ""

                try:
                    identifier = "//*[@id='__next']/div/div/div[3]/div/div/h1"
                    service_output[self.SERVICO] = self.wait.until(EC.presence_of_element_located((By.XPATH, identifier))).get_attribute(TEXT_CONTENT)
                except Exception as e:
                    print(f"Erro no servico: {service_output[self.LINK]}", e)
                try:
                    identifier = "//*[@id='__next']/div/div/div[4]/section/section[1]/div"
                    description = self.montar_descricao_de_todos_os_filhos(identifier, by=By.XPATH)
                    service_output[self.DESCRICAO] = description
                except Exception as e:
                    print(f"Erro na descrição: {service_output[self.LINK]}", e)
                try:
                    identifier = "//*[@id='__next']/div/div/div[3]/div/strong"
                    tags = self.driver.find_elements(by=By.XPATH, value=identifier)
                    digital = ""
                    for tag in tags:
                        digital += tag.get_attribute(TEXT_CONTENT) + LINE_BREAK
                    service_output[self.DIGITAL] = digital
                except Exception as e:
                    print(f"Erro no digital: {service_output[self.LINK]}", e)

                output.append(service_output)
                df = pd.DataFrame(output)
                salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())

                self.driver.back()

        return pd.DataFrame(output)


class MA(RPA):
    def __init__(self) -> None:
        super().__init__()

    def obter_uf(self) -> str:
        return "MA"

    def obter_url_e_nome(self, element):
        url = element.get_attribute(H_REF)
        nome = element.get_attribute(TEXT_CONTENT)
        return url, nome

    def extrair_servicos(self) -> pd.DataFrame:
        url = "https://www.ma.gov.br/servicos/"
        self.driver.get(url)

        identifier = "/html/body/main/section[1]/div/ul"
        container = self.wait.until(EC.presence_of_element_located((By.XPATH, identifier)))
        categories = container.find_elements(by=By.TAG_NAME, value="a")

        categories_output = []
        for category in categories:
            url, nome = self.obter_url_e_nome(category)

            service_output = {}
            service_output[self.CATEGORIA] = nome
            service_output[self.CATEGORIA + URL_SUFIX] = url
            categories_output.append(service_output)

        output = []
        for category in categories_output:
            self.driver.get(category[self.CATEGORIA + URL_SUFIX])

            urls = []
            while True:
                identifier = "/html/body/main/ul[2]"
                container = self.wait.until(EC.presence_of_element_located((By.XPATH, identifier)))

                elements = container.find_elements(by=By.TAG_NAME, value="a")

                for element in elements:
                    urls.append(element.get_attribute(H_REF))

                # # Aceiter cookies
                # accept_identifier = "/html/body/div[4]/div/div[2]/a[1]"
                # self.driver.find_element(by=By.XPATH, value=accept_identifier).click()

                identifier = "/html/body/main/nav/ul"
                container = self.wait.until(EC.presence_of_element_located((By.XPATH, identifier)))

                elements = container.find_elements(by=By.TAG_NAME, value="a")
                next_clicked = False
                for element in elements:
                    if element.get_attribute("title") == "página seguinte":
                        next_clicked = True
                        self.driver.get(element.get_attribute(H_REF))
                if not next_clicked:
                    break

            for url in urls:
                service_output = {}
                service_output[self.ESTADO] = self.obter_uf()
                service_output[self.CATEGORIA] = category[self.CATEGORIA]
                service_output[self.SUBCATEGORIA] = ""
                service_output[self.LINK] = url
                service_output[self.DIGITAL] = ""
                service_output[self.ORGAO] = ""

                try:
                    self.driver.get(url)
                except Exception:
                    print("Não conseguiu conectar", url)
                    output.append(service_output)
                    df = pd.DataFrame(output)
                    salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())
                    continue
                try:
                    identifier = "//*[@id='main']/header/h1"
                    service_output[self.SERVICO] = self.wait.until(EC.presence_of_element_located((By.XPATH, identifier))).get_attribute(TEXT_CONTENT)
                except Exception as e:
                    print(f"Erro no servico: {service_output[self.LINK]}", e)
                try:
                    identifier = "//*[@id='main']/section/details[1]/div"
                    description = self.montar_descricao_de_todos_os_filhos(identifier, by=By.XPATH)
                    service_output[self.DESCRICAO] = description
                except Exception as e:
                    print(f"Erro na descrição: {service_output[self.LINK]}", e)
                try:
                    identifier = "/html/body/div[2]/div/h1"
                    service_output[self.ORGAO] = self.driver.find_element(by=By.XPATH, value=identifier).get_attribute(TEXT_CONTENT)
                except Exception as e:
                    print(f"Erro no órgão: {service_output[self.LINK]}", e)

                output.append(service_output)
                df = pd.DataFrame(output)
                salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())
        return pd.DataFrame(output)


class RO(RPA):
    def __init__(self) -> None:
        super().__init__()

    def obter_uf(self) -> str:
        return "RO"

    def extrair_servicos(self) -> pd.DataFrame:
        url = "https://portaldocidadao.ro.gov.br/Servico/Todos"
        self.driver.get(url)
        urls = []
        # Lista serviços de todas as páginas
        while True:
            # elements = self.obter_lista_de_as("#listaServicos")
            identifier = "#carregandoServicos"
            while self.driver.find_element(by=By.CSS_SELECTOR, value=identifier).get_attribute(TEXT_CONTENT) == "":
                time.sleep(WAIT_TIME)
            identifier = "#listaServicos a"
            elements = self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, identifier)))
            for element in elements:
                urls.append(element.get_attribute(H_REF))

            pagination = self.driver.find_element(by=By.CSS_SELECTOR, value="#paginacao")
            next_page = pagination.find_elements(by=By.TAG_NAME, value="li")
            if next_page[-2].get_attribute("style") == "":
                for i in range(len(next_page)):
                    if next_page[i].get_attribute("class") == "active page-item":
                        self.clicar_em_elemento(next_page[i + 1], WAIT_TIME)
                        break
                time.sleep(WAIT_TIME)
            else:
                break

        # Acessa detalhes do Serviço
        output = []
        for url in urls:
            self.driver.get(url)

            service_output = {}
            service_output[self.ESTADO] = self.obter_uf()
            service_output[self.SUBCATEGORIA] = ""
            service_output[self.LINK] = url

            try:
                identifier = "/html/body/div[2]/div[2]/div[4]/div/h4/strong"
                service_output[self.CATEGORIA] = self.wait.until(EC.presence_of_element_located((By.XPATH, identifier))).get_attribute(TEXT_CONTENT)
            except Exception as e:
                print(f"Erro na categoria: {service_output[self.LINK]}", e)
            try:
                identifier = "/html/body/div[2]/div[2]/div[8]/div[2]/div/div"
                container = self.driver.find_element(by=By.XPATH, value=identifier)
                tags = container.find_elements(by=By.TAG_NAME, value="span")
                digital = ""
                for tag in tags:
                    digital += tag.get_attribute(TEXT_CONTENT) + LINE_BREAK
                service_output[self.DIGITAL] = digital
            except Exception as e:
                print(f"Erro na categoria: {service_output[self.LINK]}", e)
            try:
                identifier = "/html/body/div[2]/div[2]/div[5]/div/div/div[1]/h3"
                service_output[self.SERVICO] = self.driver.find_element(by=By.XPATH, value=identifier).get_attribute(TEXT_CONTENT)
            except Exception as e:
                print(f"Erro no servico: {service_output[self.LINK]}", e)
            try:
                identifier = "/html/body/div[2]/div[2]/div[7]/div[2]/div/p[1]"
                service_output[self.DESCRICAO] = self.driver.find_element(by=By.XPATH, value=identifier).get_attribute(TEXT_CONTENT)
            except Exception as e:
                print(f"Erro na descrição: {service_output[self.LINK]}", e)
            try:
                identifier = "/html/body/div[2]/div[2]/div[5]/div/div/div[1]/small"
                service_output[self.ORGAO] = self.driver.find_element(by=By.XPATH, value=identifier).get_attribute(TEXT_CONTENT)
            except Exception as e:
                print(f"Erro no órgão: {service_output[self.LINK]}", e)

            output.append(service_output)
            df = pd.DataFrame(output)
            salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())
        return pd.DataFrame(output)


class SE(RPA):
    def __init__(self) -> None:
        super().__init__()

    def obter_uf(self) -> str:
        return "SE"

    def extrair_servicos(self) -> pd.DataFrame:
        url = "https://www.ceac.se.gov.br/category/status/servicos-online/"
        self.driver.get(url)

        identifier = '//*[@id="main"]/div/div/section[2]/div/div/div[1]/div/div/div[2]/div/div'
        container = self.wait.until(EC.presence_of_element_located((By.XPATH, identifier)))
        elements = container.find_elements(by=By.TAG_NAME, value="a")
        # Pula as urls repetidas e acessa os serviços
        urls = []
        for i in range(0, len(elements), 2):
            urls.append(elements[i].get_attribute(H_REF))

        # Acessa detalhes do Serviço
        output = []
        for url in urls:
            self.driver.get(url)

            service_output = {}
            service_output[self.ESTADO] = self.obter_uf()
            service_output[self.CATEGORIA] = ""
            service_output[self.SUBCATEGORIA] = ""
            service_output[self.LINK] = url
            service_output[self.DIGITAL] = "Sim"

            try:
                identifier = "//*[@id='content']/div/div/section[2]/div/div/div/div/div/div[1]/div/h1"
                service_output[self.SERVICO] = self.wait.until(EC.presence_of_element_located((By.XPATH, identifier))).get_attribute(TEXT_CONTENT)
            except Exception as e:
                print(f"Erro no servico: {service_output[self.LINK]}", e)
            try:
                identifier = "#content > div > div > section.elementor-section.elementor-top-section.elementor-element.elementor-element-1e8d63e.elementor-section-full_width.elementor-section-height-default.elementor-section-height-default > div > div > div > div > div > div.elementor-element.elementor-element-b67e352.elementor-widget.elementor-widget-theme-post-content > div"
                description = self.montar_descricao_de_todos_os_filhos(identifier)
                service_output[self.DESCRICAO] = description
            except Exception as e:
                print(f"Erro na descrição: {service_output[self.LINK]}", e)
            try:
                identifier = "//*[@id='content']/div/div/section[2]/div/div/div/div/div/div[7]/div/ul/li/span[2]/span/a[1]"
                service_output[self.ORGAO] = self.driver.find_element(by=By.XPATH, value=identifier).get_attribute(TEXT_CONTENT)
            except Exception as e:
                print(f"Erro no órgão: {service_output[self.LINK]}", e)

            output.append(service_output)
            df = pd.DataFrame(output)
            salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())
        return pd.DataFrame(output)


class TO(RPA):
    def __init__(self) -> None:
        super().__init__()

    def obter_uf(self) -> str:
        return "TO"

    def extrair_servicos(self) -> pd.DataFrame:
        url = "https://servicos.to.gov.br/listar_servico.aspx"
        self.driver.get(url)

        urls = []

        identifier = "//*[@id='ctl00_ContentPlaceHolder1_servicosContainer']/div"
        pages = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, identifier)))
        for page in pages:
            services = page.find_elements(by=By.CSS_SELECTOR, value="div.card-servico-top")
            for service in services:
                urls.append(service.find_element(by=By.TAG_NAME, value="a").get_attribute(H_REF))

        # Acessa detalhes do Serviço
        output = []
        for url in urls:
            self.driver.get(url)

            service_output = {}
            service_output[self.ESTADO] = self.obter_uf()
            service_output[self.SUBCATEGORIA] = ""
            service_output[self.LINK] = url

            try:
                identifier = "//*[@id='ctl00_ContentPlaceHolder1_lblTxtServico']"
                service_output[self.SERVICO] = self.wait.until(EC.presence_of_element_located((By.XPATH, identifier))).get_attribute(TEXT_CONTENT)
            except Exception as e:
                print(f"Erro no servico: {service_output[self.LINK]}", e)
            try:
                identifier = "//*[@id='ctl00_ContentPlaceHolder1_lblTxtConceituacao']"
                service_output[self.DESCRICAO] = self.montar_descricao_de_todos_os_filhos(identifier, by=By.XPATH)
            except Exception as e:
                print(f"Erro na descrição: {service_output[self.LINK]}", e)
            try:
                identifier = "//*[@id='ctl00_ContentPlaceHolder1_lblEmpresa']"
                service_output[self.ORGAO] = self.driver.find_element(by=By.XPATH, value=identifier).get_attribute(TEXT_CONTENT)
            except Exception as e:
                print(f"Erro no órgão: {service_output[self.LINK]}", e)
            try:
                identifier = "//*[@id='ctl00_ContentPlaceHolder1_lblTxtServicoGrupo']"
                service_output[self.CATEGORIA] = self.driver.find_element(by=By.XPATH, value=identifier).get_attribute(TEXT_CONTENT)
            except Exception as e:
                print(f"Erro na categoria: {service_output[self.LINK]}", e)
            try:
                identifier = "//*[@id='ctl00_ContentPlaceHolder1_pnFormasAtendimento']/span"
                tags = self.driver.find_elements(by=By.XPATH, value=identifier)
                digital = ""
                for tag in tags:
                    digital += tag.get_attribute(TEXT_CONTENT) + LINE_BREAK
                service_output[self.DIGITAL] = digital
            except Exception as e:
                print(f"Erro no digital: {service_output[self.LINK]}", e)

            output.append(service_output)
            df = pd.DataFrame(output)
            salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())
        return pd.DataFrame(output)


class PI(RPA):
    def __init__(self) -> None:
        super().__init__()

    def obter_uf(self) -> str:
        return "PI"

    def encontrar_lista_de_paginas(self):
        identifier = "//*[@id='root']/div[2]/div/div[1]/div[2]/div/div[2]/ul"
        container = self.wait.until(EC.presence_of_element_located((By.XPATH, identifier)))
        paginas = container.find_elements(by=By.TAG_NAME, value="li")
        return paginas

    def encontrar_lista_de_servicos(self):
        itens = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="root"]/div[2]/div/div[1]/div[2]/div/div[2]/div/div')))
        return itens

    def extrair_servicos(self) -> pd.DataFrame:
        url = "https://pidigital.pi.gov.br/app/catalog/list"
        self.driver.get(url)

        paginas = self.encontrar_lista_de_paginas()
        n_paginas = int(paginas[-2].get_attribute(TEXT_CONTENT))

        # Paginação
        output = []
        ultima_pagina = False
        p = 0
        while not ultima_pagina:
            print(f"{p+1}/{n_paginas} página\n==============")
            # Listar serviços
            ultimo_servico = False
            k = 0
            while not ultimo_servico:
                # Alcançar página
                for _ in range(p):

                    paginas = self.encontrar_lista_de_paginas()
                    proxima_pagina = paginas[-1]
                    self.clicar_em_elemento(proxima_pagina, WAIT_TIME)
                    time.sleep(WAIT_TIME)

                paginas = self.encontrar_lista_de_paginas()
                proxima_pagina = paginas[-1]
                attribute = "aria-disabled"
                if proxima_pagina.get_attribute(attribute) == "true":
                    ultima_pagina = True

                servicos_da_pagina = self.encontrar_lista_de_servicos()
                print(f"{k+1}/{len(servicos_da_pagina)} servico da página")

                self.clicar_em_elemento(servicos_da_pagina[k], WAIT_TIME)
                time.sleep(WAIT_TIME)

                # Detalhes dos serviços
                servico_output = {}
                servico_output[self.LINK] = self.driver.current_url
                servico_output[self.ESTADO] = self.obter_uf()
                servico_output[self.DIGITAL] = "Sim"

                try:
                    identifier = "//*[@id='root']/div[2]/div/div[1]/div[2]/div[1]/div/div/div[1]/p"
                    servico = self.wait.until(EC.presence_of_element_located((By.XPATH, identifier)))

                    servico_output[self.SERVICO] = servico.get_attribute(TEXT_CONTENT)
                except Exception:
                    print(f"Erro no serviço: página {p+1}, item {k+1}")
                try:
                    identifier = "//*[@id='root']/div[2]/div/div[1]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]"
                    subcategoria = self.driver.find_element(by=By.XPATH, value=identifier).get_attribute(TEXT_CONTENT)

                    servico_output[self.SUBCATEGORIA] = subcategoria
                except Exception:
                    print(f"Erro na subcategoria: página {p+1}, item {k+1}")
                try:
                    identifier = "//*[@id='root']/div[2]/div/div[1]/div[2]/div[2]/div[2]/div[2]/div/p"
                    orgao = self.driver.find_element(by=By.XPATH, value=identifier).get_attribute("innerText")

                    servico_output[self.ORGAO] = orgao
                except Exception:
                    print(f"Erro no órgão: página {p+1}, item {k+1}")
                try:
                    identifier = "//*[@id='root']/div[2]/div/div[1]/div[2]/div[2]/div[2]/div[4]/div"
                    categoria = self.driver.find_element(by=By.XPATH, value=identifier).get_attribute("innerText")

                    servico_output[self.CATEGORIA] = categoria
                except Exception:
                    print(f"Erro na categoria: página {p+1}, item {k+1}")
                try:
                    identifier = "//*[@id='root']/div[2]/div/div[1]/div[2]/div[2]/div[1]/div[1]/p[2]"
                    descricao = self.driver.find_element(by=By.XPATH, value=identifier).get_attribute(TEXT_CONTENT)

                    servico_output[self.DESCRICAO] = descricao
                except Exception:
                    print(f"Erro na descrição: página {p+1}, item {k+1}")

                output.append(servico_output)

                df = pd.DataFrame(output)
                salvar_dataframe(df, BRONZE_FOLDER, self.obter_uf())

                k += 1
                if k >= len(servicos_da_pagina):
                    ultimo_servico = True

                self.driver.back()
                time.sleep(WAIT_TIME)

            p += 1
        return pd.DataFrame(output)


if __name__ == "__main__":

    # uf = CE()
    # output = uf.extrair_servicos()
    # df = pd.DataFrame(output)
    # salvar_dataframe(df, BRONZE_FOLDER, uf.obter_uf())

    # uf = SC()
    # output = uf.extrair_servicos()
    # df = pd.DataFrame(output)
    # salvar_dataframe(df, BRONZE_FOLDER, uf.obter_uf())

    # uf = GO()
    # output = uf.extrair_servicos()
    # df = pd.DataFrame(output)
    # salvar_dataframe(df, BRONZE_FOLDER, uf.obter_uf())

    # uf = RJ()
    # output = uf.extrair_servicos()
    # df = pd.DataFrame(output)
    # salvar_dataframe(df, BRONZE_FOLDER, uf.obter_uf())

    # uf = DF()
    # output = uf.extrair_servicos()
    # df = pd.DataFrame(output)
    # salvar_dataframe(df, BRONZE_FOLDER, uf.obter_uf())

    # uf = RS()
    # output = uf.extrair_servicos()
    # df = pd.DataFrame(output)
    # salvar_dataframe(df, BRONZE_FOLDER, uf.obter_uf())

    # uf = PR()
    # output = uf.extrair_servicos()
    # df = pd.DataFrame(output)
    # salvar_dataframe(df, BRONZE_FOLDER, uf.obter_uf())

    # uf = MG()
    # output = uf.extrair_servicos()
    # df = pd.DataFrame(output)
    # salvar_dataframe(df, BRONZE_FOLDER, uf.obter_uf())

    # uf = MT()
    # output = uf.extrair_servicos()
    # df = pd.DataFrame(output)
    # salvar_dataframe(df, BRONZE_FOLDER, uf.obter_uf())

    # uf = AC()
    # output = uf.extrair_servicos()
    # df = pd.DataFrame(output)
    # salvar_dataframe(df, BRONZE_FOLDER, uf.obter_uf())

    # uf = AL()
    # output = uf.extrair_servicos()
    # df = pd.DataFrame(output)
    # salvar_dataframe(df, BRONZE_FOLDER, uf.obter_uf())

    # uf = BA()
    # output = uf.extrair_servicos()
    # df = pd.DataFrame(output)
    # salvar_dataframe(df, BRONZE_FOLDER, uf.obter_uf())

    # uf = MS()
    # output = uf.extrair_servicos()
    # df = pd.DataFrame(output)
    # salvar_dataframe(df, BRONZE_FOLDER, uf.obter_uf())

    # uf = RO()
    # output = uf.extrair_servicos()
    # df = pd.DataFrame(output)
    # salvar_dataframe(df, BRONZE_FOLDER, uf.obter_uf())

    # uf = SE()
    # output = uf.extrair_servicos()
    # df = pd.DataFrame(output)
    # salvar_dataframe(df, BRONZE_FOLDER, uf.obter_uf())

    # uf = TO()
    # output = uf.extrair_servicos()
    # df = pd.DataFrame(output)
    # salvar_dataframe(df, BRONZE_FOLDER, uf.obter_uf())

    # uf = AP()
    # output = uf.extrair_servicos()
    # df = pd.DataFrame(output)
    # salvar_dataframe(df, BRONZE_FOLDER, uf.obter_uf())

    # uf = MA()
    # output = uf.extrair_servicos()
    # df = pd.DataFrame(output)
    # salvar_dataframe(df, BRONZE_FOLDER, uf.obter_uf())

    uf = PI()
    output = uf.extrair_servicos()
    df = pd.DataFrame(output)
    salvar_dataframe(df, BRONZE_FOLDER, uf.obter_uf())
