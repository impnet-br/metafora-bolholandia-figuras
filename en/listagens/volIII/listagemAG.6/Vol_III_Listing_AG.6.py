#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ------------------
# Source file:       generate_rate_equations.py
# Author:            Antonio Ferrão Neto
# Creation date:     2025-08-06
# Last modified:     2025-08-06
#
# Description:
# This program reads a text file containing a set of chemical equations with their
# respective rate constants, and automatically generates the differential rate
# equations for each species involved, based on mass-action kinetics.
#
# The parser recognizes species names with commas, slashes, leading digits, and
# other special characters common in biochemistry (e.g., Fructose1,6BP, 1,3BPG,
# 1/2O2, 3PG, 2PG, NADP+, alpha-KG).
#
# Disambiguation rule for coefficient vs. name:
#   - If there is a space between leading digits and the rest, it is split into
#     coefficient + name. Ex: "2 B" --> (2, "B"), "3 ATP" --> (3, "ATP")
#   - Otherwise, the entire term is treated as a species name with implicit
#     coefficient 1. Ex: "3PG" --> (1, "3PG"), "1,3BPG" --> (1, "1,3BPG")
#
# Consequence: stoichiometric coefficients MUST be separated from the species
# name by at least one space (e.g., "2 B", never "2B").
#
# The program supports the following output modes:
#   - Plain text (default)
#   - LaTeX (--latex)
#   - Both (--both)
#
# Additional features:
#   - Comment lines (starting with #) are ignored
#   - Verbose mode (--verbose) for debugging the parsing
#   - Input validation with detailed error messages
#   - Detection of duplicate species on the same side of the reaction
#
# Copyright: (C) 2025 Antonio Ferrão Neto. All rights reserved.
#
# Usage:
#     python generate_rate_equations.py entrada.txt saida.txt [--latex] [--both] [--verbose]
#
# Example input (entrada.txt):
#     # Hairer system (stiff)
#     0.04: A -> B
#     3e7: B + B -> B
#     1e4: B + C -> A + C
#
# Example plain-text output (saida.txt):
#     d[A]/dt = -(0.04)*[A] +(1e4)*[B]*[C]
#     d[B]/dt = +(0.04)*[A] -(3e7)*[B]**2 -(1e4)*[B]*[C]
#     d[C]/dt = 0
#
# Example LaTeX output (saida.tex):
#     \frac{d[\mathrm{A}]}{dt} &= -(0.04)\,[\mathrm{A}] +(1e4)\,[\mathrm{B}]\,[\mathrm{C}] \\
#     \frac{d[\mathrm{B}]}{dt} &= +(0.04)\,[\mathrm{A}] -(3e7)\,[\mathrm{B}]^{2} -(1e4)\,[\mathrm{B}]\,[\mathrm{C}] \\
#     \frac{d[\mathrm{C}]}{dt} &= 0
# ------------------

import re
import sys
import warnings


# ======================================
# Parsing
# ======================================

def parse_species_term(term):
    """
    Interprets an individual term of a reaction (e.g., '2 B', 'Fructose1,6BP',
    '1,3BPG', '3PG', '1/2O2') and returns (coefficient, species_name).

    Single disambiguation rule:
      - If there is a space between leading digits and the rest, split into
        coefficient and name. Ex: "2 B" -> (2, "B"),  "3 ATP" -> (3, "ATP")
      - Otherwise, the entire term is treated as a species name
        with implicit coefficient 1.
        Ex: "3PG" -> (1, "3PG"),  "1,3BPG" -> (1, "1,3BPG"),
            "1/2O2" -> (1, "1/2O2"),  "2PG" -> (1, "2PG")

    Consequence: stoichiometric coefficients MUST be separated from the species
    name by at least one space (e.g., "2 B", never "2B").
    """
    term = term.strip()
    if not term:
        return None

    # Split by space: digits + space(s) + name
    match_space = re.match(r'^(\d+)\s+(.+)$', term)
    if match_space:
        coeff = int(match_space.group(1))
        name = match_space.group(2).strip()
        return coeff, name

    # No space: the whole term is the species name
    return 1, term


def parse_side(side):
    """
    Parses one side of the reaction (reagents or products).
    Returns a dictionary {species_name: stoichiometric_coefficient}.
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
    Takes a line such as '0.04: A -> B' and returns:
    (k_value_str, reagents_dict, products_dict)
    """
    prefix = f"Line {line_number}: " if line_number is not None else ""

    if ':' not in line:
        raise ValueError(
            f"{prefix}Missing ':' separating the rate constant from the reaction.\n"
            f"  Expected format: k: reagents -> products\n"
            f"  Received: {line}"
        )
    if '->' not in line:
        raise ValueError(
            f"{prefix}Missing '->' separating reagents from products.\n"
            f"  Expected format: k: reagents -> products\n"
            f"  Received: {line}"
        )

    k_str, reaction = line.split(':', 1)
    k = k_str.strip()

    # Validate that k is a number
    try:
        float(k)
    except ValueError:
        raise ValueError(
            f"{prefix}Invalid rate constant: '{k}'\n"
            f"  Expected: a number (e.g., 0.04, 1e3, 3.2e7)\n"
            f"  Received: {line}"
        )

    left, right = reaction.split('->', 1)

    reagents = parse_side(left)
    products = parse_side(right)

    if not reagents:
        raise ValueError(
            f"{prefix}No reagent recognized on the left-hand side.\n"
            f"  Received: {line}"
        )
    if not products:
        warnings.warn(
            f"{prefix}No product recognized on the right-hand side: {line}"
        )

    return k, reagents, products


