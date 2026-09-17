#!/usr/bin/env bash
set -u

PY=$(command -v python3 || command -v python)
DIR="$(cd "$(dirname "$0")" && pwd)"
EV="$DIR/evidencias"
mkdir -p "$EV"

echo "=================================================="
echo " LAB 01 - CONCORRENCIA, THREADS E RACE CONDITION"
echo "=================================================="
{
    echo "Data......: $(date '+%d/%m/%Y %H:%M:%S')"
    echo "Sistema...: $(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME" || uname -s)"
    echo "Kernel....: $(uname -r)"
    echo "Arquitet..: $(uname -m)"
    echo "CPUs......: $(nproc)"
    echo "Python....: $($PY --version 2>&1)"
    echo "Hostname..: $(hostname)"
} | tee "$EV/ambiente.txt"
echo

echo "### PARTE 1 - CONTA BANCARIA INSEGURA (3 execucoes) ###"
{
    for i in 1 2 3; do
        echo "===== EXECUCAO $i ====="
        $PY "$DIR/conta_bancaria_insegura.py"
        echo
    done
} 2>&1 | tee "$EV/saida_insegura.txt"

echo "### PARTE 2 - CONTA BANCARIA SEGURA COM MUTEX (3 execucoes) ###"
{
    for i in 1 2 3; do
        echo "===== EXECUCAO $i ====="
        $PY "$DIR/conta_bancaria_segura.py"
        echo
    done
} 2>&1 | tee "$EV/saida_segura.txt"

echo "### DESAFIO EXTRA - 3 THREADS (3 execucoes) ###"
{
    for i in 1 2 3; do
        echo "===== EXECUCAO $i ====="
        $PY "$DIR/desafio_3_threads.py"
        echo
    done
} 2>&1 | tee "$EV/saida_desafio_3_threads.txt"

echo "### RACE CONDITION EVIDENTE (sem lock x com lock) ###"
$PY "$DIR/race_condition_evidente.py" 2>&1 | tee "$EV/saida_race_evidente.txt"
echo

echo "### BENCHMARK - OVERHEAD DO MUTEX ###"
$PY "$DIR/benchmark.py" 2>&1 | tee "$EV/saida_benchmark.txt"
echo

echo "### BYTECODE DA SECAO CRITICA ###"
$PY - << 'PYEOF' 2>&1 | tee "$EV/bytecode_secao_critica.txt"
import dis, sys
src = "def depositar():\n    global saldo_conta\n    temp = saldo_conta\n    temp = temp + 1\n    saldo_conta = temp\n"
ns = {}
exec(compile(src, "<lab01>", "exec"), ns)
print("Python", sys.version.split()[0])
print()
dis.dis(ns["depositar"])
PYEOF
echo

echo "=================================================="
echo " CONCLUIDO. Evidencias salvas em: $EV"
echo "=================================================="
ls -la "$EV"
