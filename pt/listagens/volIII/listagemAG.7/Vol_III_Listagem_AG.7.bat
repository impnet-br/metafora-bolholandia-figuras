@echo off
rem ------------------
rem Nome do Fonte:    run_montecarlo.bat
rem Autor:            Antonio Ferrão Neto
rem Data de criação:  2025-08-06
rem Última alteração: 2025-08-06
rem
rem Descrição:
rem Script .BAT de exemplo para chamadas de Monte Carlo para
rem múltiplos valores dos parâmetros.
rem
rem Execução:
rem > run_montecarlo.bat
rem ------------------
setlocal EnableExtensions EnableDelayedExpansion

rem === Configurações fixas ===
set "PY=python"
set "SCRIPT=mzs_simulacao.py"
set "PREC=20"
set "N_RUNS=20000"
set "MC_SEED0=20250809"

if not exist "logs" mkdir "logs"

for %%R in (1 2 3 4 5) do (
  rem p_second = 0.01 -> p_both: 0.001
  call :RUNSET 0.01 "0.001" %%R
  rem p_second = 0.02 -> p_both: 0.001 0.002
  call :RUNSET 0.02 "0.001 0.002" %%R
  rem p_second = 0.03 -> p_both: 0.001 0.002 0.003
  call :RUNSET 0.03 "0.001 0.002 0.003" %%R
  rem p_second = 0.04 -> p_both: 0.001 0.002 0.003 0.004
  call :RUNSET 0.04 "0.001 0.002 0.003 0.004" %%R
  rem p_second = 0.05 -> p_both: 0.001 0.002 0.003 0.004 0.005
  call :RUNSET 0.05 "0.001 0.002 0.003 0.004 0.005" %%R
  rem p_second = 0.06 -> p_both: 0.001 0.002 0.003 0.004 0.005 0.006
  call :RUNSET 0.06 "0.001 0.002 0.003 0.004 0.005 0.006" %%R
  rem p_second = 0.07 -> p_both: 0.001 0.002 0.003 0.004 0.005 0.006 0.007
  call :RUNSET 0.07 "0.001 0.002 0.003 0.004 0.005 0.006 0.007" %%R
  rem p_second = 0.08 -> p_both: 0.001 0.002 0.003 0.004 0.005 0.006 0.007 0.008
  call :RUNSET 0.08 "0.001 0.002 0.003 0.004 0.005 0.006 0.007 0.008" %%R
  rem p_second = 0.09 -> p_both: 0.001 0.002 0.003 0.004 0.005 0.006 0.007 0.008 0.009
  call :RUNSET 0.09 "0.001 0.002 0.003 0.004 0.005 0.006 0.007 0.008 0.009" %%R
  rem p_second = 0.10 -> p_both: 0.001 ... 0.010
  call :RUNSET 0.10 "0.001 0.002 0.003 0.004 0.005 0.006 0.007 0.008 0.009 0.010" %%R
)

echo.
echo [OK] Todas as simulacoes foram enfileiradas. Logs em .\logs\
goto :eof


:RUNSET
rem %1 = p_second   (ex.: 0.05)
rem %2 = lista p_both (ex.: "0.001 0.002 0.003 0.004 0.005")
rem %3 = retries
set "PSECOND=%~1"
set "PBOTHLIST=%~2"
set "RETRIES=%~3"

for %%B in (%PBOTHLIST%) do (
  set "PBOTH=%%B"
  rem Sanitiza para nome de arquivo: troca . por p
  set "S_P=%PSECOND:.=p%"
  set "B_P=!PBOTH:.=p!"
  set "LOG=logs\mc_prec%PREC%_ps%S_P%_pb%B_P%_r%RETRIES%.txt"

  echo Executando: p_second=%PSECOND%  p_both=!PBOTH!  retries=%RETRIES%
  %PY% %SCRIPT% --prec %PREC% --p_second %PSECOND% --p_both !PBOTH! --retries %RETRIES% --mc --n_runs %N_RUNS% --mc_seed0 %MC_SEED0% > "!LOG!"
)
goto :eof
