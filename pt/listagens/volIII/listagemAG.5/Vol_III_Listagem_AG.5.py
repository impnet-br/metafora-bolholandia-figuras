#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ------------------
# Nome do Fonte:     energia_frequencia.py
# Autor:             Antonio Ferrão Neto
# Data de criação:   2025-08-06
# Última alteração:  2025-08-06
#
# Descrição:
# Programa para plotar o gráfico que demonstra a relação entre a energia cinética dos elétrons em Fun-
# ção da frequência.
#
# Execução:
# > python energia_frequencia.py
#
# ------------------
import numpy as np
import matplotlib.pyplot as plt

# Valores de função trabalho (em eV) e suas descrições
phi_values = {
   'Sódio (Na)': (2.28, 'goldenrod'),
   'Potássio (K)': (2.30, 'purple'),
   'Cobre (Cu)': (4.65, 'orange'),
   'Zinco (Zn)': (4.30, 'blue'),
   'Alumínio (Al)': (4.08, 'green'),
   'Prata (Ag)': (4.73, 'gray'),
   'Ouro (Au)': (5.10, 'gold')
}

# Constante de Planck (em eV*s)
h = 4.135667696e-15

# Plota os gráficos sobrepostos
plt.figure(figsize=(10, 6))

for material, (phi, color) in phi_values.items():
   # Faixa de frequência correspondente ao valor de phi em terahertz (THz)
   frequencies = np.linspace(phi/(h*1e12), 5e3, 1000)

   # Cálculo da energia cinética dos elétrons
   energies = h * frequencies * 1e12 - phi

   # Plotagem do gráfico para o material com cor correspondente
   plt.plot(frequencies, energies, label=f'{material} (phi = {phi} eV)', color=color)

plt.xlabel('Frequência (THz)')
plt.ylabel('Energia Cinética dos Elétrons (eV)')
plt.title('Energia cinética dos elétrons em função da frequência')
plt.legend()
plt.grid(True)
plt.show()
