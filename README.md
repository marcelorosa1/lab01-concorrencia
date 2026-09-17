# Laboratório 01 — Concorrência, Threads e Condição de Corrida

**Disciplina:** Sistemas Operacionais (2026.2) — 4º Semestre, ADS / UNIFADESA
**Docente:** Prof. Esp. Rodrigo Martins Sousa
**Avaliação:** 1,0 ponto na N1 — Entrega até 01/10/2026
**Aluno(a):** _preencher_

---

## 1. Objetivo

Provocar intencionalmente uma **condição de corrida** (*race condition*) sobre uma variável
compartilhada por múltiplas *threads*, entender por que o incremento de um contador **não é
atômico** no nível da CPU, e corrigir o problema com a primitiva de sincronização do sistema
operacional: o **Mutex (`threading.Lock`)**.

## 2. Ambiente de execução

Todos os testes foram executados **dentro de uma máquina virtual Linux**, não no sistema
hospedeiro:

```
Sistema...: Ubuntu 26.04 LTS
Kernel....: 7.0.0-30-generic
Arquitetura: x86_64
CPUs......: 1
Python....: 3.14.4 (CPython)
Hostname..: ubuntu
Virtualizador: Oracle VirtualBox
```

O arquivo [`evidencias/ambiente.txt`](evidencias/ambiente.txt) contém essa coleta feita pelo
próprio script de execução, com data e hora.

> **Nota sobre a VM ter apenas 1 vCPU:** isso **não invalida** o experimento — pelo contrário,
> reforça o conceito. Com um único núcleo não existe paralelismo real: as *threads* são
> multiplexadas pelo escalonador do SO por meio de **troca de contexto**. Ou seja, a condição de
> corrida demonstrada aqui não depende de múltiplos processadores, ela nasce exclusivamente da
> **preempção** — que é exatamente o que o roteiro pede para compreender.

## 3. Estrutura do repositório

```
.
├── conta_bancaria_insegura.py     # Parte 1 — seção crítica desprotegida
├── conta_bancaria_segura.py       # Parte 2 — exclusão mútua com Mutex (Lock)
├── desafio_3_threads.py           # Bônus — 2 threads de depósito + 1 de saque
├── race_condition_evidente.py     # Complementar — torna a race visível no CPython
├── benchmark.py                   # Auxiliar — mede o overhead do Lock (Questão 2)
├── executar_tudo.sh               # Executa toda a bateria e salva as evidências
├── evidencias/
│   ├── ambiente.txt
│   ├── saida_insegura.txt
│   ├── saida_segura.txt
│   ├── saida_desafio_3_threads.txt
│   ├── saida_race_evidente.txt
│   ├── saida_benchmark.txt
│   └── bytecode_secao_critica.txt
└── README.md
```

## 4. Como executar

Dentro da máquina virtual:

```bash
bash executar_tudo.sh
```

Ou individualmente:

```bash
python3 conta_bancaria_insegura.py
python3 conta_bancaria_segura.py
python3 desafio_3_threads.py
python3 race_condition_evidente.py
python3 benchmark.py
```

---

## 5. Parte 1 — Provocando a condição de corrida

Duas *threads* (`Thread-Caixa-1` e `Thread-App-2`) executam 100.000 incrementos cada sobre a
variável global `saldo_conta`, usando a sequência **ler → somar → escrever**, sem nenhuma
proteção. O saldo esperado é 200.000.

Script executado 3 vezes na VM ([`evidencias/saida_insegura.txt`](evidencias/saida_insegura.txt)):

| Execução | Saldo esperado | Saldo obtido | Perda | Tempo |
|---|---|---|---|---|
| 1 | 200.000 | 200.000 | 0 | 0,1253 s |
| 2 | 200.000 | 200.000 | 0 | 0,1363 s |
| 3 | 200.000 | 200.000 | 0 | 0,1161 s |

### 5.1. Por que o resultado saiu íntegro — e por que isso não significa que o código é seguro

O roteiro prevê que "o valor final quase nunca atinge 200.000". **No Ubuntu 26.04 com CPython
3.14.4 o resultado saiu correto nas três execuções.** O mesmo teste repetido no host Windows com
CPython 3.10 deu o mesmo resultado, então não é particularidade de uma versão isolada. A
explicação está no interpretador:

