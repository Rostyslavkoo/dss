# Швидкий Довідник - Логічні Години у Алгоритмі Террі

## Бистрий Старт

### Тестування Годинників
```bash
python test_clocks.py
```
Результат: ✓ Все працює правильно

### Запуск Симуляції
```bash
python run_simulation.py
```

## Структура Реалізації

### Файли Годинників
```
scheduler/core/
├── lamport_clock.py      # Логічний годинник Лемпорта
└── vector_clock.py       # Векторний годинник
```

### Модифіковані Файли
```
scheduler/implementation/
├── tarry_node.py         # Інтеграція годинників в TarryNode
└── current_network.py    # Передача ID вузлів
```

## Ключові Концепції

### Логічний Годинник Лемпорта

| Операція | Формула | Приклад |
|----------|---------|---------|
| **Локальна дія** | `LC := LC + 1` | 0 → 1 → 2 |
| **Отримання msg** | `LC := max(LC, msg.LC) + 1` | LC=2, msg.LC=5 → 6 |
| **Достатність** | `if LC(a) < LC(b) then a → b` | Часткове впорядкування |

**Коли використовувати:** Проста впорядкування подій, відпустити розподілену систему

### Векторний Годинник

| Операція | Формула | Приклад |
|----------|---------|---------|
| **Локальна дія** | `VC[i] := VC[i] + 1` | [1,0,0] → [2,0,0] |
| **Отримання msg** | `VC[j] := max(VC[j], msg.VC[j])` ∀j, потім `VC[i] += 1` | [2,0,0] + msg[1,2,1] → [2,2,1] → [3,2,1] |
| **Порівняння** | `VC1 < VC2 if ∀i VC1[i] ≤ VC2[i] and ∃j VC1[j] < VC2[j]` | [1,1,0] < [2,2,1] |
| **Паралельність** | `VC1 || VC2 if ¬(VC1 < VC2) and ¬(VC2 < VC1)` | [1,0,1] || [0,1,1] |

**Коли використовувати:** Визначення паралельних подій, причинно-наслідкових відносин

## Приклади Базового Використання

### Використання LamportClock
```python
from scheduler.core.lamport_clock import LamportClock
import uuid

node_id = uuid.uuid4()
clock = LamportClock(node_id)

# Локальна дія
clock.increment()  # Returns 1

# Отримання повідомлення
clock.update_on_receive(5)  # Returns 6

# Отримання часової мітки
ts = clock.get_timestamp()  # Returns 6
```

### Використання VectorClock
```python
from scheduler.core.vector_clock import VectorClock
import uuid

node_ids = [uuid.uuid4() for _ in range(3)]
node_id = node_ids[0]

clock = VectorClock(node_id, node_ids)

# Локальна дія
clock.increment()  # Returns {node1: 1, node2: 0, node3: 0}

# Отримання повідомлення
received_vector = {node_ids[0]: 1, node_ids[1]: 2, node_ids[2]: 1}
clock.update_on_receive(received_vector)
# Returns {node1: 2, node2: 2, node3: 1}

# Отримання вектора
vc = clock.get_vector()
```

### Інтеграція в TarryNode
```python
# Автоматично ініціалізовано в TarryNode.__init__
node = TarryNode(node_id, neighbors, all_node_ids)

# Місцевий доступ до годинників
lamport_ts = node.lamport_clock.get_timestamp()
vector_ts = node.vector_clock.get_vector()

# Годинники оновлюються автоматично при отриманні/відправленні повідомлень
```

## Інтеграція в Алгоритм Террі

### Алгоритм хвилі Террі
1. **Ініціатор** заважно вибирає сусіда і відправляє йому повідомлення
2. **Вузол**, який отримав **вперше**, записує ініціатора як батька
3. **Вузли** відправляють повідомлення всім сусідам крім батька
4. **Дитини** відправляють результат батькові
5. **Батьки** передають результат вверх
6. **Ініціатор** закінчує, коли отримав від усіх дітей

### Годинники у Террі
- **Lagmort Clock** включається в кожне повідомлення як `'lamport_timestamp'`
- **Vector Clock** включається в кожне повідомлення як `'vector_timestamp'`
- Годинники оновлюються при отримання та інкрементуються при відправленні
- Дозволяють відстежити порядок повідомлень у мережі

## Діагностика

### Виведення в Консоль
```
Node <id> processing <message>
Node <id> Data 10
Node <id> Lamport Clock: 5
Node <id> Vector Clock: {key1: 3, key2: 2, key3: 4}
```

### Поширені Проблеми

| Проблема | Рішення |
|----------|---------|
| Година не інкрементується | Перевірити, чи вызывается `increment()` |
| Неправильне значення при отриманні | Переконатися, що `update_on_receive()` вызивается з правильным значенням |
| Невеликий вектор | Перевірити, чи `all_node_ids` передано правильно до `VectorClock` |

## Документація

- **CLOCKS_IMPLEMENTATION.md** - Детальна архітектурна документація
- **IMPLEMENTATION_SUMMARY.md** - Резюме змін і результатів
- **test_clocks.py** - Приклади тестування