# ======================================
# Building the rate expressions
# ======================================

def build_rate_expression(k, reagents):
    """
    Builds the rate expression using the law of mass action.
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
    From a list of (k, reagents, products), generates a dictionary
    {species: ODE_string} with the differential rate equations.
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
            # Net balance for species s in this reaction
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


# ======================================
# Output formatting
# ======================================

def format_plain(ode_dict):
    """Returns the ODEs as plain text."""
    lines = []
    for specie, ode in ode_dict.items():
        lines.append(ode)
    return '\n'.join(lines)


def _latex_species(name):
    r"""
    Formats a species name for LaTeX.
    Ex: 'Fructose1,6BP' --> r'\mathrm{Fructose1{,}6BP}'
        'alpha-KG'       --> r'\mathrm{\alpha\text{-}KG}'
    For simplicity, wraps in \mathrm{} and escapes commas.
    """
    # Escape commas inside \mathrm to avoid breaking the LaTeX
    safe = name.replace(',', '{,}')
    return r'\mathrm{' + safe + '}'


def _latex_rate_expression(k, reagents):
    r"""
    Builds the rate expression in LaTeX format.
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
    Returns the ODEs formatted in LaTeX (align or aligned environment).
    """
    # Recompute terms in LaTeX
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


# ======================================
# Main function
# ======================================

def main():
    # --- Argument parsing ---
    args = sys.argv[1:]
    verbose = '--verbose' in args
    latex_mode = '--latex' in args
    both_mode = '--both' in args

    # Remove flags from the positional arguments
    positional = [a for a in args
                  if a not in ('--verbose', '--latex', '--both')]

    if len(positional) != 2:
        print(
            "Usage: python generate_rate_equations.py entrada.txt saida.txt "
            "[--latex] [--both] [--verbose]"
        )
        print()
        print("Options:")
        print("  --latex    Generates output in LaTeX format (instead of plain text)")
        print("  --both     Generates output in both formats (.txt and .tex)")
        print("  --verbose  Shows parsing details for debugging")
        sys.exit(1)

    input_path = positional[0]
    output_path = positional[1]

    # --- Reading the input file ---
    try:
        with open(input_path, encoding='utf-8') as f:
            raw_lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: file not found: {input_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading the input file: {e}")
        sys.exit(1)

    # Filter out comments and blank lines
    lines = []
    for line in raw_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            lines.append(stripped)

    if not lines:
        print("Error: no equation found in the input file.")
        sys.exit(1)

    # --- Parsing the equations ---
    parsed_equations = []
    errors = []
    for i, line in enumerate(lines, start=1):
        try:
            parsed = parse_equation(line, line_number=i)
            parsed_equations.append(parsed)
        except ValueError as e:
            errors.append(str(e))

    if errors:
        print("Errors found during parsing:")
        for err in errors:
            print(f"  {err}")
        sys.exit(1)

    # --- Verbose mode: show the parsing result ---
    if verbose:
        print("=" * 60)
        print("PARSING (verbose mode)")
        print("=" * 60)
        for i, (k, reagents, products) in enumerate(parsed_equations, 1):
            print(f"  Reaction {i}:")
            print(f"    k = {k}")
            print(f"    Reagents: {reagents}")
            print(f"    Products:  {products}")
        print("=" * 60)
        print()

    # --- Generating the rate equations ---
    ode_dict = generate_rate_equations(parsed_equations)

    # --- Writing the output file ---
    try:
        if both_mode:
            # Plain text
            plain_output = format_plain(ode_dict)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(plain_output + '\n')
            print(f"Rate equations (text) saved to: {output_path}")

            # LaTeX
            latex_path = output_path.rsplit('.', 1)[0] + '.tex'
            latex_output = format_latex(ode_dict, parsed_equations)
            with open(latex_path, 'w', encoding='utf-8') as f:
                f.write(latex_output + '\n')
            print(f"Rate equations (LaTeX) saved to: {latex_path}")

        elif latex_mode:
            latex_output = format_latex(ode_dict, parsed_equations)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(latex_output + '\n')
            print(f"Rate equations (LaTeX) saved to: {output_path}")

        else:
            plain_output = format_plain(ode_dict)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(plain_output + '\n')
            print(f"Rate equations saved to: {output_path}")

    except Exception as e:
        print(f"Error writing the output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