- O CPython usa a **GIL** (*Global Interpreter Lock*): apenas uma *thread* executa bytecode por
  vez, mesmo em máquinas com vários núcleos.
- A troca de *thread* **não acontece em qualquer instrução**. O interpretador só avalia o pedido
  de liberação da GIL (*eval breaker*) em pontos determinados do laço de execução — na prática, no
  **salto de volta do `for`** e em chamadas que liberam a GIL (I/O, `sleep`, `time`).
- Como as instruções da seção crítica ficam **entre dois saltos de laço**, a preempção quase nunca
  cai no meio delas e a atualização perdida não se manifesta.

Ou seja: **o defeito continua existindo, mas o escalonamento do interpretador o esconde**. Basta
existir qualquer ponto de preempção dentro da seção crítica — uma chamada de função, uma operação
de I/O, um acesso a banco de dados, ou seja, o que acontece em código real — para a perda de dados
aparecer.

O script `race_condition_evidente.py` prova isso: mantém a mesma lógica não-atômica, mas insere um
ponto de troca de contexto (`time.sleep(0)`) entre a leitura e a escrita, e roda a mesma carga
**sem lock** e **com lock**
([`evidencias/saida_race_evidente.txt`](evidencias/saida_race_evidente.txt)):

```
--- SEM LOCK (secao critica desprotegida) ---
[*] Saldo Esperado:  100000
[!] Saldo Obtido:    50000
[*] Operacoes perdidas: 50000
[*] Tempo de Execucao:  24.0381 s
[ALERTA] Condicao de Corrida detectada! Houve perda de dados.

--- COM LOCK (exclusao mutua) ---
[*] Saldo Esperado:  100000
[!] Saldo Obtido:    100000
[*] Operacoes perdidas: 0
[*] Tempo de Execucao:  32.2996 s
[OK] Resultado integro.
```

**50% das operações foram perdidas** sem o lock, e **nenhuma** com o lock. Está demonstrado que a
seção crítica desprotegida é incorreta e que o Mutex é o que garante a integridade.

---

## 6. Parte 2 — Exclusão mútua com Mutex (Lock)

Mesma carga de trabalho, com a seção crítica inteira protegida por `with lock_bancario:`.
Script executado 3 vezes na VM ([`evidencias/saida_segura.txt`](evidencias/saida_segura.txt)):

| Execução | Saldo esperado | Saldo obtido | Tempo |
|---|---|---|---|
| 1 | 200.000 | 200.000 | 0,4347 s |
| 2 | 200.000 | 200.000 | 0,4606 s |
| 3 | 200.000 | 200.000 | 1,0361 s |

Resultado **sempre íntegro**, em todas as execuções — que é justamente a garantia do mutex: o
resultado deixa de depender da ordem de escalonamento escolhida pelo SO.

---

## 7. Questões do relatório

### Questão 1 — Troca de contexto e atomicidade

As três linhas abaixo parecem uma operação única para o programador, mas são **uma sequência de
operações distintas** para a CPU:

```python
temp = saldo_conta     # LEITURA
temp = temp + 1        # MODIFICAÇÃO
saldo_conta = temp     # ESCRITA
```

Nenhum processador de arquitetura *load/store* (ARM, RISC-V) — e nem mesmo o x86, quando o
compilador ou o interpretador não emite uma instrução atômica específica — soma 1 a uma posição de
memória em um único passo indivisível. O ciclo obrigatório é:

1. **LOAD** — copiar o valor da memória (RAM/cache) para um registrador;
2. **ADD** — somar 1 dentro do registrador (a memória ainda guarda o valor antigo);
3. **STORE** — gravar o valor do registrador de volta na memória.

No CPython isso fica explícito no bytecode gerado na própria VM
([`evidencias/bytecode_secao_critica.txt`](evidencias/bytecode_secao_critica.txt)), que mostra
**oito instruções** para o que parecia uma operação só:

```
  3   LOAD_GLOBAL        (saldo_conta)     <-- LEITURA
      STORE_FAST         (temp)

  4   LOAD_FAST_BORROW   (temp)
      LOAD_SMALL_INT     1
      BINARY_OP          (+)               <-- MODIFICAÇÃO
      STORE_FAST         (temp)

  5   LOAD_FAST_BORROW   (temp)
      STORE_GLOBAL       (saldo_conta)     <-- ESCRITA
```

