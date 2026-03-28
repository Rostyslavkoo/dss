"""
Network implementation with Logical Clock support
"""
import uuid
from typing import List, Dict

from scheduler.abstract.abstract_network import AbstractNetwork
from scheduler.implementation.node_with_clocks import NodeWithClocks


class NetworkWithClocks(AbstractNetwork):
    """
    Distributed network with nodes that support Lamport and Vector clocks.
    
    This network creates nodes that maintain logical clocks for causal ordering.
    """
    
    NUMBER_OF_NODES = 4

    def __init__(self, num_nodes: int = None, enable_lamport: bool = True, enable_vector: bool = True):
        """
        Initialize network with clock-aware nodes.
        
        Args:
            num_nodes: Number of nodes in the network
            enable_lamport: Enable Lamport clock on all nodes
            enable_vector: Enable Vector clock on all nodes
        """
        if num_nodes is not None:
            self.NUMBER_OF_NODES = num_nodes
        
        self.clock_nodes: List[NodeWithClocks] = []
        self.enable_lamport = enable_lamport
        self.enable_vector = enable_vector
        
        # Create node IDs
        ids = [uuid.uuid4() for _ in range(self.NUMBER_OF_NODES)]
        
        # Define network topology
        self.edges = self._get_edges(ids)
        
        # Create nodes with clocks
        for index, node_id in enumerate(ids):
            node = NodeWithClocks(
                node_id=node_id,
                neighbors=self.edges[node_id],
                process_index=index,
                num_processes=self.NUMBER_OF_NODES,
                enable_lamport=enable_lamport,
                enable_vector=enable_vector
            )
            self.clock_nodes.append(node)
        
        # Also assign to nodes for AbstractNetwork (cast to list of AbstractNode)
        self.nodes = list(self.clock_nodes)
        super().__init__(self.nodes)
    
    def _get_edges(self, ids: List[uuid.UUID]) -> Dict[uuid.UUID, List[uuid.UUID]]:
        """
        Define network topology.
        Creates a simple linear topology for demonstration.
        
        Args:
            ids: List of node IDs
            
        Returns:
            Dictionary mapping node IDs to their neighbors
        """
        if len(ids) == 4:
            # Linear topology: 0-1-2-3
            return {
                ids[0]: [ids[1]],
                ids[1]: [ids[0], ids[2]],
                ids[2]: [ids[1], ids[3]],
                ids[3]: [ids[2]]
            }
        else:
            # For arbitrary number of nodes, create a simple ring topology
            edges = {}
            for i, node_id in enumerate(ids):
                neighbors = []
                if i > 0:
                    neighbors.append(ids[i - 1])
                if i < len(ids) - 1:
                    neighbors.append(ids[i + 1])
                edges[node_id] = neighbors
            return edges

    def get_node_by_index(self, index: int) -> NodeWithClocks:
        """Get node by index"""
        if 0 <= index < len(self.clock_nodes):
            return self.clock_nodes[index]
        raise IndexError(f"Node index {index} out of range")

    def print_clocks(self):
        """Print current clock values for all nodes"""
        print("\n=== Current Clock Values ===")
        for i, node in enumerate(self.clock_nodes):
            clock_info = node.get_clock_info()
            print(f"Node {i}: {node.node_id.hex[:8]}")
            print(f"  Lamport Clock: {clock_info['lamport']}")
            print(f"  Vector Clock:  {clock_info['vector']}")

    def print_events(self):
        """Print event history for all nodes"""
        print("\n=== Event History ===")
        for i, node in enumerate(self.clock_nodes):
            events = node.get_events()
            if events:
                print(f"\nNode {i} ({node.node_id.hex[:8]}):")
                for event in events:
                    print(f"  {event}")
            else:
                print(f"\nNode {i} ({node.node_id.hex[:8]}): No events")
