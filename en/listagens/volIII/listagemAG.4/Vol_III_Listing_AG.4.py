#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ------------------
# Source file:       photoelectric_current.py
# Author:            Antonio Ferrão Neto
# Creation date:     2025-08-06
# Last modified:     2025-08-06
#
# Description:
# Program to plot the graph that demonstrates the Photoelectric Effect.
#
# Execution:
# > python photoelectric_current.py
#
# ------------------
import numpy as np
import matplotlib.pyplot as plt

def sigmoid(x, Imax, V0, k):
   desl_vert = -0.1
   desl_hor = -12.0
   return Imax * np.maximum(1 / (1 + np.exp(-k * (x - V0 + desl_hor))) + desl_vert, 0)

# Sigmoid function parameters
Imax_values = [0.10, 0.33, 0.66, 1.00]  # Imax values to be plotted
V0 = 5.0  # Voltage value at the midpoint
k = 0.1  # Parameter controlling the slope of the sigmoid curve

# Voltage values
V = np.linspace(-30, 100, 1000)  # Voltage range from -30 to 100V

# Plot of the overlaid curves
for Imax in Imax_values:
   I = sigmoid(V, Imax, V0, k)
   plt.plot(V, I, label=f'Imax={Imax}')

# Highlighting the vertical and horizontal axes
plt.axhline(y=0, color='k', linewidth=1.0)
plt.axvline(x=0, color='k', linewidth=1.0)

# Marking the point (V=-5.0V, i=0uA) with the label "V_0"
plt.scatter([-5.0], [0], color='black')
plt.text(-4.50, -0.05, '$V_0$', ha='right', va='bottom')

plt.xlabel('Voltage (V)')
plt.ylabel('Photoelectric current (uA)')
plt.title('Conceptual Plot of the Photoelectric Current With the Same Frequency\n and the Same Cathode Metal and Various Light Intensities')
plt.grid(True, linestyle='dotted')  # Setting the grid as dotted
plt.legend()
plt.show()
