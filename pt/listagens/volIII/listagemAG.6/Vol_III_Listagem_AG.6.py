#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ------------------
# Nome do Fonte:     gerar_equacoes_de_taxa.py
# Autor:             Antonio Ferrão Neto
# Data de criação:   2025-08-06
# Última alteração:  2025-08-06
#
# Descrição:
# Este programa recebe um arquivo texto contendo um conjunto de equações químicas
# com suas respectivas constantes de velocidade, e gera automaticamente as equações
# diferenciais de taxa para cada espécie envolvida, baseando-se na lei da ação das
# massas (mass-action kinetics).
#
# O parser reconhece nomes de espécies com vírgulas, barras, dígitos iniciais e
# outros caracteres especiais comuns em bioquímica (ex: Fructose1,6BP, 1,3BPG,
# 1/2O2, 3PG, 2PG, NADP+, alpha-KG).
#
# Regra de desambiguação coeficiente vs. nome:
#   - Se há espaço entre dígitos iniciais e o resto, separa coeficiente e nome.
#     Ex: "2 B" --> (2, "B"),  "3 ATP" --> (3, "ATP")
#   - Caso contrário, o termo inteiro é tratado como nome de espécie com
#     coeficiente implícito 1.
#     Ex: "3PG" --> (1, "3PG"),  "1,3BPG" --> (1, "1,3BPG"),
#         "1/2O2" --> (1, "1/2O2"),  "2PG" --> (1, "2PG")
#
# Consequência: coeficientes estequiométricos DEVEM ser separados do nome da
# espécie por ao menos um espaço (ex: "2 B", nunca "2B").
#
# O programa suporta os seguintes modos de saída:
#   - Texto plano (padrão)
#   - LaTeX (--latex)
#   - Ambos (--both)
#
# Funcionalidades adicionais:
#   - Linhas de comentário (iniciadas por #) são ignoradas
#   - Modo verboso (--verbose) para depuração do parsing
#   - Validação de entrada com mensagens de erro detalhadas
#   - Detecção de espécies duplicadas em um mesmo lado da reação
#
# Copyright: (C) 2025 Antonio Ferrão Neto. Todos os direitos reservados.
#
# Uso:
#     python gerar_equacoes_de_taxa.py entrada.txt saida.txt [--latex] [--both] [--verbose]
#
# Exemplo de entrada (entrada.txt):
#     # Sistema de Hairer (stiff)
#     0.04: A -> B
#     3e7: B + B -> B
#     1e4: B + C -> A + C
#
# Exemplo de saída em texto plano (saida.txt):
#     d[A]/dt = -(0.04)*[A] +(1e4)*[B]*[C]
#     d[B]/dt = +(0.04)*[A] -(3e7)*[B]**2 -(1e4)*[B]*[C]
#     d[C]/dt = 0
#
# Exemplo de saída em LaTeX (saida.tex):
#     \frac{d[\mathrm{A}]}{dt} &= -(0.04)\,[\mathrm{A}] +(1e4)\,[\mathrm{B}]\,[\mathrm{C}] \\
#     \frac{d[\mathrm{B}]}{dt} &= +(0.04)\,[\mathrm{A}] -(3e7)\,[\mathrm{B}]^{2} -(1e4)\,[\mathrm{B}]\,[\mathrm{C}] \\
#     \frac{d[\mathrm{C}]}{dt} &= 0
# ------------------

import re
import sys
import warnings


# ==========================================
# Parsing
# ==========================================

def parse_species_term(term):
    """
    Interpreta um termo individual de uma reação (ex: '2 B', 'Fructose1,6BP',
    '1,3BPG', '3PG', '1/2O2') e retorna (coeficiente, nome_da_espécie).

    Regra única de desambiguação:
      - Se há espaço entre dígitos iniciais e o resto, separa coeficiente e nome.
        Ex: "2 B" -> (2, "B"),  "3 ATP" -> (3, "ATP")
      - Caso contrário, o termo inteiro é tratado como nome de espécie
        com coeficiente implícito 1.
        Ex: "3PG" -> (1, "3PG"),  "1,3BPG" -> (1, "1,3BPG"),
            "1/2O2" -> (1, "1/2O2"),  "2PG" -> (1, "2PG")

    Consequência: coeficientes estequiométricos DEVEM ser separados do nome
    da espécie por ao menos um espaço (ex: "2 B", nunca "2B").
    """
    term = term.strip()
    if not term:
        return None

    # Separação por espaço: dígitos + espaço(s) + nome
    match_space = re.match(r'^(\d+)\s+(.+)$', term)
    if match_space:
        coeff = int(match_space.group(1))
        name = match_space.group(2).strip()
        return coeff, name

    # Sem espaço: tudo é nome da espécie
    return 1, term