**Por que isso quebra:** o escalonador do SO é *preemptivo*. Ele pode interromper uma *thread* a
qualquer momento — no fim do seu *quantum* (fatia de tempo), numa interrupção de hardware, ou
quando uma *thread* de maior prioridade fica pronta. Se a interrupção ocorrer **entre o LOAD e o
STORE**, a *thread* interrompida tem o valor já lido salvo no seu contexto (registradores e pilha,
guardados no TCB — *Thread Control Block*). Quando ela volta a executar, o SO **restaura esse
contexto** e a *thread* continua de onde parou, escrevendo o valor **obsoleto** que carregava —
sobrescrevendo silenciosamente tudo o que a outra *thread* gravou nesse intervalo.

Exemplo de intercalação que perde um depósito:

| Tempo | Thread-Caixa-1 | Thread-App-2 | `saldo_conta` |
|---|---|---|---|
| t1 | lê saldo → temp = 100 | — | 100 |
| t2 | *(preempção — contexto salvo com temp = 100)* | — | 100 |
| t3 | — | lê saldo → temp = 100 | 100 |
| t4 | — | soma e escreve 101 | **101** |
| t5 | *(contexto restaurado, temp = 100)* | — | 101 |
| t6 | soma e escreve 101 | — | **101** ← um depósito sumiu |

Duas operações de depósito foram executadas, mas o saldo subiu apenas 1. É a chamada **atualização
perdida** (*lost update*). O trecho entre o LOAD e o STORE é a **seção crítica**, e o resultado do
programa passa a depender da ordem em que o escalonador decidiu alternar as *threads* — algo que o
programador não controla. Daí o nome *condição de corrida*: as *threads* "correm" pelo recurso e o
resultado depende de quem chega primeiro.

Vale reforçar: esta VM tem **um único núcleo**. Não houve execução simultânea em nenhum momento —
a corrupção de dados demonstrada na seção 5.1 foi causada **apenas pela troca de contexto**, o que
derruba a intuição comum de que race conditions só acontecem em máquinas multicore.

### Questão 2 — Custo do Lock (overhead)

Medição feita na VM com 5 repetições de cada versão, dentro do mesmo processo (`benchmark.py`,
[`evidencias/saida_benchmark.txt`](evidencias/saida_benchmark.txt)), com 100.000 operações por
*thread* e 2 *threads*:

| Versão | Rodadas (s) | Média |
|---|---|---|
| **Sem lock** | 0,1136 / 0,1229 / 0,1276 / 0,1293 / 0,1108 | **0,1208 s** |
| **Com lock** | 0,1705 / 0,3365 / 0,2208 / 0,2563 / 0,2167 | **0,2401 s** |

> **Resultado: a versão com Mutex é ~1,99x mais lenta** (+119,3 ms em 200.000 operações), o que dá
> um custo médio de **≈ 0,6 microssegundo por par aquisição/liberação de lock**.

**De onde vem essa sobrecarga:**

1. **Instruções atômicas de hardware.** Adquirir um mutex exige uma operação *read-modify-write*
   atômica (`LOCK CMPXCHG` / *compare-and-swap*, *test-and-set*). Essa instrução trava a linha de
   cache ou o barramento, não pode ser reordenada pela CPU e impõe uma **barreira de memória** —
   inibindo otimizações de pipeline, execução especulativa e reordenamento que tornariam o código
   rápido.
2. **Chamadas ao sistema e bloqueio.** Quando o lock já está tomado, a *thread* não pode
   prosseguir: o SO a retira do estado *Running* e a coloca em **Blocked**, na fila de espera do
   mutex. Isso envolve chamada ao *kernel* (no Linux, `futex`), salvar o contexto, escalonar outra
   *thread* e, mais tarde, acordar e restaurar a que esperava. **Cada troca de contexto custa** — e
   ainda polui cache e TLB.
3. **Coerência de cache.** Em máquinas com vários núcleos, a variável do lock é disputada por
   todos eles: cada aquisição obriga o protocolo de coerência (MESI) a invalidar aquela linha de
   cache nos demais núcleos e transferi-la (*cache line bouncing*). Nesta VM de 1 vCPU esse custo
   específico não aparece — o que explica o overhead menor (1,99x) comparado ao medido no host
   Windows com 8 núcleos (2,61x).
