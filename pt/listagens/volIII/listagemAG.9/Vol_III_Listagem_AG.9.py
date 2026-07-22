#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ------------------
# Nome do Fonte:     mzs_dispositivo.py
# Autor:             Antonio Ferrão Neto
# Data de criação:   2025-08-08
# Última alteração:  2025-08-08
#
# Descrição:
# Prova de conceito do Método dos Zooms Sucessivos (MZS) com ênfase na
# **inalcançabilidade do número em estudo**: o valor alvo (resultado analógico)
# não é exposto nem mantido como atributo do objeto. Apenas artefatos estritamente
# necessários à extração incremental (mantissa normalizada, expoente e sinal)
# são retidos, e mesmo assim já *desacoplados* do valor original.
#
# O "dispositivo" simula um sensor que retorna **blocos de 2 dígitos significativos**
# da mantissa por interação. A cada leitura, aplica-se **zoom + translação** no
# resíduo para trazer os próximos dígitos à frente. O processo termina quando o
# resíduo cai abaixo do limiar definido pela precisão.
#
# Copyright:
# Copyright: (C) 2025 Antonio Ferrão Neto. Todos os direitos reservados.
#
# Uso:
#     python mzs_dispositivo.py
#
# Exemplo de saída:
#     n          lista_f    lista_mantissas         lista_dig_ac
#     0            45       0.34697376592671294822           45
#     1            34       0.69737659267129482276         4534
#     2            69       0.73765926712948227638       453469
#     ...
#     Resultado final: 4.534697e-27
# ------------------
import decimal
from decimal import Decimal, getcontext, ROUND_FLOOR


class MZSDispositivo:
    """
    Dispositivo MZS que **não armazena** o número em estudo como atributo.
    Apenas mantém a mantissa normalizada (in [1,10)), expoente científico e sinal,
    suficientes para simular leituras incrementais. O valor original nunca é
    exposto e não é recuperável via API pública.
    """

    __slots__ = ("_precisao", "_mantissa_norm", "_expoente", "_sinal", "_limiar")

    def __init__(self, precisao: int, numero=None):
        if precisao < 1:
            raise ValueError("precisão deve ser >= 1")
        self._precisao = int(precisao)

        # Nota: modifica decimal.getcontext() globalmente.
        # Para uso concorrente, substituir por decimal.localcontext().
        getcontext().prec = self._precisao

        # --- Normalização científica do valor alvo (sem armazená-lo depois) ---
        if numero is None:
            _valor = Decimal('0.000000000000000000000000004534697376592671294822767382'
                             '8785441322473869300353232')
        else:
            _valor = Decimal(str(numero))

        if _valor.is_zero():
            self._sinal = ''
            self._expoente = 0
            self._mantissa_norm = Decimal(0)
        else:
            self._sinal = '-' if _valor.is_signed() else ''
            adj = _valor.adjusted()                # expoente científico
            self._expoente = adj
            self._mantissa_norm = _valor.copy_abs().scaleb(-adj)  # in [1,10)

        # Descartar referência ao valor original - torna-o inacessível
        del _valor

        # Menor valor "perceptível" com a precisão atual
        self._limiar = Decimal('1').scaleb(-(self._precisao - 1))

    # --------- Blindagem básica contra introspecção casual ----------
    def __repr__(self):
        return f"<MZSDispositivo precisao={self._precisao} estado=protegido>"

    # ------------------- API Pública -------------------

    @property
    def precisao(self) -> int:
        return self._precisao

    def extrair_duplas(self):
        """
        Retorna um dicionário com:
          - 'lista_f'          : blocos de 2 dígitos (strings "00".."99")
          - 'lista_mantissas'  : resíduos normalizados após cada extração (string)
          - 'lista_dig_ac'     : concatenação cumulativa dos blocos (string)
        """
        if self._mantissa_norm.is_zero():
            return {'lista_f': [], 'lista_mantissas': [], 'lista_dig_ac': []}

        lista_blocos = []
        lista_residuos = []
        lista_acum = []

        mant = +self._mantissa_norm   # cópia de trabalho
        acum = ""

        # Cada passo consome 2 dígitos significativos
        # (precisao + 2) // 2 passos para cobrir todos os dígitos, +2 de margem
        max_passos = (self._precisao + 2) // 2 + 2

        for _ in range(max_passos):
            if mant.is_zero():
                break
            if mant < 0:
                raise RuntimeError("Resíduo negativo -- erro na extração")

            # dois primeiros dígitos significativos (10..99)
            d2 = (mant * 10).to_integral_value(rounding=ROUND_FLOOR)   # ex.: 45
            prox = d2 / Decimal(10)                                    # 4.5

            # zoom + translação
            mant = (mant - prox) * 100

            # eliminação de ruído numérico residual
            if mant.copy_abs() < self._limiar:
                mant = Decimal(0)

            bloco = f"{int(d2):02d}"
            acum += bloco
            lista_blocos.append(bloco)
            lista_residuos.append(f"{mant.normalize():f}")
            lista_acum.append(acum)

        return {
            'lista_f': lista_blocos,
            'lista_mantissas': lista_residuos,
            'lista_dig_ac': lista_acum
        }

    def recompor(self, lista_blocos):
        """
        Recompõe o número (aproximação) apenas a partir dos blocos lidos.
        Não utiliza nem expõe o valor original.
        """
        if not lista_blocos:
            return "0e0"
        digits = ''.join(lista_blocos)
        mant_str = digits[0] + '.' + digits[1:]
        return f"{self._sinal}{mant_str}e{self._expoente}"


if __name__ == "__main__":
    dev = MZSDispositivo(precisao=20)
    d = dev.extrair_duplas()

    # Cabeçalho de impressão
    chaves = list(d.keys())
    pr = dev.precisao
    print(f"{'n':^10}", end=' ')
    for k in chaves:
        if k == 'lista_f':
            print(f"{k:10}", end=' ')
        else:
            print(f"{k:{pr + 3}}", end=' ')
    print()

    # Número de linhas
    m = min((len(v) for v in d.values()), default=0)

    # Tabela
    for i in range(m):
        print(f"{i:^10}", end=' ')
        for k in chaves:
            vals = d[k]
            if k == 'lista_f':
                print(f"{vals[i]:^10}", end=' ')
            else:
                print(f"{vals[i]:{pr + 3}}", end=' ')
        print('')

    # Resultado final
    print("\nResultado final:", dev.recompor(d.get('lista_f', [])))
