import pulp

# Criação do problema de minimização
problema = pulp.LpProblem("Problema de Transporte", pulp.LpMinimize)

# Variáveis de decisão
x = pulp.LpVariable.dicts("quantidade_enviada",
                           [(i, j) for i in ["Planta1", "Planta2"]
                                  for j in ["CD1", "CD2", "CD3"]],
                           lowBound=0,
                           cat='Continuous')

# Definição dos custos de transporte
custos = {
    ("Planta1", "CD1"): 700,
    ("Planta1", "CD2"): 900,
    ("Planta1", "CD3"): 800,
    ("Planta2", "CD1"): 800,
    ("Planta2", "CD2"): 900,
    ("Planta2", "CD3"): 700
}

# Adição da função objetivo
problema += sum(custos[i, j] * x[i, j] for i in ["Planta1", "Planta2"] for j in ["CD1", "CD2", "CD3"]), "Custo Total de Transporte"

print(problema)

# Restrições de oferta
problema += sum(x[("Planta1", j)] for j in ["CD1", "CD2", "CD3"]) <= 12, "Oferta Planta1"
problema += sum(x[("Planta2", j)] for j in ["CD1", "CD2", "CD3"]) <= 15, "Oferta Planta2"



# Restrições de demanda mínima para cada centro de distribuição
demanda_minima = {"CD1": 10, "CD2": 8, "CD3": 9}
for j in ["CD1", "CD2", "CD3"]:
    problema += sum(x[(i, j)] for i in ["Planta1", "Planta2"]) >= demanda_minima[j], f"Demand_Min_{j}"
    


# Restrições de distribuição
for i in ["Planta1", "Planta2"]:
    for j in ["CD1", "CD2", "CD3"]:
        problema += x[(i, j)] >= 1, f"Restricao_distribuicao_{i}_{j}"



# Resolvendo o problema
problema.solve()



# Exibindo os resultados
print("Status:", pulp.LpStatus[problema.status])
print("Custo Total de Transporte =", pulp.value(problema.objective))
for var in x.values():
    print(f"A quantidade enviada de {var.name} é {var.varValue}")
