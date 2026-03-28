#!/usr/bin/env python
"""
Simple test script to verify the Lamport and Vector clocks are working correctly.
"""

import uuid
import sys
sys.path.insert(0, '/Users/rostislavurdejcuk/My Drive/lnu/uni-2026/algorithms/lab1/dss')

from scheduler.core.lamport_clock import LamportClock
from scheduler.core.vector_clock import VectorClock

def test_lamport_clock():
    """Test Lamport clock functionality"""
    print("=" * 60)
    print("Testing Lamport Clock")
    print("=" * 60)
    
    node_id = uuid.uuid4()
    clock = LamportClock(node_id)
    
    print(f"Initial clock: {clock.get_timestamp()}")
    assert clock.get_timestamp() == 0
    
    print(f"After increment: {clock.increment()}")
    assert clock.get_timestamp() == 1
    
    print(f"After increment: {clock.increment()}")
    assert clock.get_timestamp() == 2
    
    print(f"After receiving message with timestamp 5: {clock.update_on_receive(5)}")
    assert clock.get_timestamp() == 6
    
    print(f"After receiving message with timestamp 3: {clock.update_on_receive(3)}")
    assert clock.get_timestamp() == 7
    
    print(f"After increment: {clock.increment()}")
    assert clock.get_timestamp() == 8
    
    print("\n✓ Lamport clock tests passed!\n")


def test_vector_clock():
    """Test Vector clock functionality"""
    print("=" * 60)
    print("Testing Vector Clock")
    print("=" * 60)
    
    node1_id = uuid.uuid4()
    node2_id = uuid.uuid4()
    node3_id = uuid.uuid4()
    
    all_ids = [node1_id, node2_id, node3_id]
    
    clock1 = VectorClock(node1_id, all_ids)
    clock2 = VectorClock(node2_id, all_ids)
    clock3 = VectorClock(node3_id, all_ids)
    
    print(f"Initial vector for node1: {clock1.get_vector()}")
    for node_id in all_ids:
        assert clock1.get_vector()[node_id] == 0
    
    print(f"After node1 increment: {clock1.increment()}")
    assert clock1.get_vector()[node1_id] == 1
    
    print(f"After node2 increment: {clock2.increment()}")
    assert clock2.get_vector()[node2_id] == 1
    
    # Simulate node2 receiving a message from node1
    print(f"Node2 receiving message from node1 with vector {clock1.get_vector()}")
    received_vector = clock1.get_vector()
    updated = clock2.update_on_receive(received_vector)
    print(f"Node2 after update: {updated}")
    
    # Check that node2's clock is now [1, 2, 0]
    assert updated[node1_id] == 1
    assert updated[node2_id] == 2
    assert updated[node3_id] == 0
    
    # Node3 receives message from node2
    print(f"Node3 receiving message from node2 with vector {clock2.get_vector()}")
    received_vector = clock2.get_vector()
    updated = clock3.update_on_receive(received_vector)
    print(f"Node3 after update: {updated}")
    
    assert updated[node1_id] == 1
    assert updated[node2_id] == 2
    assert updated[node3_id] == 1
    
    print("\n✓ Vector clock tests passed!\n")


if __name__ == '__main__':
    try:
        test_lamport_clock()
        test_vector_clock()
        print("=" * 60)
        print("All tests passed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
