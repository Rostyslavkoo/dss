"""
Advanced demonstration scenarios for Logical Clocks
"""
from scheduler.implementation.network_with_clocks import NetworkWithClocks
from scheduler.implementation.node_with_clocks import NodeWithClocks


def scenario_concurrent_messages():
    """
    Scenario: Demonstrate concurrent messages in distributed system
    
    Network: Linear topology 0-1-2-3
    
    Timeline:
    1. Node 0 sends to Node 1
    2. Node 2 sends to Node 3 (concurrent, not related to message 1)
    3. Node 1 receives from Node 0
    4. Node 3 receives from Node 2
    """
    print("\n" + "="*70)
    print("SCENARIO 1: Concurrent Messages in Distributed System")
    print("="*70)
    
    network = NetworkWithClocks(num_nodes=4, enable_lamport=True, enable_vector=True)
    
    print("\nInitial State:")
    network.print_clocks()
    
    # Get nodes
    nodes = network.clock_nodes
    
    print("\n--- Concurrent Event 1: Node 0 -> Node 1 ---")
    msg1 = nodes[0].send_message_to(nodes[1].node_id, "msg_01")
    print(f"Sent: {msg1}")
    
    print("\n--- Concurrent Event 2: Node 2 -> Node 3 ---")
    msg2 = nodes[2].send_message_to(nodes[3].node_id, "msg_23")
    print(f"Sent: {msg2}")
    
    print("\nAfter sending (before receiving):")
    network.print_clocks()
    
    print("\n--- Node 1 receives from Node 0 ---")
    nodes[1].process_action(msg1)
    print("Received and processed")
    
    print("\n--- Node 3 receives from Node 2 ---")
    nodes[3].process_action(msg2)
    print("Received and processed")
    
    print("\nAfter receiving:")
    network.print_clocks()
    
    # Analyze causality
    print("\n--- Causality Analysis ---")
    lc_0 = nodes[0].get_clock_info()['lamport']
    lc_1 = nodes[1].get_clock_info()['lamport']
    lc_2 = nodes[2].get_clock_info()['lamport']
    lc_3 = nodes[3].get_clock_info()['lamport']
    
    print(f"Lamport Clocks: 0={lc_0}, 1={lc_1}, 2={lc_2}, 3={lc_3}")
    print(f"Note: Events on 0->1 and 2->3 are concurrent (no causal relationship)")
    
    network.print_events()


def scenario_message_chain():
    """
    Scenario: Message chain creating causal ordering
    
    Timeline:
    1. Node 0 sends to Node 1
    2. Node 1 receives and sends to Node 2
    3. Node 2 receives and sends to Node 3
    
    This creates a causal chain: Event0 -> Event1 -> Event2 -> Event3
    """
    print("\n" + "="*70)
    print("SCENARIO 2: Message Chain with Causal Ordering")
    print("="*70)
    
    network = NetworkWithClocks(num_nodes=4, enable_lamport=True, enable_vector=True)
    nodes = network.clock_nodes
    
    print("\nInitial State:")
    network.print_clocks()
    
    print("\n--- Step 1: Node 0 -> Node 1 ---")
    msg1 = nodes[0].send_message_to(nodes[1].node_id, "step1")
    print(f"Message: {msg1}")
    nodes[1].process_action(msg1)
    print("Node 1 received and updated clocks")
    
    print("\nClocks after Step 1:")
    network.print_clocks()
    
    print("\n--- Step 2: Node 1 -> Node 2 ---")
    msg2 = nodes[1].send_message_to(nodes[2].node_id, "step2")
    print(f"Message: {msg2}")
    nodes[2].process_action(msg2)
    print("Node 2 received and updated clocks")
    
    print("\nClocks after Step 2:")
    network.print_clocks()
    
    print("\n--- Step 3: Node 2 -> Node 3 ---")
    msg3 = nodes[2].send_message_to(nodes[3].node_id, "step3")
    print(f"Message: {msg3}")
    nodes[3].process_action(msg3)
    print("Node 3 received and updated clocks")
    
    print("\nClocks after Step 3:")
    network.print_clocks()
    
    print("\n--- Causality Analysis ---")
    vc_0 = nodes[0].vector_clock.get_timestamp()
    vc_1 = nodes[1].vector_clock.get_timestamp()
    vc_2 = nodes[2].vector_clock.get_timestamp()
    vc_3 = nodes[3].vector_clock.get_timestamp()
    
    print(f"Vector Clocks:")
    print(f"  Node 0: {vc_0}")
    print(f"  Node 1: {vc_1}")
    print(f"  Node 2: {vc_2}")
    print(f"  Node 3: {vc_3}")
    
    print("\nCausal relationships (Vector Clock 'happened-before'):")
    print(f"  0 -> 1: {nodes[0].vector_clock.happened_before(vc_1)}")
    print(f"  1 -> 2: {nodes[1].vector_clock.happened_before(vc_2)}")
    print(f"  2 -> 3: {nodes[2].vector_clock.happened_before(vc_3)}")
    print(f"  0 -> 3: {nodes[0].vector_clock.happened_before(vc_3)} (transitive)")
    
    network.print_events()


