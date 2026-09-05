#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ------------------
# Source file:       energy_vs_frequency.py
# Author:            Antonio Ferrão Neto
# Creation date:     2025-08-06
# Last modified:     2025-08-06
#
# Description:
# Program to plot the graph that demonstrates the relationship between the kinetic
# energy of the electrons as a function of frequency.
#
# Execution:
# > python energy_vs_frequency.py
#
# ------------------
import numpy as np
import matplotlib.pyplot as plt

# Work-function values (in eV) and their descriptions
phi_values = {
   'Sodium (Na)': (2.28, 'goldenrod'),
   'Potassium (K)': (2.30, 'purple'),
   'Copper (Cu)': (4.65, 'orange'),
   'Zinc (Zn)': (4.30, 'blue'),
   'Aluminum (Al)': (4.08, 'green'),
   'Silver (Ag)': (4.73, 'gray'),
   'Gold (Au)': (5.10, 'gold')
}

# Planck constant (in eV*s)
h = 4.135667696e-15

# Plot the overlaid curves
plt.figure(figsize=(10, 6))

for material, (phi, color) in phi_values.items():
   # Frequency range corresponding to the phi value, in terahertz (THz)
   frequencies = np.linspace(phi/(h*1e12), 5e3, 1000)

   # Computation of the electrons' kinetic energy
   energies = h * frequencies * 1e12 - phi

   # Plotting the graph for the material with the corresponding color
   plt.plot(frequencies, energies, label=f'{material} (phi = {phi} eV)', color=color)

plt.xlabel('Frequency (THz)')
plt.ylabel('Kinetic Energy of the Electrons (eV)')
plt.title('Kinetic energy of the electrons as a function of frequency')
plt.legend()
plt.grid(True)
plt.show()
