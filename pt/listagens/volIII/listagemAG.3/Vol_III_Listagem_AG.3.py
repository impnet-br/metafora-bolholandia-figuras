#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ------------------
# Nome do Fonte:     grafico_catast_uv2.py
# Autor:             Antonio Ferrão Neto
# Data de criação:   2025-08-06
# Última alteração:  2025-08-06
#
# Descrição:
# Programa para plotar o gráfico que demonstra a catástrofe do ultravioleta.
#
# Execução:
# > python grafico_catast_uv2.py
#
# ------------------
import numpy as np
import matplotlib.pyplot as plt

# Definição das constantes
h = 6.62607015e-34  # constante de Planck em J.s
c = 299792458  # velocidade da luz em m/s
k = 1.380649e-23  # constante de Boltzmann em J/K

# Faixa de comprimento de onda em nanômetros
wavelengths = np.linspace(1, 4000, 1000)

# Temperaturas
temperatures = [3000, 4000, 5000, 6000, 7000]

# Cores correspondentes às temperaturas
colors = ['blue', 'orange', 'green', 'red', 'purple']

# Função para calcular a densidade espectral de energia pela expressão de Planck
def spectral_radiance_planck(wavelength, temperature):
    wavelength_m = wavelength * 1e-9  # converter para metros
    numerator = 2 * h * c**2
    with np.errstate(over='ignore'):
        denominator = wavelength_m**5 * (np.exp((h * c) / (wavelength_m * k * temperature)) - 1)
    return numerator / denominator

# Função para calcular a densidade espectral de energia pela expressão de Rayleigh-Jeans
def spectral_radiance_rayleigh_jeans(wavelength, temperature):
    wavelength_m = wavelength * 1e-9  # converter para metros
    numerator = 2 * c * k * temperature
    denominator = wavelength_m**4
    return numerator / denominator

# Plotar as densidades espectrais de energia para cada temperatura
for i, temperature in enumerate(temperatures):
    radiance_planck = spectral_radiance_planck(wavelengths, temperature)
    radiance_rayleigh_jeans = spectral_radiance_rayleigh_jeans(wavelengths, temperature)
    plt.plot(wavelengths, radiance_planck, color=colors[i], label=f"{temperature}K")
    plt.plot(wavelengths, radiance_rayleigh_jeans, '--', color=colors[i])

# Dados experimentais
experimental_data = {
    200: 7.00e11, 250: 1.10e12, 300: 2.50e12, 350: 5.70e12, 400: 9.00e12, 450: 1.16e13, 500: 1.22e13, 550: 1.24e13,
    600: 1.23e13, 650: 1.19e13, 700: 1.12e13, 750: 1.02e13, 850: 8.97e12, 900: 7.86e12, 1000: 6.70e12,
    1150: 4.51e12, 1300: 3.48e12, 1350: 3.00e12, 1500: 2.30e12, 1600: 1.84e12, 1700: 1.40e12, 1800: 1.30e12,
    1950: 8.70e11, 2100: 7.80e11, 2200: 5.80e11, 2350: 4.90e11, 2450: 4.20e11, 2550: 3.70e11, 2700: 2.20e11,
    2900: 1.40e11
}

# Extrair os comprimentos de onda e as intensidades
exp_wavelengths = list(experimental_data.keys())
exp_intensities = list(experimental_data.values())

# Plotar os pontos experimentais
plt.scatter(exp_wavelengths, exp_intensities, color='#006400', s=10)

# Adicionar um ponto verde escuro na legenda
plt.plot([], [], 'o', color='#006400', label='Dados experimentais (T=5000K)')

# Regiões do espectro e suas faixas de comprimento de onda
uv_region = [1, 400]
visible_region = [400, 700]
infrared_region = [700, 4000]

# Indicação das regiões no gráfico
# Faixa Ultravioleta
plt.axvspan(uv_region[0], uv_region[1], facecolor='#300030', alpha=0.2, label='Ultravioleta (invisível)', linewidth=0)

# Adicionar faixas verticais para as cores da luz visível
plt.axvspan(400, 450, color='#906090', alpha=0.7, label='Violeta', linewidth=0)
plt.axvspan(450, 495, color='blue', alpha=0.42, label='Azul', linewidth=0)
plt.axvspan(495, 570, color='green', alpha=0.42, label='Verde', linewidth=0)
plt.axvspan(570, 590, color='yellow', alpha=0.42, label='Amarelo', linewidth=0)
plt.axvspan(590, 620, color='orange', alpha=0.62, label='Laranja', linewidth=0)
plt.axvspan(620, 700, color='red', alpha=0.52, label='Vermelho', linewidth=0)

# Faixa Infravermelha
plt.axvspan(infrared_region[0], infrared_region[1], facecolor='#FFCC99', alpha=0.2, label='Infravermelho (invisível)', linewidth=0)

# Configurações do gráfico
plt.xlabel('Comprimento de Onda (nm)')
plt.ylabel('Radiancia Espectral (W.sr^-1.m^-3.m^-2)')
plt.title('Densidade espectral de energia do corpo negro\nPlanck (linha cheia) vs Rayleigh-Jeans (linha tracejada)')
plt.legend()
plt.grid(True)

# Limitar o eixo vertical a 8e13
plt.ylim(0, 8e13)

# Exibir o gráfico
plt.show()
