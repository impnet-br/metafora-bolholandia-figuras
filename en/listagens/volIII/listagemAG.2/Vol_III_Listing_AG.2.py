#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ------------------
# Source file:       hydrogen_atom_model.py
# Author:            Antonio Ferrão Neto
# Creation date:     2025-08-06
# Last modified:     2025-08-06
#
# Description:
# Program to plot the electric field generated in a simplistic model of a hydrogen atom.
#
# Execution:
# > python hydrogen_atom_model.py
#
# ------------------
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
from matplotlib import cm
from matplotlib.colors import Normalize

# --- Provided data ---

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

# --- Cubic interpolation ---

sorted_indices = np.argsort(x_total)
x_sorted = x_total[sorted_indices]
y_sorted = y_total[sorted_indices]
x_unique, unique_indices = np.unique(x_sorted, return_index=True)
y_unique = y_sorted[unique_indices]

spline = make_interp_spline(x_unique, y_unique, k=3)

# --- Domain for function evaluation ---

x_interp = np.linspace(-10, 10, 300)

# --- Definition of p(x) = f(x) - f(x - 0.75) ---

y_p = spline(x_interp) - spline(x_interp - 0.75)

# --- Construction of the surface of revolution about the y-axis ---

theta_vals = np.linspace(0, 2 * np.pi, 200)
X, Theta = np.meshgrid(x_interp, theta_vals)

Y = y_p[np.newaxis, :]
Y = np.repeat(Y, len(theta_vals), axis=0)

Z = X * np.sin(Theta)
X_rot = X * np.cos(Theta)

# --- Colormap based on Y values ---

norm = Normalize(vmin=Y.min(), vmax=Y.max())
colors = cm.Reds(norm(Y))

# --- 3D plot ---

fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
ax.plot_wireframe(X_rot, Y, Z, color='darkred', linewidth=0.5)
ax.set_xlim([-10, 10])
ax.set_ylim([Y.min(), Y.max()])
ax.set_zlim([-10, 10])
ax.set_box_aspect([1, 0.5, 1])
ax.set_axis_off()

plt.tight_layout()
plt.show()
