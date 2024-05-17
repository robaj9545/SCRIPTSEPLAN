import tkinter as tk
from tkinter import simpledialog

import pulp

def resolver_problema_transporte(num_fabricas, num_centros, custos, oferta, demanda_minima):
    # Nomes para fábricas e centros de distribuição
    fabricas = [f"Fabrica{i}" for i in range(1, num_fabricas + 1)]
    centros_distribuicao = [f"CD{i}" for i in range(1, num_centros + 1)]

    # Criação do problema de otimização
    problema = pulp.LpProblem("Problema de Transporte", pulp.LpMinimize)

    # Variáveis de decisão
    x = pulp.LpVariable.dicts("quantidade_enviada",
                               [(i, j) for i in fabricas for j in centros_distribuicao],
                               lowBound=0,
                               cat='Continuous')

    # Adição da função objetivo
    problema += sum(custos[i, j] * x[i, j] for i in fabricas for j in centros_distribuicao), "Custo Total de Transporte"

    # Restrições de oferta
    for i in fabricas:
        problema += sum(x[(i, j)] for j in centros_distribuicao) <= oferta[i], f"Oferta_{i}"

    # Restrições de demanda
    for j in centros_distribuicao:
        problema += sum(x[(i, j)] for i in fabricas) >= demanda_minima[j], f"Demand_Min_{j}"

    # Restrições de distribuição
    for i in fabricas:
        for j in centros_distribuicao:
            problema += x[(i, j)] >= 0, f"Restricao_Distribuicao_{i}_{j}"

    # Resolver o problema
    problema.solve()

    # Exibir os resultados
    resultado = "Status: " + pulp.LpStatus[problema.status] + "\n"
    resultado += "Custo Total de Transporte = " + str(pulp.value(problema.objective)) + "\n"
    for var in x.values():
        resultado += f"A quantidade enviada de {var.name} é {var.varValue}\n"
    
    return resultado

def obter_dados():
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal do Tkinter

    num_fabricas = simpledialog.askinteger("Número de Fábricas", "Digite o número de fábricas:")
    num_centros = simpledialog.askinteger("Número de Centros de Distribuição", "Digite o número de centros de distribuição:")

    custos = {}
    for i in range(1, num_fabricas + 1):
        for j in range(1, num_centros + 1):
            custo = simpledialog.askinteger("Custo de Transporte", f"Digite o custo de transporte da Fabrica{i} para CD{j}:")
            custos[f"Fabrica{i}", f"CD{j}"] = custo

    oferta = {}
    for i in range(1, num_fabricas + 1):
        oferta[f"Fabrica{i}"] = simpledialog.askinteger("Capacidade de Oferta", f"Digite a capacidade de oferta da Fabrica{i}:")

    demanda_minima = {}
    for j in range(1, num_centros + 1):
        demanda_minima[f"CD{j}"] = simpledialog.askinteger("Demanda Mínima", f"Digite a demanda mínima do CD{j}:")

    return num_fabricas, num_centros, custos, oferta, demanda_minima

def menu():
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal do Tkinter

    escolha = simpledialog.askinteger("Menu", "Escolha uma opção:\n1. Executar o script novamente\n2. Fechar o aplicativo")
    return escolha

# Loop principal
while True:
    # Obter dados do usuário
    num_fabricas, num_centros, custos, oferta, demanda_minima = obter_dados()

    # Resolver o problema de transporte com os dados fornecidos pelo usuário
    resultado = resolver_problema_transporte(num_fabricas, num_centros, custos, oferta, demanda_minima)

    # Exibir resultado e menu
    tk.messagebox.showinfo("Resultado", resultado)
    escolha = menu()
    if escolha == 1:
        continue
    elif escolha == 2:
        print("Aplicativo encerrado.")
        break
    else:
        tk.messagebox.showerror("Erro", "Opção inválida. Por favor, escolha novamente.")