def scenario_diamond_pattern():
    """
    Scenario: Diamond pattern - multiple paths converge
    
    Shows how nodes receive multiple messages from different paths
    and their vector clocks reflect all causal relationships
    """
    print("\n" + "="*70)
    print("SCENARIO 3: Multiple Messages and Causal Relationships")
    print("="*70)
    
    network = NetworkWithClocks(num_nodes=4, enable_lamport=True, enable_vector=True)
    nodes = network.clock_nodes
    
    print("\nNetwork Topology: Linear 0-1-2-3")
    print("\nInitial State:")
    network.print_clocks()
    
    # Message 1: 0 -> 1
    print("\n--- Message 1: Node 0 -> Node 1 ---")
    msg_01 = nodes[0].send_message_to(nodes[1].node_id, "msg_01")
    print(f"Message: {msg_01}")
    nodes[1].process_action(msg_01)
    
    print("\nClocks after Message 1:")
    network.print_clocks()
    
    # Message 2: 1 -> 2 (carries information from msg 1)
    print("\n--- Message 2: Node 1 -> Node 2 (causal chain) ---")
    msg_12 = nodes[1].send_message_to(nodes[2].node_id, "msg_12")
    print(f"Message: {msg_12}")
    nodes[2].process_action(msg_12)
    
    print("\nClocks after Message 2:")
    network.print_clocks()
    
    # Message 3: 2 -> 3
    print("\n--- Message 3: Node 2 -> Node 3 (causal chain) ---")
    msg_23 = nodes[2].send_message_to(nodes[3].node_id, "msg_23")
    print(f"Message: {msg_23}")
    nodes[3].process_action(msg_23)
    
    print("\nClocks after Message 3:")
    network.print_clocks()
    
    # Additional message: 1 -> 2 (another message to show vector clock updates)
    print("\n--- Message 4: Node 1 -> Node 2 (another message) ---")
    msg_12_2 = nodes[1].send_message_to(nodes[2].node_id, "msg_12_2")
    print(f"Message: {msg_12_2}")
    nodes[2].process_action(msg_12_2)
    
    print("\nClocks after Message 4:")
    network.print_clocks()
    
    print("\n--- Causality Analysis ---")
    print("Vector Clock represents:")
    print("  Position 0: Node 0's view (how many events at Node 0)")
    print("  Position 1: Node 1's view (how many events at Node 1)")
    print("  Position 2: Node 2's view (how many events at Node 2)")
    print("  Position 3: Node 3's view (how many events at Node 3)")
    print("\nFinal Vector Clock at Node 3:", nodes[3].vector_clock.get_timestamp())
    print("This shows Node 3 'knows about' all previous events in the chain")
    
    network.print_events()


def compare_clocks():
    """
    Scenario: Compare Lamport vs Vector clocks
    
    Shows the difference between the two clock types
    """
    print("\n" + "="*70)
    print("COMPARISON: Lamport Clock vs Vector Clock")
    print("="*70)
    
    network = NetworkWithClocks(num_nodes=3, enable_lamport=True, enable_vector=True)
    nodes = network.clock_nodes
    
    print("\n--- Test Case: Two independent concurrent events ---")
    
    print("\nInitial state:")
    print("  Lamport Clocks: [0, 0, 0]")
    print("  Vector Clocks:  [0,0,0] [0,0,0] [0,0,0]")
    
    print("\nEvent 1: Node 0 sends to Node 1")
    msg1 = nodes[0].send_message_to(nodes[1].node_id, "msg1")
    nodes[1].process_action(msg1)
    
    lc = [n.lamport_clock.get_timestamp() for n in nodes]
    vc = [n.vector_clock.get_timestamp() for n in nodes]
    
    print(f"  Lamport Clocks: {lc}")
    print(f"  Vector Clocks:  {vc}")
    
    print("\nEvent 2: Node 2 performs internal event (concurrent with Event 1)")
    nodes[2].vector_clock.increment_internal()
    nodes[2].lamport_clock.increment_internal()
    
    lc = [n.lamport_clock.get_timestamp() for n in nodes]
    vc = [n.vector_clock.get_timestamp() for n in nodes]
    
    print(f"  Lamport Clocks: {lc}")
    print(f"  Vector Clocks:  {vc}")
    
    print("\n--- Analysis ---")
    print("Lamport Clocks:")
    print("  - Provide total ordering (all events can be linearly ordered)")
    print("  - Cannot distinguish between causal and concurrent events")
    print("  - Lightweight (single counter per process)")
    
    print("\nVector Clocks:")
    print("  - Provide partial ordering (distinguish causal vs concurrent)")
    print("  - Heavier (vector size = number of processes)")
    print("  - Can determine causal relationships precisely")


def run_all_scenarios():
    """Run all demonstration scenarios"""
    print("\n" + "="*70)
    print("LOGICAL CLOCKS DEMONSTRATION SCENARIOS")
    print("="*70)
    
    try:
        scenario_concurrent_messages()
        scenario_message_chain()
        scenario_diamond_pattern()
        compare_clocks()
        
        print("\n" + "="*70)
        print("ALL SCENARIOS COMPLETED SUCCESSFULLY ✓")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Scenario failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_scenarios()