4. **Serialização da concorrência.** Este é o custo conceitualmente mais importante: dentro da
   seção crítica **não existe paralelismo**. As *threads* passam a executar aquele trecho em fila
   indiana. Como neste laboratório a seção crítica é praticamente o corpo inteiro do laço, quase
   todo o programa foi serializado. É a **Lei de Amdahl** na prática: quanto maior a fração
   serializada do código, menor o ganho possível ao adicionar mais *threads*.
5. **Overhead do `with`.** Em Python soma-se ainda o custo do gerenciador de contexto
   (`__enter__` / `__exit__`), duas chamadas de método por iteração.

**Conclusão de engenharia:** o custo é o **preço da correção** — um resultado rápido e errado não
tem valor algum. Mas ele mostra por que a boa prática é manter a **seção crítica no menor escopo
possível**: só o que realmente toca o recurso compartilhado deve ficar dentro do lock. Cálculos,
validações, formatação e I/O devem ficar **fora** dele. Em cenários de leitura predominante,
alternativas menos custosas (operações atômicas, *read-write locks*, dados imutáveis ou filas como
`queue.Queue`) evitam boa parte desse overhead.

### Questão 3 — Desafio extra: 3 threads (2 depósitos + 1 saque)

Implementado em `desafio_3_threads.py`:

- `Thread-Deposito-1` → 100.000 depósitos de R$ 1,00
- `Thread-Deposito-2` → 100.000 depósitos de R$ 1,00
- `Thread-Saque-1` → 100.000 saques de R$ 1,00

Saldo final esperado: `(2 × 100.000) − (1 × 100.000)` = **100.000**.

Executado 3 vezes na VM
([`evidencias/saida_desafio_3_threads.txt`](evidencias/saida_desafio_3_threads.txt)):

| Execução | Saldo esperado | Saldo obtido | Tempo |
|---|---|---|---|
| 1 | 100.000 | 100.000 | 1,2886 s |
| 2 | 100.000 | 100.000 | 1,0891 s |
| 3 | 100.000 | 100.000 | 1,0727 s |

**Decisão de projeto — um único mutex para as três threads.** O recurso compartilhado é um só
(`saldo_conta`), logo a seção crítica é a mesma para depósito e saque e **as três *threads*
disputam o mesmo `lock_bancario`**. Usar um lock para depósitos e outro para saques *não*
resolveria nada: uma *thread* de depósito e uma de saque poderiam entrar simultaneamente na região
crítica, cada uma segurando um lock diferente, e a atualização perdida voltaria a ocorrer.

> **Regra geral:** o lock protege **o dado**, não a função. Todo caminho de código que lê e escreve
> o mesmo recurso compartilhado precisa passar pelo **mesmo** mutex.

Vale notar que a operação de saque tem exatamente o mesmo problema de atomicidade do depósito
(`ler → subtrair → escrever`), e que o resultado correto independe da ordem em que o SO escalonou
as três *threads* — exatamente o que a exclusão mútua garante.

---

## 8. Conclusão

| Cenário | Integridade | Desempenho |
|---|---|---|
| Sem sincronização (teste evidente) | ❌ Incorreto — 50.000 de 100.000 operações perdidas | 24,04 s |
| Com Mutex (mesmo teste) | ✅ Correto — 0 perdidas | 32,30 s |
| Sem lock (benchmark, 2 threads) | ⚠️ Correto por sorte do escalonamento | 0,1208 s |
| Com Mutex (benchmark, 2 threads) | ✅ Correto por garantia | 0,2401 s (1,99x) |
| Com Mutex (3 threads: depósito + saque) | ✅ Sempre correto | ~1,1 s |

Concorrência sem controle de acesso produz resultados **não determinísticos**: o programa pode
funcionar em dezenas de testes e falhar em produção, porque o defeito depende do escalonamento — e
o escalonamento muda com a carga da máquina, o número de núcleos e a versão do interpretador.
Foi exatamente o que aconteceu aqui: o script da Parte 1 "passou" três vezes seguidas e mesmo
assim está errado. A primitiva de sincronização do SO troca um pouco de desempenho por **correção
garantida**, e cabe ao desenvolvedor reduzir ao mínimo o tamanho da seção crítica para pagar o
menor preço possível por essa garantia.

---

## 9. Evidências

As saídas completas de todas as execuções, geradas dentro da máquina virtual, estão em
[`evidencias/`](evidencias/).
_Anexar aqui também as capturas de tela do terminal da VM._
