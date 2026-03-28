# Інтеграція Логічних Годинників

## Експорт

Усі модулі логічних годинників експортуються через пакет `scheduler.clocks`:

```python
from scheduler.clocks.lamport_clock import LamportClock
from scheduler.clocks.vector_clock import VectorClock
from scheduler.implementation.node_with_clocks import NodeWithClocks
from scheduler.implementation.network_with_clocks import NetworkWithClocks
from scheduler.core.timestamped_action import TimestampedAction
```

## Використання з існуючою системою

Для інтеграції логічних годинників у існуючу мережу:

### Крок 1: Замінити Node на NodeWithClocks

```python
# Раніше:
from scheduler.implementation.node import Node

# Тепер:
from scheduler.implementation.node_with_clocks import NodeWithClocks

node = NodeWithClocks(
    node_id=uuid.uuid4(),
    neighbors=[...],
    process_index=0,
    num_processes=total_nodes,
    enable_lamport=True,
    enable_vector=True
)
```

### Крок 2: Замінити Network на NetworkWithClocks

```python
# Раніше:
from scheduler.implementation.current_network import CurrentNetwork

# Тепер:
from scheduler.implementation.network_with_clocks import NetworkWithClocks

network = NetworkWithClocks(
    num_nodes=4,
    enable_lamport=True,
    enable_vector=True
)
```

### Крок 3: Використовувати TimestampedAction

```python
from scheduler.core.timestamped_action import TimestampedAction

# Замість звичайного Action використовувати TimestampedAction
msg = TimestampedAction(
    data={"operation": "write", "value": 42},
    sender_id=sender_node.node_id,
    receiver_id=receiver_node.node_id,
    lamport_timestamp=sender_node.lamport_clock.send_timestamp(),
    vector_timestamp=sender_node.vector_clock.send_timestamp()
)

# Процесувати повідомлення
response = receiver_node.process_action(msg)
```

## Конфігурація

### Параметри NodeWithClocks

| Параметр | Тип | Опис |
|----------|-----|------|
| `node_id` | UUID | Унікальний ідентифікатор вузла |
| `neighbors` | List[UUID] | Список сусідніх вузлів |
| `process_index` | int | Індекс процесу (для векторного годинника) |
| `num_processes` | int | Загальна кількість процесів |
| `enable_lamport` | bool | Увімкнути Lamport Clock |
| `enable_vector` | bool | Увімкнути Vector Clock |

### Параметри NetworkWithClocks

| Параметр | Тип | Опис |
|----------|-----|------|
| `num_nodes` | int | Кількість вузлів у мережі (за замовчуванням 4) |
| `enable_lamport` | bool | Увімкнути Lamport Clock на всіх вузлах |
| `enable_vector` | bool | Увімкнути Vector Clock на всіх вузлах |

## API Методів

### LamportClock

```python
clock = LamportClock(initial_value=0)

clock.increment_internal()        # Інкремент на внутрішню подію
timestamp = clock.send_timestamp() # Отримати мітку часу для відправки
clock.receive_timestamp(ts)       # Оновити на отримання повідомлення
value = clock.get_timestamp()     # Отримати поточне значення
```

### VectorClock

```python
vc = VectorClock(process_id=0, num_processes=4)

vc.increment_internal()            # Інкремент на внутрішню подію
timestamp = vc.send_timestamp()    # Отримати вектор для відправки
vc.receive_timestamp(vector)       # Оновити вектор на отримання
vector = vc.get_timestamp()        # Отримати поточний вектор

# Аналіз причинно-наслідкових зв'язків
is_before = vc.happened_before(other_vector)  # Перевірка VC(self) < VC(other)
is_concurrent = vc.concurrent_with(other_vector)  # Перевірка паралельності
```

### NodeWithClocks

```python
node = NodeWithClocks(...)

# Відправка повідомлення
msg = node.send_message_to(neighbor_id, data)

# Обробка повідомлення
response = node.process_action(message)

# Отримання інформації про годинники
info = node.get_clock_info()  # {'lamport': int, 'vector': List[int]}

# Отримання історії подій
events = node.get_events()  # List[dict]
```

### NetworkWithClocks

