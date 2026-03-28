import uuid
from typing import List, Dict


class VectorClock:
    """
    Implementation of a vector clock for distributed systems.
    
    The vector clock is a vector of n integers (where n is the number of processes):
    1. Each process i maintains a vector of length n
    2. The i-th entry is the logical clock of process i
    3. On local action: increment the local entry
    4. On sending message: include the entire vector
    5. On receiving message: update each entry to max(local[j], received[j]) for j != i,
                             then increment local[i]
    """

    def __init__(self, node_id: uuid.UUID, all_node_ids: List[uuid.UUID]):
        """
        Initialize the vector clock for a specific node.
        
        :param node_id: The unique identifier of this node
        :param all_node_ids: List of all node IDs in the system (must include node_id)
        """
        self.node_id = node_id
        self.all_node_ids = sorted(all_node_ids, key=lambda x: str(x))  # Keep consistent ordering
        self.node_index = self.all_node_ids.index(node_id)
        # Initialize vector with zeros
        self.vector = {node_id: 0 for node_id in self.all_node_ids}

    def increment(self) -> Dict[uuid.UUID, int]:
        """
        Increment the clock (used when performing a local action).
        
        :return: The current vector clock
        """
        self.vector[self.node_id] += 1
        return self.vector.copy()

    def update_on_receive(self, received_vector: Dict[uuid.UUID, int]) -> Dict[uuid.UUID, int]:
        """
        Update the clock upon receiving a message.
        
        For each entry j:
        - If j == node_id: increment local entry
        - Otherwise: take max of local and received entries
        
        :param received_vector: The vector clock from the received message
        :return: The updated vector clock
        """
        # Update each entry
        for node_id in self.all_node_ids:
            if node_id == self.node_id:
                # Will increment after updating
                pass
            else:
                # Take maximum
                received_timestamp = received_vector.get(node_id, 0)
                self.vector[node_id] = max(self.vector[node_id], received_timestamp)
        
        # Increment local entry
        self.vector[self.node_id] += 1
        return self.vector.copy()

    def get_vector(self) -> Dict[uuid.UUID, int]:
        """
        Get the current vector clock without modifying it.
        
        :return: A copy of the current vector clock
        """
        return self.vector.copy()

    def __repr__(self):
        vector_str = {str(k)[:8]: v for k, v in self.vector.items()}
        return f"VectorClock(node={str(self.node_id)[:8]}, vector={vector_str})"
