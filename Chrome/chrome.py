import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Inicializar o WebDriver
driver = webdriver.Chrome()

# Navegar até uma página da web
driver.get("https://whats-app-394f8910c20c.herokuapp.com/")

# Localizar o botão pelo ID (ou outra estratégia de localização)
#botao = driver.find_element_by_id("id_do_botao")


# Localizar o botão pela classe usando By.CLASS_NAME
#botao = driver.find_element(By.CLASS_NAME, "col-md-12 mb-3")

botao = driver.find_element(By.PARTIAL_LINK_TEXT, "Login")



# Clicar no botão
botao.click()

# Localizar os campos de entrada para usuário e senha
campo_usuario = driver.find_element(By.ID, "id_username")
campo_senha = driver.find_element(By.ID, "id_password")

# Inserir as credenciais nos campos de entrada
usuario = "teste3"
senha = "Inte9545"
campo_usuario.send_keys(usuario)
campo_senha.send_keys(senha)

# Simular pressionamento da tecla "Enter" após inserir a senha
campo_senha.send_keys(Keys.ENTER)

botao2 = driver.find_element(By.PARTIAL_LINK_TEXT, "Ir para Lista de Produtos")

botao2.click()


# Aguardar por 10 segundos
time.sleep(10)

# Função para cadastrar um produto
def cadastrar_produto(driver, codigo, nome, descricao, categoria, preco_por_kilo, estoque_em_kilos):
    # Localizar os campos de entrada e preenchê-los
    driver.find_element_by_id("id_do_campo_codigo").send_keys(codigo)
    driver.find_element_by_id("id_do_campo_nome").send_keys(nome)
    driver.find_element_by_id("id_do_campo_descricao").send_keys(descricao)
    driver.find_element_by_id("id_do_campo_categoria").send_keys(categoria)
    driver.find_element_by_id("id_do_campo_preco_por_kilo").send_keys(preco_por_kilo)
    driver.find_element_by_id("id_do_campo_estoque_em_kilos").send_keys(estoque_em_kilos)
    
    # Submeter o formulário
    driver.find_element_by_id("id_do_botao_submit").click()

# Inicializar o WebDriver
driver = webdriver.Chrome()

# Navegar até a página de cadastro de produtos
driver.get("https://seusite.com/cadastrar_produto")

# Ler os dados do arquivo Excel
dados_produtos = pd.read_excel("dados_produtos.xlsx")

# Iterar sobre os dados e cadastrar os produtos
for indice, linha in dados_produtos.iterrows():
    cadastrar_produto(driver, linha['Codigo'], linha['Nome'], linha['Descricao'], linha['Categoria'], linha['Preco_por_kilo'], linha['Estoque_em_kilos'])
    
    # Aguardar um tempo para visualização (opcional)
    time.sleep(2)

# Fechar o navegador
driver.quit()


# Fechar o navegador
driver.quit()

