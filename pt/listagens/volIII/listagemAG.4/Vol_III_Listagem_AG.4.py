#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ------------------
# Nome do Fonte:     corrente_fotoeletrica.py
# Autor:             Antonio Ferrão Neto
# Data de criação:   2025-08-06
# Última alteração:  2025-08-06
#
# Descrição:
# Programa para plotar o gráfico que demonstra o Efeito Fotoelétrico.
#
# Execução:
# > python corrente_fotoeletrica.py
#
# ------------------
import numpy as np
import matplotlib.pyplot as plt

def sigmoid(x, Imax, V0, k):
   desl_vert = -0.1
   desl_hor = -12.0
   return Imax * np.maximum(1 / (1 + np.exp(-k * (x - V0 + desl_hor))) + desl_vert, 0)

# Parâmetros da função sigmoide
Imax_values = [0.10, 0.33, 0.66, 1.00]  # Valores de Imax a serem plotados
V0 = 5.0  # Valor de voltagem no ponto médio
k = 0.1  # Parâmetro que controla a inclinação da curva sigmoide

# Valores de voltagem
V = np.linspace(-30, 100, 1000)  # Intervalo de voltagem de -30 a 100V

# Plot dos gráficos sobrepostos
for Imax in Imax_values:
   I = sigmoid(V, Imax, V0, k)
   plt.plot(V, I, label=f'Imax={Imax}')

# Destacando os eixos vertical e horizontal
plt.axhline(y=0, color='k', linewidth=1.0)
plt.axvline(x=0, color='k', linewidth=1.0)

# Marcando o ponto (V=-5.0V, i=0uA) com o label "V_0"
plt.scatter([-5.0], [0], color='black')
plt.text(-4.50, -0.05, '$V_0$', ha='right', va='bottom')

plt.xlabel('Voltagem (V)')
plt.ylabel('Corrente fotoelétrica (uA)')
plt.title('Gráfico conceitual da corrente fotoelétrica com a mesma frequência\n e mesmo metal no catodo e várias intensidades de luz')
plt.grid(True, linestyle='dotted')  # Configurando a grade como pontilhada
plt.legend()
plt.show()