def parse_side(side):
    """
    Faz o parsing de um lado da reação (reagentes ou produtos).
    Retorna um dicionário {nome_espécie: coeficiente_estequiométrico}.
    """
    species = {}
    terms = [t.strip() for t in side.strip().split('+')]

    for term in terms:
        if not term:
            continue
        result = parse_species_term(term)
        if result is None:
            continue
        coeff, name = result

        if name in species:
            species[name] += coeff
        else:
            species[name] = coeff

    return species


def parse_equation(line, line_number=None):
    """
    Recebe uma linha como '0.04: A -> B' e retorna:
    (k_value_str, reagents_dict, products_dict)
    """
    prefix = f"Linha {line_number}: " if line_number is not None else ""

    if ':' not in line:
        raise ValueError(
            f"{prefix}Falta ':' separando a constante de velocidade da reação.\n"
            f"  Formato esperado: k: reagentes -> produtos\n"
            f"  Recebido: {line}"
        )
    if '->' not in line:
        raise ValueError(
            f"{prefix}Falta '->' separando reagentes de produtos.\n"
            f"  Formato esperado: k: reagentes -> produtos\n"
            f"  Recebido: {line}"
        )

    k_str, reaction = line.split(':', 1)
    k = k_str.strip()

    # Validar que k é um número
    try:
        float(k)
    except ValueError:
        raise ValueError(
            f"{prefix}Constante de velocidade inválida: '{k}'\n"
            f"  Esperado: número (ex: 0.04, 1e3, 3.2e7)\n"
            f"  Recebido: {line}"
        )

    left, right = reaction.split('->', 1)

    reagents = parse_side(left)
    products = parse_side(right)

    if not reagents:
        raise ValueError(
            f"{prefix}Nenhum reagente reconhecido no lado esquerdo.\n"
            f"  Recebido: {line}"
        )
    if not products:
        warnings.warn(
            f"{prefix}Nenhum produto reconhecido no lado direito: {line}"
        )

    return k, reagents, products


# ==========================================
# Construção das expressões de taxa
# ==========================================

def build_rate_expression(k, reagents):
    """
    Constrói a expressão da taxa pela lei da ação das massas.
    Ex: k=0.04, reagents={'A':1, 'B':2} --> '(0.04)*[A]*[B]**2'
    """
    expr = f'({k})'
    for s, coeff in reagents.items():
        if coeff == 1:
            expr += f'*[{s}]'
        else:
            expr += f'*[{s}]**{coeff}'
    return expr


def generate_rate_equations(parsed_equations):
    """
    A partir de uma lista de (k, reagentes, produtos), gera um dicionário
    {espécie: string_da_ODE} com as equações diferenciais de taxa.
    """
    species_set = set()
    rates = []

    for k_value, reagents, products in parsed_equations:
        rate_expr = build_rate_expression(k_value, reagents)
        rates.append({
            'k': k_value,
            'reagents': reagents,
            'products': products,
            'expression': rate_expr
        })
        species_set.update(reagents)
        species_set.update(products)

    ode_dict = {}
    for s in sorted(species_set):
        terms = []
        for rate in rates:
            # Saldo líquido para a espécie s nesta reação
            net_coeff = 0
            if s in rate['products']:
                net_coeff += rate['products'][s]
            if s in rate['reagents']:
                net_coeff -= rate['reagents'][s]

            if net_coeff != 0:
                if net_coeff == 1:
                    terms.append(f'+{rate["expression"]}')
                elif net_coeff == -1:
                    terms.append(f'-{rate["expression"]}')
                else:
                    sign = '+' if net_coeff > 0 else '-'
                    terms.append(
                        f'{sign}{abs(net_coeff)}*{rate["expression"]}'
                    )

        if terms:
            ode_dict[s] = f'd[{s}]/dt = {" ".join(terms)}'
        else:
            ode_dict[s] = f'd[{s}]/dt = 0'

    return ode_dict


# ==========================================
# Formatação de saída
# ==========================================

def format_plain(ode_dict):
    """Retorna as ODEs como texto plano."""
    lines = []
    for specie, ode in ode_dict.items():
        lines.append(ode)
    return '\n'.join(lines)


def _latex_species(name):
    r"""
    Formata o nome de uma espécie para LaTeX.
    Ex: 'Fructose1,6BP' --> r'\mathrm{Fructose1{,}6BP}'
        'alpha-KG'       --> r'\mathrm{\alpha\text{-}KG}'
    Para simplicidade, envolve em \mathrm{} e escapa vírgulas.
    """
    # Escapar vírgula dentro de \mathrm para evitar quebra no LaTeX
    safe = name.replace(',', '{,}')
    return r'\mathrm{' + safe + '}'


def _latex_rate_expression(k, reagents):
    r"""
    Constrói a expressão da taxa em formato LaTeX.
    Ex: k='0.04', reagents={'A':1, 'B':2}
        --> r'(0.04)\,[\mathrm{A}]\,[\mathrm{B}]^{2}'
    """
    expr = f'({k})'
    for s, coeff in reagents.items():
        ls = _latex_species(s)
        if coeff == 1:
            expr += rf'\,[{ls}]'
        else:
            expr += rf'\,[{ls}]^{{{coeff}}}'
    return expr


