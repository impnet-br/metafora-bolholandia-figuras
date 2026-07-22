#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ------------------
# Nome do Fonte:     eletron_model.py
# Autor:             Antonio Ferrão Neto
# Data de criação:   2025-08-06
# Última alteração:  2025-08-06
#
# Descrição:
# Programa para plotar o campo elétrico gerado num modelo simplista de um elétron.
#
# Execução:
# > python eletron_model.py
#
# ------------------
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline

# --- 1. Dados fornecidos ---

# Pontos para f(x)
x1 = np.linspace(-10.0, -0.5, 50)
y1 = 1 / (x1 ** 2)

x2 = np.array([
    0.0, -0.1, -0.2, -0.3, -0.4, -0.41, -0.43, -0.45, -0.47, -0.49,
    0.0,  0.1,  0.2,  0.3,  0.4,  0.41,  0.43,  0.45,  0.47,  0.49
])
y2 = np.array([
   -5.0, -4.9, -3.0,  2.0,  4.0,  4.1,  4.3,  4.4,  4.3,  4.1,
   -5.0, -4.9, -3.0,  2.0,  4.0,  4.1,  4.3,  4.4,  4.3,  4.1
])

x3 = np.linspace(0.5, 10.0, 50)
y3 = 1 / (x3 ** 2)

x_total = np.concatenate([x1, x2, x3])
y_total = np.concatenate([y1, y2, y3])

# --- 2. Interpolação cúbica ---

sorted_indices = np.argsort(x_total)
x_sorted = x_total[sorted_indices]
y_sorted = y_total[sorted_indices]
x_unique, unique_indices = np.unique(x_sorted, return_index=True)
y_unique = y_sorted[unique_indices]

spline = make_interp_spline(x_unique, y_unique, k=3)

# --- 3. Superfície de revolução em torno do eixo y ---

x_vals = np.linspace(-10, 10, 300)
theta_vals = np.linspace(0, 2 * np.pi, 200)
X, Theta = np.meshgrid(x_vals, theta_vals)

Y = np.zeros_like(X)
mask = (X >= np.min(x_unique)) & (X <= np.max(x_unique))
Y[mask] = spline(X[mask])

X_rot = X * np.cos(Theta)
Z_rot = X * np.sin(Theta)

# --- 4. Gráfico 3D interativo ---

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')
ax.plot_wireframe(X_rot, Y, Z_rot, color='darkblue', linewidth=0.5)
ax.set_xlim([-10, 10])
ax.set_ylim([np.min(y_total), np.max(y_total)])
ax.set_zlim([-10, 10])
ax.set_box_aspect([1, 0.5, 1])  # proporções do gráfico
ax.set_axis_off()

plt.show()
