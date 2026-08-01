// SUBMISSAO DE EXEMPLO -- FICTICIA. Nao corresponde a montagem real alguma. Existe para demonstrar o formato esperado.
//
// Esboco do laco de controle. O valor de sqrt(2) NAO aparece em ponto
// algum deste arquivo -- nem em assercao de depuracao, nem em valor
// inicial de busca. E a exigencia de blindagem do alvo: firmware que
// consulte a resposta converte a demonstracao em tautologia.

#include <stdint.h>

// coeficientes acumulados, em inteiros exatos (aritmetica de precisao
// arbitraria implementada em software; ponto flutuante nao serve)
static Big A, B, C;

void setup() {
  Serial.begin(115200);
  problema_inicial(&A, &B, &C);   // x^2 - 2 = 0
}

void loop() {
  deflacao_afim(&A, &B, &C);      // subtrai a parte conhecida (exato)
  reescalar(&A, &B, &C);          // traz o residuo a ordem de volts

  dac_escrever(coef_normalizado(B, C));
  aguardar_acomodacao();

  float m[3] = { ler_monitor(0), ler_monitor(1), ler_monitor(2) };
  int digito;
  uint8_t tentativas = 0;
  do {
    digito = maioria_de_tres(m);  // erros descorrelacionados: ver enunciado
    tentativas++;
  } while (digito < 0 && tentativas < 8);

  registrar(digito, tentativas, m);
  acumular(digito, &A, &B, &C);
}
