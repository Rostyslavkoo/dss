# Швидкий старт: Логічні Годинники

## Установка

Проект вже інтегрований у структуру DSS. Просто запустіть:

```bash
python test_clocks.py      # Запустити тести
python demo_clocks.py      # Запустити демонстрацію
```

## Базовий приклад

### 1. Використання Lamport Clock

```python
from scheduler.clocks.lamport_clock import LamportClock

# Створити годинник
clock = LamportClock()

# Внутрішня подія
clock.increment_internal()
print(f"Після внутрішньої события: {clock.get_timestamp()}")  # 1

# Відправка повідомлення
ts = clock.send_timestamp()
print(f"Відправлена мітка часу: {ts}")  # 2

# Отримання повідомлення з іншого процесу
clock.receive_timestamp(5)
print(f"Після отримання: {clock.get_timestamp()}")  # 6
```

### 2. Використання Vector Clock

```python
from scheduler.clocks.vector_clock import VectorClock

# Створити вектор для 3 процесів
vc = VectorClock(process_id=0, num_processes=3)

# Внутрішня подія
vc.increment_internal()
print(f"Після события: {vc.get_timestamp()}")  # [1, 0, 0]

# Отримання вектора від іншого процесу
received = [2, 1, 0]
vc.receive_timestamp(received)
print(f"Після отримання: {vc.get_timestamp()}")  # [2, 1, 1]

# Перевірити причинно-наслідкові зв'язки
v1 = [1, 0, 0]
v2 = [2, 1, 0]
print(f"v1 -> v2: {vc.happened_before(v1)}")  # False (vc has [2,1,1])

vc2 = VectorClock(1, 3)
vc2.receive_timestamp(v1)
print(f"v1 -> v2: {vc2.happened_before(v2)}")  # True
```

### 3. Використання NetworkWithClocks

```python
from scheduler.implementation.network_with_clocks import NetworkWithClocks

# Створити мережу з 4 вузлами
network = NetworkWithClocks(num_nodes=4)

# Отримати вузли
node0 = network.clock_nodes[0]
node1 = network.clock_nodes[1]
node2 = network.clock_nodes[2]

# Відправити повідомлення
msg = node0.send_message_to(node1.node_id, "Hello")
node1.process_action(msg)

# Продовжити ланцюг
msg2 = node1.send_message_to(node2.node_id, "Relay")
node2.process_action(msg2)

# Вивести результати
print("Clock Values:")
network.print_clocks()

print("\nEvent History:")
network.print_events()
```

## Часто використовувані операції

### Отримати поточну мітку часу

```python
lamport_ts = node.lamport_clock.get_timestamp()
vector_ts = node.vector_clock.get_timestamp()
```

### Перевірити причинно-наслідковий зв'язок

```python
if node1.vector_clock.happened_before(node2_vc):
    print("Event at Node1 caused Event at Node2")

if node1.vector_clock.concurrent_with(node2_vc):
    print("Events are concurrent")
```

### Відправити повідомлення з мітками часу

```python
msg = node1.send_message_to(node2.node_id, data)
# msg автоматично містить поточні мітки часу
node2.process_action(msg)
```

### Отримати інформацію про вузол

```python
info = node.get_clock_info()
# {'lamport': 5, 'vector': [1, 3, 2, 0]}

events = node.get_events()
# [{'type': 'receive', 'from': 'xxx', 'lamport': 2, 'vector': [...], 'data': {...}}]
```

## Конфігурація

### Увімкнути/Вимкнути годинники

```python
# Тільки Lamport Clock
node = NodeWithClocks(..., enable_lamport=True, enable_vector=False)

# Тільки Vector Clock
node = NodeWithClocks(..., enable_lamport=False, enable_vector=True)

# Обидва (за замовчуванням)
node = NodeWithClocks(..., enable_lamport=True, enable_vector=True)
```

### Кількість вузлів у мережі

```python
# 4 вузли (за замовчуванням)
network = NetworkWithClocks()

# 8 вузлів
network = NetworkWithClocks(num_nodes=8)

# Доступ до всіх вузлів
for i, node in enumerate(network.clock_nodes):
    print(f"Node {i}: {node}")
```

## Основні концепції

### Lamport Clock

- **Коли використовувати**: Коли потрібна просто лінійна упорядкованість подій
- **Переваги**: О(1) накладні витрати, просто реалізація
- **Недоліки**: Не розрізняє причинність та конкурентність

```
Приклад часової лінії:
Process A: [1] ---> [3]
Process B:   [2] -> [4]
Process C:         [5]
Упорядкування: 1 < 2 < 3 < 4 < 5
```

### Vector Clock

- **Коли використовувати**: Коли потрібна інформація про причинність
- **Переваги**: Точне визначення причинно-наслідкових залежностей
- **Недоліки**: O(n) накладні витрати, де n = кількість процесів

```
Приклад:
Process A: [1,0,0] -> [2,0,0]
Process B: [2,1,0] -> [2,2,0]
Process C: [2,2,1]

A[2,0,0] < B[2,2,0]? Так (2<=2, 0<=2, 0<=0 і не рівні)
A[2,0,0] || C[2,2,1]? Ні (послідовно через B)
```

## Налагодження

### Вивести детальну історію

```python
network.print_clocks()   # Поточні значення
network.print_events()   # Ціла історія подій
```

### Розглянути окремий вузол

```python
node = network.clock_nodes[0]
print(f"Lamport: {node.lamport_clock}")
print(f"Vector: {node.vector_clock}")
print(f"Events: {node.get_events()}")
```

## Наступні кроки

1. Читайте `LOGICAL_CLOCKS_README.md` для деталей
2. Дивіться `INTEGRATION_GUIDE.md` для розширених операцій
3. Запустіть `test_clocks.py` для самої дообави
4. Запустіть `demo_clocks.py` для інтерактивних прикладів

## Документація

- **LOGICAL_CLOCKS_README.md** - Повна теорія та практика
- **INTEGRATION_GUIDE.md** - API та інтеграція
- **IMPLEMENTATION_SUMMARY.md** - Огляд реалізації

Успіхів у роботі з логічними годинниками!
