# Distributed Algorithms Implementation Guide

## Overview

This document describes the implementations of two distributed spanning tree algorithms: **Averbukh (BFS-based)** and **Sidon (DFS-based)**.

## Algorithms Comparison

| Aspect | Averbukh | Sidon |
|--------|----------|-------|
| **Traversal Type** | Breadth-First (BFS) | Depth-First (DFS) |
| **Exploration Pattern** | Parallel waves | Single path at a time |
| **Tree Construction** | All edges explored simultaneously | One neighbor at a time |
| **Back-edge Detection** | Implicit (all non-tree edges) | Explicit (BACK_EDGE messages) |
| **Phases** | 4: waiting → exploring → collecting → finished | 4: waiting → exploring → backtracking → finished |
| **Time Complexity** | O(n + m) | O(n + m) |
| **Message Complexity** | O(n + m) | O(n² + m) (due to DFS nature) |

---

## Averbukh Algorithm (BFS-based Spanning Tree)

### Overview
The Averbukh algorithm constructs a spanning tree using Breadth-First Search. Based on Baruch Awerbuch's foundational work on distributed spanning trees (1987), this algorithm explores all neighbors in parallel waves for efficient tree construction.

### Phases

#### 1. **Waiting** (Initial state)
- All non-root nodes start in this phase
- Waiting to receive an EXPLORE message

#### 2. **Exploring**
- Root initiates by sending EXPLORE to all neighbors
- Non-root nodes that receive EXPLORE accept the first sender as parent
- Each node sends EXPLORE to all unvisited neighbors
- Parent-child relationships established

#### 3. **Collecting**
- All exploration complete
- Nodes collect data from children
- Prepare aggregated results for parent

#### 4. **Finished**
- Data reaches root
- Algorithm terminates
- Spanning tree fully constructed

### Messages

- **EXPLORE**: Initiates tree exploration (carries lamport/vector clock timestamps)
- **COLLECT**: Signals start of data collection phase
- **DATA**: Carries aggregated data from children
- **ACK**: Acknowledges receipt of DATA

### State Variables

```python
parent: UUID | None              # Parent node ID
children: List[UUID]             # Child node IDs
visited_neighbors: List[UUID]    # Neighbors already contacted
phase: str                        # Current phase name
collected_data: Dict             # Node metadata and children data
lamport_clock: LamportClock      # Lamport logical clock
vector_clock: VectorClock        # Vector logical clock
```

### Algorithm Flow

```
1. Root transitions from waiting → exploring
2. Root broadcasts EXPLORE to all neighbors
3. Other nodes receive EXPLORE:
   - Accept first sender as parent
   - Transition to exploring
   - Send EXPLORE to remaining neighbors
4. When all neighbors explored, transition to collecting
5. Send COLLECT to all children
6. Receive DATA from children, aggregate
7. Send DATA to parent (or finish if root)
8. All nodes reach finished phase
```

### Key Properties

- **Correctness**: Produces a valid spanning tree with single parent per node (except root)
- **Optimality**: Minimal height on BFS tree (network diameter)
- **Parallelism**: Explores multiple paths simultaneously
- **Synchronization**: Uses logical clocks to track event ordering

---

## Sidon Algorithm (DFS-based Spanning Tree)

### Overview
The Sidon algorithm constructs a spanning tree using Depth-First Search. Unlike BFS, it explores one neighbor at a time, detecting back-edges (non-tree edges) more explicitly.

### Phases

#### 1. **Waiting** (Initial state)
- All non-root nodes start in this phase
- Waiting to receive an EXPLORE message

#### 2. **Exploring**
- Root/receiving node selects unvisited neighbor randomly
- Sends EXPLORE message to that neighbor
- Continues until all neighbors explored
- Detects back-edges (EXPLORE from non-parent)

#### 3. **Backtracking**
- No unvisited neighbors remain
- Aggregates data from children
- Sends results back to parent
- Waits for CONTINUE from parent or finishes

#### 4. **Finished**
- Data reaches root
- Algorithm terminates
- DFS spanning tree constructed

### Messages

- **EXPLORE**: Initiates DFS exploration to one neighbor
- **BACK_EDGE**: Responds to EXPLORE from non-parent (back-edge detection)
- **CONTINUE**: Signals next exploration phase
- **DATA**: Carries aggregated data to parent
- **ACK**: Acknowledges receipt of DATA

### State Variables

```python
parent: UUID | None                    # Parent node ID
children: Set[UUID]                    # Child node IDs
visited_neighbors: Set[UUID]          # Already explored neighbors
unvisited_neighbors: Set[UUID]        # Not yet explored neighbors
children_completed: Set[UUID]         # Children finished backtracking
phase: str                            # Current phase name
collected_data: Dict                  # Node metadata, children data, DFS level
lamport_clock: LamportClock           # Lamport logical clock
vector_clock: VectorClock             # Vector logical clock
```

### Algorithm Flow

```
1. Root transitions from waiting → exploring
2. Root selects random unvisited neighbor
3. Root sends EXPLORE to that neighbor
4. Non-root receiving EXPLORE:
   - Marks sender as parent
   - Selects own unvisited neighbor
   - Sends EXPLORE to it (or BACK_EDGE if none)
5. Back-edge detection:
   - If EXPLORE received from non-parent → BACK_EDGE
   - If EXPLORE received from parent → tree edge
6. DFS continues until all neighbors explored
7. Transition to backtracking:
   - Send DATA to parent
   - Wait for all children to complete
8. Parent receives DATA:
   - Aggregates results
   - Continues exploration or backtracks
9. Root receives all results → algorithm finishes
```

