import threading
import time

NUM_OPERACOES = 50000

saldo_conta = 0
lock_bancario = threading.Lock()


def depositar_inseguro():
    global saldo_conta
    for _ in range(NUM_OPERACOES):
        temp = saldo_conta
        time.sleep(0)
        saldo_conta = temp + 1


def depositar_seguro():
    global saldo_conta
    for _ in range(NUM_OPERACOES):
        with lock_bancario:
            temp = saldo_conta
            time.sleep(0)
            saldo_conta = temp + 1


def executar(funcao, rotulo):
    global saldo_conta
    saldo_conta = 0

    t1 = threading.Thread(target=funcao, name="Thread-Caixa-1")
    t2 = threading.Thread(target=funcao, name="Thread-App-2")

    inicio = time.time()
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    fim = time.time()

    esperado = NUM_OPERACOES * 2
    print(f"--- {rotulo} ---")
    print(f"[*] Saldo Esperado:  {esperado}")
    print(f"[!] Saldo Obtido:    {saldo_conta}")
    print(f"[*] Operacoes perdidas: {esperado - saldo_conta}")
    print(f"[*] Tempo de Execucao:  {fim - inicio:.4f} s")
    if saldo_conta != esperado:
        print("[ALERTA] Condicao de Corrida detectada! Houve perda de dados.\n")
    else:
        print("[OK] Resultado integro.\n")


def main():
    print(f"[*] Operacoes por thread: {NUM_OPERACOES} | Threads: 2\n")
    executar(depositar_inseguro, "SEM LOCK (secao critica desprotegida)")
    executar(depositar_seguro, "COM LOCK (exclusao mutua)")


if __name__ == "__main__":
    main()
