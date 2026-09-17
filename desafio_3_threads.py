import threading
import time

saldo_conta = 0
NUM_OPERACOES = 100000
VALOR_OPERACAO = 1
lock_bancario = threading.Lock()


def depositar():
    global saldo_conta
    for _ in range(NUM_OPERACOES):
        with lock_bancario:
            temp = saldo_conta
            temp = temp + VALOR_OPERACAO
            saldo_conta = temp


def sacar():
    global saldo_conta
    for _ in range(NUM_OPERACOES):
        with lock_bancario:
            temp = saldo_conta
            temp = temp - VALOR_OPERACAO
            saldo_conta = temp


def main():
    global saldo_conta
    print(f"[*] Saldo Inicial:   {saldo_conta}")

    threads = [
        threading.Thread(target=depositar, name="Thread-Deposito-1"),
        threading.Thread(target=depositar, name="Thread-Deposito-2"),
        threading.Thread(target=sacar, name="Thread-Saque-1"),
    ]

    inicio = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    fim = time.time()

    saldo_esperado = (2 * NUM_OPERACOES * VALOR_OPERACAO) - (NUM_OPERACOES * VALOR_OPERACAO)

    print(f"[*] Threads:         {', '.join(t.name for t in threads)}")
    print(f"[*] Saldo Esperado:  {saldo_esperado}")
    print(f"[*] Saldo Obtido:    {saldo_conta}")
    print(f"[*] Tempo de Execucao: {fim - inicio:.4f} s")

    if saldo_conta == saldo_esperado:
        print("\n[OK] Resultado integro mesmo com 3 threads concorrentes.")
    else:
        print("\n[ALERTA] Inconsistencia detectada!")


if __name__ == "__main__":
    main()
