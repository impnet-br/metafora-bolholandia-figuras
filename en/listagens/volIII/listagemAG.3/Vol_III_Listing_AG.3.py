#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ------------------
# Source file:       uv_catastrophe_plot.py
# Author:            Antonio Ferrão Neto
# Creation date:     2025-08-06
# Last modified:     2025-08-06
#
# Description:
# Program to plot the graph that demonstrates the ultraviolet catastrophe.
#
# Execution:
# > python uv_catastrophe_plot.py
#
# ------------------
import numpy as np
import matplotlib.pyplot as plt

# Constant definitions
h = 6.62607015e-34  # Planck constant in J.s
c = 299792458  # speed of light in m/s
k = 1.380649e-23  # Boltzmann constant in J/K

# Wavelength range in nanometers
wavelengths = np.linspace(1, 4000, 1000)

# Temperatures
temperatures = [3000, 4000, 5000, 6000, 7000]

# Colors corresponding to the temperatures
colors = ['blue', 'orange', 'green', 'red', 'purple']

# Function to compute the spectral energy density using Planck's expression
def spectral_radiance_planck(wavelength, temperature):
    wavelength_m = wavelength * 1e-9  # convert to meters
    numerator = 2 * h * c**2
    with np.errstate(over='ignore'):
        denominator = wavelength_m**5 * (np.exp((h * c) / (wavelength_m * k * temperature)) - 1)
    return numerator / denominator

# Function to compute the spectral energy density using the Rayleigh-Jeans expression
def spectral_radiance_rayleigh_jeans(wavelength, temperature):
    wavelength_m = wavelength * 1e-9  # convert to meters
    numerator = 2 * c * k * temperature
    denominator = wavelength_m**4
    return numerator / denominator

# Plot the spectral energy densities for each temperature
for i, temperature in enumerate(temperatures):
    radiance_planck = spectral_radiance_planck(wavelengths, temperature)
    radiance_rayleigh_jeans = spectral_radiance_rayleigh_jeans(wavelengths, temperature)
    plt.plot(wavelengths, radiance_planck, color=colors[i], label=f"{temperature}K")
    plt.plot(wavelengths, radiance_rayleigh_jeans, '--', color=colors[i])

# Experimental data
experimental_data = {
    200: 7.00e11, 250: 1.10e12, 300: 2.50e12, 350: 5.70e12, 400: 9.00e12, 450: 1.16e13, 500: 1.22e13, 550: 1.24e13,
    600: 1.23e13, 650: 1.19e13, 700: 1.12e13, 750: 1.02e13, 850: 8.97e12, 900: 7.86e12, 1000: 6.70e12,
    1150: 4.51e12, 1300: 3.48e12, 1350: 3.00e12, 1500: 2.30e12, 1600: 1.84e12, 1700: 1.40e12, 1800: 1.30e12,
    1950: 8.70e11, 2100: 7.80e11, 2200: 5.80e11, 2350: 4.90e11, 2450: 4.20e11, 2550: 3.70e11, 2700: 2.20e11,
    2900: 1.40e11
}

# Extract the wavelengths and intensities
exp_wavelengths = list(experimental_data.keys())
exp_intensities = list(experimental_data.values())

# Plot the experimental points
plt.scatter(exp_wavelengths, exp_intensities, color='#006400', s=10)

# Add a dark green point to the legend
plt.plot([], [], 'o', color='#006400', label='Experimental data (T=5000K)')

# Spectrum regions and their wavelength ranges
uv_region = [1, 400]
visible_region = [400, 700]
infrared_region = [700, 4000]

# Marking the regions on the plot
# Ultraviolet band
plt.axvspan(uv_region[0], uv_region[1], facecolor='#300030', alpha=0.2, label='Ultraviolet (invisible)', linewidth=0)

# Add vertical bands for the visible-light colors
plt.axvspan(400, 450, color='#906090', alpha=0.7, label='Violet', linewidth=0)
plt.axvspan(450, 495, color='blue', alpha=0.42, label='Blue', linewidth=0)
plt.axvspan(495, 570, color='green', alpha=0.42, label='Green', linewidth=0)
plt.axvspan(570, 590, color='yellow', alpha=0.42, label='Yellow', linewidth=0)
plt.axvspan(590, 620, color='orange', alpha=0.62, label='Orange', linewidth=0)
plt.axvspan(620, 700, color='red', alpha=0.52, label='Red', linewidth=0)

# Infrared band
plt.axvspan(infrared_region[0], infrared_region[1], facecolor='#FFCC99', alpha=0.2, label='Infrared (invisible)', linewidth=0)

# Plot settings
plt.xlabel('Wavelength (nm)')
plt.ylabel('Spectral Radiance (W.sr^-1.m^-3.m^-2)')
plt.title('Spectral Energy Density of the Black Body\nPlanck (solid line) vs Rayleigh-Jeans (dashed line)')
plt.legend()
plt.grid(True)

# Limit the vertical axis to 8e13
plt.ylim(0, 8e13)

# Display the plot
plt.show()