### DFS Properties

- **Level Tracking**: Each node knows its depth in DFS tree
- **Back-edge Detection**: Explicit BACK_EDGE messages identify cycles
- **Sequential Exploration**: One path explored fully before backtracking
- **Memory Efficiency**: Fewer messages in certain network topologies

### Key Properties

- **Correctness**: Produces valid DFS spanning tree with cycle detection
- **Depth**: May be deeper than BFS tree (network diameter × number of branches)
- **Back-edge Detection**: Explicitly identifies non-tree edges
- **Synchronization**: Uses logical clocks for event ordering

---

## Logical Clock Integration

Both algorithms integrate **Lamport** and **Vector** clocks:

### Lamport Clock
- Simple counter-based logical clock
- Incremented on every local event and message receipt
- `update(received_time)`: Sets local clock to `max(local, received) + 1`
- Ensures happens-before relationship for event ordering

### Vector Clock
- n-dimensional vector (one entry per process)
- Enables detection of causal relationships
- Updated on all message sends and receives
- Allows distinguishing causally ordered vs. concurrent events

### Clock Usage in Algorithms

```python
# On sending message
sender.lamport_clock.increment()
sender.vector_clock.increment()
message_data['lamport_timestamp'] = sender.lamport_clock.value
message_data['vector_timestamp'] = sender.vector_clock.get_time()

# On receiving message
receiver.lamport_clock.update(message_data['lamport_timestamp'])
receiver.vector_clock.update(message_data['vector_timestamp'])
```

---

## Network Topology

Both algorithms are tested on an 8-node tree topology:

```
        Node 0 (root)
       /          \
    Node 1       Node 2
   /  |  \      / | | \
  3   4   5    6  7 8  9
```

This topology allows testing:
- Multiple children per node
- Different tree depths
- Various message patterns

---

## Implementation Details

### File Structure

```
scheduler/
├── core/
│   ├── lamport_clock.py       # Lamport clock implementation
│   ├── vector_clock.py        # Vector clock implementation
│   ├── action.py             # Message class
│   ├── node_response.py       # Response wrapper
│   └── mailbox.py            # Message delivery
├── implementation/
│   ├── averbukh_node.py       # BFS algorithm node
│   ├── averbukh_network.py    # BFS network topology
│   ├── sidon_node.py          # DFS algorithm node
│   └── sidon_network.py       # DFS network topology
└── abstract/
    ├── abstract_node.py       # Base node interface
    └── abstract_network.py    # Base network interface
```

### Running Tests

```bash
# Run all algorithm tests
pytest test_averbukh_sidon.py -v

# Run specific algorithm tests
pytest test_averbukh_sidon.py::TestAverbukAlgorithm -v
pytest test_averbukh_sidon.py::TestSidonAlgorithm -v

# Run with coverage
pytest test_averbukh_sidon.py --cov=scheduler
```

---

## Performance Characteristics

### Message Complexity

| Metric | Averbukh | Sidon |
|--------|----------|-------|
| Tree edges | n-1 | n-1 |
| EXPLORE messages | O(m) | O(n²) worst case |
| DATA messages | O(n) | O(n) |
| BACK_EDGE messages | 0 | O(m - n + 1) |
| Total messages | O(n + m) | O(n² + m) |

### Time Complexity

| Metric | Averbukh | Sidon |
|--------|----------|-------|
| Phases | 4 | 4 |
| Message delay | O(diam) | O(diam × nodes) |
| Spanning tree height | O(diam) | O(n) worst case |

*where diam = network diameter*

---

## Testing Strategy

### Unit Tests (16 total)

#### Averbukh Tests (6)
- Network creation and initialization
- Initial state validation
- Root initialization
- Clock advancement
- Parent-child relationships
- Vector clock dimensions

#### Sidon Tests (7)
- Network creation and initialization  
- Initial state validation
- Root initialization
- DFS traversal pattern
- Back-edge detection
- Clock advancement
- Vector clock dimensions

#### Comparison Tests (3)
- Both use same network size
- Both have logical clock support
- Both support phase transitions

---

## Future Enhancements

1. **Simulation Support**: Integrate with `run_simulation.py` for message tracing
2. **Visualization**: Generate tree visualization from algorithm results
3. **Alternative Topologies**: Add ring, star, mesh network support
4. **Performance Analysis**: Add timing and message count instrumentation
5. **Variants**: Implement async message handling, fault tolerance

---

## References

- **Averbukh Algorithm**: Baruch Awerbuch, "Optimal Distributed Algorithms for Minimum Spanning Trees and Shortest Paths" (1987)
- **Logical Clocks**: Leslie Lamport, "Time, Clocks, and the Ordering of Events in a Distributed System" (1978)
- **Vector Clocks**: Colin J. Fidge, "Logical Time in Distributed Computing Systems" (1988)

---

## Author Notes

These implementations demonstrate key concepts in distributed systems:
- **Synchronization**: Without shared memory or synchronized clocks
- **Graph Traversal**: Constructing spanning trees in a distributed manner
- **Message Passing**: Using asynchronous message exchange
- **State Management**: Tracking complex distributed state across multiple processes

The algorithms are educationally rigorous while remaining practical for understanding real distributed systems challenges.
