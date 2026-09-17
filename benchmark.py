import threading
import time

NUM_OPERACOES = 100000
REPETICOES = 5

saldo_conta = 0
lock_bancario = threading.Lock()


def depositar_inseguro():
    global saldo_conta
    for _ in range(NUM_OPERACOES):
        temp = saldo_conta
        temp = temp + 1
        saldo_conta = temp


def depositar_seguro():
    global saldo_conta
    for _ in range(NUM_OPERACOES):
        with lock_bancario:
            temp = saldo_conta
            temp = temp + 1
            saldo_conta = temp


def medir(funcao):
    global saldo_conta
    saldo_conta = 0
    t1 = threading.Thread(target=funcao, name="Thread-Caixa-1")
    t2 = threading.Thread(target=funcao, name="Thread-App-2")
    inicio = time.perf_counter()
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    return time.perf_counter() - inicio, saldo_conta


def main():
    print(f"[*] {REPETICOES} repeticoes | {NUM_OPERACOES} operacoes por thread | 2 threads\n")
    resultados = {}

    for rotulo, funcao in (("SEM LOCK", depositar_inseguro), ("COM LOCK", depositar_seguro)):
        tempos = []
        for i in range(1, REPETICOES + 1):
            tempo, saldo = medir(funcao)
            tempos.append(tempo)
            print(f"  {rotulo} | rodada {i}: {tempo:.4f} s | saldo = {saldo}")
        resultados[rotulo] = sum(tempos) / len(tempos)
        print(f"  {rotulo} | MEDIA: {resultados[rotulo]:.4f} s\n")

    sem, com = resultados["SEM LOCK"], resultados["COM LOCK"]
    print(f"[*] Overhead do Mutex: {com / sem:.2f}x mais lento "
          f"(+{(com - sem) * 1000:.1f} ms em {NUM_OPERACOES * 2} operacoes)")
    print(f"[*] Custo medio por aquisicao/liberacao de lock: "
          f"{((com - sem) / (NUM_OPERACOES * 2)) * 1e6:.3f} microssegundos")


if __name__ == "__main__":
    main()