```python
network = NetworkWithClocks(num_nodes=4)

# Доступ до вузлів
node = network.clock_nodes[0]
node = network.get_node_by_index(0)

# Друк інформації
network.print_clocks()   # Вивести поточні значення годинників
network.print_events()   # Вивести історію подій
```

## Приклади

### Приклад 1: Простий ланцюг повідомлень

```python
from scheduler.implementation.network_with_clocks import NetworkWithClocks

# Створити мережу
network = NetworkWithClocks(num_nodes=3)
nodes = network.clock_nodes

# Відправити повідомлення по ланцюгу
msg1 = nodes[0].send_message_to(nodes[1].node_id, "msg1")
nodes[1].process_action(msg1)

msg2 = nodes[1].send_message_to(nodes[2].node_id, "msg2")
nodes[2].process_action(msg2)

# Вивести результати
network.print_clocks()
network.print_events()
```

### Приклад 2: Аналіз причинно-наслідкових зв'язків

```python
from scheduler.clocks.vector_clock import VectorClock

vc1 = VectorClock(0, 3)
vc2 = VectorClock(1, 3)
vc3 = VectorClock(2, 3)

# Процес 1 посилає до Процесу 2
ts1 = vc1.send_timestamp()  # [1, 0, 0]
vc2.receive_timestamp(ts1)   # [1, 1, 0]

# Процес 2 посилає до Процесу 3
ts2 = vc2.send_timestamp()  # [1, 2, 0]
vc3.receive_timestamp(ts2)   # [1, 2, 1]

# Перевірити причинно-наслідкові зв'язки
print(vc1.happened_before(vc2.get_timestamp()))  # True: 1→2
print(vc2.happened_before(vc3.get_timestamp()))  # True: 2→3
print(vc1.happened_before(vc3.get_timestamp()))  # True: 1→3 (транзитивно)
```

### Приклад 3: Виявлення одночасних подій

```python
from scheduler.clocks.vector_clock import VectorClock

vc1 = VectorClock(0, 2)
vc2 = VectorClock(1, 2)

# Два незалежні інкременти (одночасні)
vc1.increment_internal()  # [1, 0]
vc2.increment_internal()  # [0, 1]

# Перевірити паралельність
print(vc1.concurrent_with(vc2.get_timestamp()))  # True
print(vc2.concurrent_with(vc1.get_timestamp()))  # True

# Перевірити причинно-наслідковий зв'язок
print(vc1.happened_before(vc2.get_timestamp()))  # False
print(vc2.happened_before(vc1.get_timestamp()))  # False
```

## Розширення

### Додавання нових типів годинників

Для додавання нового типу годинника:

1. Спадкуйте від `ClockInterface` у `lamport_clock.py`
2. Реалізуйте необхідні методи
3. Інтегруйте з `NodeWithClocks`

```python
from scheduler.clocks.lamport_clock import ClockInterface

class MyCustomClock(ClockInterface):
    def __init__(self):
        # Ініціалізація
        pass
    
    def increment_internal(self):
        # Реалізація
        pass
    
    def send_timestamp(self):
        # Реалізація
        pass
    
    def receive_timestamp(self, timestamp):
        # Реалізація
        pass
    
    def get_timestamp(self):
        # Реалізація
        pass
```

## Питання часто задані

**P: Який годинник вибрати - Lamport чи Vector?**

A: Вибір залежить від вимог:
- Lamport для простоти та мінімальних накладних витрат
- Vector для точної інформації про причинно-наслідкові зв'язки

**P: Як обробити мережу з великою кількістю вузлів?**

A: Vector Clock мають O(n) накладні витрати. Для великих мереж розглядайте:
- Lamport Clock (O(1) накладні витрати)
- Матричні годинники для певних сценаріїв
- Скорочені векторні годинники

**P: Як використовувати годинники для виявлення конфліктів?**

A: Використовуйте Vector Clock для порівняння операцій:
```python
if vc_op1.happened_before(vc_op2.get_timestamp()):
    # op1 сталася раніше за op2
elif vc_op2.happened_before(vc_op1.get_timestamp()):
    # op2 сталася раніше за op1
else:
    # Операції одночасні - можливий конфлікт!
```
