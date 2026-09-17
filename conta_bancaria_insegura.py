import threading
import time

saldo_conta = 0
NUM_OPERACOES = 100000


def depositar():
    global saldo_conta
    for _ in range(NUM_OPERACOES):
        temp = saldo_conta
        temp = temp + 1
        saldo_conta = temp


def main():
    global saldo_conta
    print(f"[*] Saldo Inicial:   {saldo_conta}")

    t1 = threading.Thread(target=depositar, name="Thread-Caixa-1")
    t2 = threading.Thread(target=depositar, name="Thread-App-2")

    inicio = time.time()
    t1.start()
    t2.start()

    t1.join()
    t2.join()
    fim = time.time()

    saldo_esperado = NUM_OPERACOES * 2
    print(f"[*] Saldo Esperado:  {saldo_esperado}")
    print(f"[!] Saldo Obtido:    {saldo_conta}")
    print(f"[*] Perda de dados:  {saldo_esperado - saldo_conta} operacoes perdidas")
    print(f"[*] Tempo de Execucao: {fim - inicio:.4f} s")

    if saldo_conta != saldo_esperado:
        print("\n[ALERTA] Condicao de Corrida detectada! Houve perda de dados.")
    else:
        print("\n[OK] Resultado integro.")


if __name__ == "__main__":
    main()