def format_latex(ode_dict, parsed_equations):
    """
    Retorna as ODEs formatadas em LaTeX (ambiente align ou aligned).
    """
    # Recalcular termos em LaTeX
    species_set = set()
    rates = []
    for k_value, reagents, products in parsed_equations:
        rate_expr = _latex_rate_expression(k_value, reagents)
        rates.append({
            'reagents': reagents,
            'products': products,
            'expression': rate_expr
        })
        species_set.update(reagents)
        species_set.update(products)

    lines = []
    sorted_species = sorted(species_set)
    for i, s in enumerate(sorted_species):
        ls = _latex_species(s)
        terms = []
        for rate in rates:
            net_coeff = 0
            if s in rate['products']:
                net_coeff += rate['products'][s]
            if s in rate['reagents']:
                net_coeff -= rate['reagents'][s]
            if net_coeff != 0:
                if net_coeff == 1:
                    terms.append(f'+{rate["expression"]}')
                elif net_coeff == -1:
                    terms.append(f'-{rate["expression"]}')
                else:
                    sign = '+' if net_coeff > 0 else '-'
                    terms.append(
                        f'{sign}{abs(net_coeff)} \\cdot {rate["expression"]}'
                    )

        rhs = ' '.join(terms) if terms else '0'
        suffix = ' \\\\' if i < len(sorted_species) - 1 else ''
        lines.append(
            rf'\frac{{d[{ls}]}}{{dt}} &= {rhs}{suffix}'
        )

    return '\n'.join(lines)


# ==========================================
# Função principal
# ==========================================

def main():
    # --- Parsing de argumentos ---
    args = sys.argv[1:]
    verbose = '--verbose' in args
    latex_mode = '--latex' in args
    both_mode = '--both' in args

    # Remover flags dos argumentos posicionais
    positional = [a for a in args
                  if a not in ('--verbose', '--latex', '--both')]

    if len(positional) != 2:
        print(
            "Uso: python gerar_equacoes_de_taxa.py entrada.txt saida.txt "
            "[--latex] [--both] [--verbose]"
        )
        print()
        print("Opções:")
        print("  --latex    Gera saída em formato LaTeX (em vez de texto plano)")
        print("  --both     Gera saída em ambos os formatos (.txt e .tex)")
        print("  --verbose  Mostra detalhes do parsing para depuração")
        sys.exit(1)

    input_path = positional[0]
    output_path = positional[1]

    # --- Leitura do arquivo de entrada ---
    try:
        with open(input_path, encoding='utf-8') as f:
            raw_lines = f.readlines()
    except FileNotFoundError:
        print(f"Erro: arquivo não encontrado: {input_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao ler o arquivo de entrada: {e}")
        sys.exit(1)

    # Filtrar comentários e linhas em branco
    lines = []
    for line in raw_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            lines.append(stripped)

    if not lines:
        print("Erro: nenhuma equação encontrada no arquivo de entrada.")
        sys.exit(1)

    # --- Parsing das equações ---
    parsed_equations = []
    errors = []
    for i, line in enumerate(lines, start=1):
        try:
            parsed = parse_equation(line, line_number=i)
            parsed_equations.append(parsed)
        except ValueError as e:
            errors.append(str(e))

    if errors:
        print("Erros encontrados durante o parsing:")
        for err in errors:
            print(f"  {err}")
        sys.exit(1)

    # --- Modo verboso: mostrar resultado do parsing ---
    if verbose:
        print("=" * 60)
        print("PARSING (modo verboso)")
        print("=" * 60)
        for i, (k, reagents, products) in enumerate(parsed_equations, 1):
            print(f"  Reação {i}:")
            print(f"    k = {k}")
            print(f"    Reagentes: {reagents}")
            print(f"    Produtos:  {products}")
        print("=" * 60)
        print()

    # --- Geração das equações de taxa ---
    ode_dict = generate_rate_equations(parsed_equations)

    # --- Escrita do arquivo de saída ---
    try:
        if both_mode:
            # Texto plano
            plain_output = format_plain(ode_dict)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(plain_output + '\n')
            print(f"Equações de taxa (texto) salvas em: {output_path}")

            # LaTeX
            latex_path = output_path.rsplit('.', 1)[0] + '.tex'
            latex_output = format_latex(ode_dict, parsed_equations)
            with open(latex_path, 'w', encoding='utf-8') as f:
                f.write(latex_output + '\n')
            print(f"Equações de taxa (LaTeX) salvas em: {latex_path}")

        elif latex_mode:
            latex_output = format_latex(ode_dict, parsed_equations)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(latex_output + '\n')
            print(f"Equações de taxa (LaTeX) salvas em: {output_path}")

        else:
            plain_output = format_plain(ode_dict)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(plain_output + '\n')
            print(f"Equações de taxa salvas em: {output_path}")

    except Exception as e:
        print(f"Erro ao escrever o arquivo de saída: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
