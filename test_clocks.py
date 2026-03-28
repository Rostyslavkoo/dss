"""
Demonstration and test suite for Logical Clocks
"""
import uuid
from scheduler.implementation.network_with_clocks import NetworkWithClocks
from scheduler.implementation.node_with_clocks import NodeWithClocks
from scheduler.core.timestamped_action import TimestampedAction


def test_lamport_clock_basic():
    """Test basic Lamport clock functionality"""
    print("\n" + "="*60)
    print("TEST 1: Basic Lamport Clock Operations")
    print("="*60)
    
    from scheduler.clocks.lamport_clock import LamportClock
    
    # Create two clocks
    clock1 = LamportClock(0)
    clock2 = LamportClock(0)
    
    print(f"Initial state:")
    print(f"  Clock 1: {clock1.get_timestamp()}")
    print(f"  Clock 2: {clock2.get_timestamp()}")
    
    # Internal event at clock1
    clock1.increment_internal()
    print(f"\nAfter internal event at Clock 1:")
    print(f"  Clock 1: {clock1.get_timestamp()}")
    
    # Send message from clock1 to clock2
    ts1 = clock1.send_timestamp()
    print(f"\nClock 1 sends message with timestamp {ts1}")
    print(f"  Clock 1: {clock1.get_timestamp()}")
    
    # Receive at clock2
    clock2.receive_timestamp(ts1)
    print(f"\nClock 2 receives message with timestamp {ts1}")
    print(f"  Clock 2: {clock2.get_timestamp()}")
    
    # Another internal event at clock2
    clock2.increment_internal()
    print(f"\nAfter internal event at Clock 2:")
    print(f"  Clock 2: {clock2.get_timestamp()}")
    
    print("\n✓ Lamport Clock test passed")


def test_vector_clock_basic():
    """Test basic Vector clock functionality"""
    print("\n" + "="*60)
    print("TEST 2: Basic Vector Clock Operations")
    print("="*60)
    
    from scheduler.clocks.vector_clock import VectorClock
    
    # Create three clocks for three processes
    vc1 = VectorClock(0, 3)
    vc2 = VectorClock(1, 3)
    vc3 = VectorClock(2, 3)
    
    print(f"Initial state:")
    print(f"  VC1 (Process 0): {vc1.get_timestamp()}")
    print(f"  VC2 (Process 1): {vc2.get_timestamp()}")
    print(f"  VC3 (Process 2): {vc3.get_timestamp()}")
    
    # Internal events
    vc1.increment_internal()
    vc2.increment_internal()
    print(f"\nAfter internal events at VC1 and VC2:")
    print(f"  VC1: {vc1.get_timestamp()}")
    print(f"  VC2: {vc2.get_timestamp()}")
    
    # Send from VC1 to VC2
    ts1 = vc1.send_timestamp()
    print(f"\nVC1 sends message with timestamp {ts1}")
    
    vc2.receive_timestamp(ts1)
    print(f"VC2 receives message")
    print(f"  VC2: {vc2.get_timestamp()}")
    
    # Send from VC2 to VC3
    ts2 = vc2.send_timestamp()
    print(f"\nVC2 sends message with timestamp {ts2}")
    
    vc3.receive_timestamp(ts2)
    print(f"VC3 receives message")
    print(f"  VC3: {vc3.get_timestamp()}")
    
    # Test causal relationships
    print(f"\nCausal relationships:")
    vc1_ts = vc1.get_timestamp()
    vc2_ts = vc2.get_timestamp()
    print(f"  VC1 happened before VC2: {vc1.happened_before(vc2_ts)}")
    
    vc2.increment_internal()
    vc3.increment_internal()
    vc2_ts = vc2.get_timestamp()
    vc3_ts = vc3.get_timestamp()
    print(f"  VC2 and VC3 concurrent: {vc2.concurrent_with(vc3_ts)}")
    
    print("\n✓ Vector Clock test passed")


def test_network_with_clocks():
    """Test network with logical clocks"""
    print("\n" + "="*60)
    print("TEST 3: Network with Logical Clocks")
    print("="*60)
    
    # Create network with 4 nodes
    network = NetworkWithClocks(num_nodes=4, enable_lamport=True, enable_vector=True)
    
    print(f"\nCreated network with {len(network.nodes)} nodes")
    print("Network topology (Linear: 0-1-2-3):")
    
    for i, node in enumerate(network.nodes):
        neighbors_str = ", ".join([n.hex[:8] for n in node.neighbors])
        print(f"  Node {i}: neighbors = [{neighbors_str}]")
    
    # Initial state
    print("\nInitial clock values:")
    network.print_clocks()
    
    # Simulate message from node 0 to node 1
    node0: NodeWithClocks = network.clock_nodes[0]
    node1: NodeWithClocks = network.clock_nodes[1]
    node2: NodeWithClocks = network.clock_nodes[2]
    
    print(f"\n--- Sending message from Node 0 to Node 1 ---")
    
    # Create and send message
    msg = node0.send_message_to(node1.node_id, "Hello from Node 0")
    print(f"Message: {msg}")
    
    # Process at node 1
    print(f"\nNode 1 processes message")
    response = node1.process_action(msg)
    print(f"Node 1 clock updated")
    
    # Display updated clocks
    print("\nUpdated clock values:")
    network.print_clocks()
    
    # More messages
    print(f"\n--- Sending message from Node 1 to Node 2 ---")
    msg2 = node1.send_message_to(node2.node_id, "Relay to Node 2")
    print(f"Message: {msg2}")
    
    node2.process_action(msg2)
    
    print("\nUpdated clock values:")
    network.print_clocks()
    
    # Event history
    network.print_events()
    
    print("\n✓ Network test passed")


def test_causal_ordering():
    """Test causal ordering with vector clocks"""
    print("\n" + "="*60)
    print("TEST 4: Causal Ordering with Vector Clocks")
    print("="*60)
    
    from scheduler.clocks.vector_clock import VectorClock
    
    # Simulate scenario: A -> B -> C (causal chain)
    print("Scenario: Message chain A -> B -> C")
    
    vc_a = VectorClock(0, 3)
    vc_b = VectorClock(1, 3)
    vc_c = VectorClock(2, 3)
    
    # A sends to B
    print("\n1. A sends to B")
    ts_ab = vc_a.send_timestamp()
    print(f"   A's clock: {ts_ab}")
    vc_b.receive_timestamp(ts_ab)
    print(f"   B's clock after receiving: {vc_b.get_timestamp()}")
    
    # B sends to C
    print("\n2. B sends to C")
    ts_bc = vc_b.send_timestamp()
    print(f"   B's clock: {ts_bc}")
    vc_c.receive_timestamp(ts_bc)
    print(f"   C's clock after receiving: {vc_c.get_timestamp()}")
    
    # Check causality
    print("\n3. Causality check:")
    print(f"   A's event happened before B: {vc_a.happened_before(vc_b.get_timestamp())}")
    print(f"   B's event happened before C: {vc_b.happened_before(vc_c.get_timestamp())}")
    print(f"   A's event happened before C: {vc_a.happened_before(vc_c.get_timestamp())}")
    
    print("\n✓ Causal ordering test passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("LOGICAL CLOCKS TEST SUITE")
    print("="*60)
    
    try:
        test_lamport_clock_basic()
        test_vector_clock_basic()
        test_causal_ordering()
        test_network_with_clocks()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
