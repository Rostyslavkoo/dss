import uuid
from typing import List, Dict, Optional, Any
from scheduler.abstract.abstract_node import AbstractNode
from scheduler.core.action import Action
from scheduler.core.mailbox import Mailbox
from scheduler.core.node_response import NodeResponse
from scheduler.clocks.lamport_clock import LamportClock
from scheduler.clocks.vector_clock import VectorClock


class AverbukAlgorithmNode(AbstractNode):
    """
    Implementation of Averbukh's Breadth-First Search (BFS) algorithm 
    for distributed network traversal and spanning tree construction.
    
    The algorithm follows BFS principles in a distributed setting:
    1. An initiator sends out a wave of messages
    2. Each node upon first receipt becomes part of the spanning tree
    3. Nodes collect information from all neighbors
    4. Information is aggregated and returned to root
    """

    def __init__(self, node_id: uuid.UUID, neighbors: List[uuid.UUID], all_node_ids: List[uuid.UUID]):
        self.node_id = node_id
        self.mailbox = Mailbox()
        self.neighbors = neighbors
        self.all_node_ids = all_node_ids
        
        # Algorithm-specific state
        self.parent: Optional[uuid.UUID] = None
        self.children: List[uuid.UUID] = []
        self.visited_neighbors: List[uuid.UUID] = []
        self.algorithm_started = False
        self.phase = "waiting"  # waiting, exploring, collecting, finished
        self.messages_received_from_children = 0
        
        # Data collection
        self.collected_data: Dict[str, Any] = {
            "node_id": str(node_id),
            "neighbors": [str(n) for n in neighbors],
            "visited_neighbors": []
        }
        
        # Clocks for tracking order of events
        self.lamport_clock = LamportClock(0)
        self.vector_clock = VectorClock(all_node_ids.index(node_id), len(all_node_ids))
        
        # Statistics
        self.action_count = 0
        self.message_count = 0

    def process_action(self, message: Action) -> NodeResponse:
        """Process incoming message and execute algorithm logic."""
        self.action_count += 1
        
        # Update clocks
        if message.data.get('lamport_timestamp') is not None:
            self.lamport_clock.receive_timestamp(message.data['lamport_timestamp'])
        if message.data.get('vector_timestamp') is not None:
            self.vector_clock.receive_timestamp(message.data['vector_timestamp'])
        
        # Route message to appropriate handler
        message_type = message.data.get('message_type')
        
        if message_type == 'INIT':
            return self._handle_init(message)
        elif message_type == 'EXPLORE':
            return self._handle_explore(message)
        elif message_type == 'COLLECT':
            return self._handle_collect(message)
        elif message_type == 'DATA':
            return self._handle_data(message)
        
        return NodeResponse([])

    def _handle_init(self, message: Action) -> NodeResponse:
        """Initialize algorithm from root."""
        print(f"[Averbukh] Node {self.node_id} INITIALIZED as root")
        self.algorithm_started = True
        self.phase = "exploring"
        
        # Increment clocks for local action
        self.lamport_clock.increment_internal()
        self.vector_clock.increment_internal()
        
        # Send EXPLORE messages to all neighbors
        return self._send_to_neighbors('EXPLORE', 
                                       sender=self.node_id,
                                       parent=None)

    def _handle_explore(self, message: Action) -> NodeResponse:
        """Handle EXPLORE message during BFS phase."""
        sender = message.data.get('sender')
        is_root = sender is None
        
        # Only process if not yet in tree
        if self.parent is not None:
            return NodeResponse([])  # Already in tree, ignore duplicate
        
        print(f"[Averbukh] Node {self.node_id} received EXPLORE from {sender}, becoming child of {sender}")
        
        self.parent = sender
        self.phase = "exploring"
        self.visited_neighbors.append(sender)
        
        # Increment clocks for local action
        self.lamport_clock.increment_internal()
        self.vector_clock.increment_internal()
        
        # Send EXPLORE to all neighbors except parent
        outgoing = []
        for neighbor in self.neighbors:
            if neighbor != self.parent:
                outgoing.append(neighbor)
                self.visited_neighbors.append(neighbor)
        
        if not outgoing:
            # Leaf node - send ACK back to parent
            self.phase = "collecting"
            return self._send_ack_to_parent()
        
        # Send EXPLORE messages to non-parent neighbors
        return self._send_to_neighbors('EXPLORE',
                                       sender=self.node_id,
                                       parent=self.parent,
                                       targets=outgoing)

    def _handle_collect(self, message: Action) -> NodeResponse:
        """Handle COLLECT message during aggregation phase."""
        self.phase = "collecting"
        self.lamport_clock.increment_internal()
        self.vector_clock.increment_internal()
        
        print(f"[Averbukh] Node {self.node_id} starting data collection")
        
        # If leaf node, send ACK immediately
        if not self.children:
            return self._send_ack_to_parent()
        
        # Otherwise, we'll collect from children in DATA messages
        return NodeResponse([])

    def _handle_data(self, message: Action) -> NodeResponse:
        """Handle DATA message with aggregated information from children."""
        sender = message.data.get('sender')
        child_data = message.data.get('data', {})
        
        print(f"[Averbukh] Node {self.node_id} received DATA from child {sender}")
        
        # Record child as having reported
        if sender in self.children:
            self.children.remove(sender)  # Remove once we get data
        
        # Aggregate data
        if 'children_data' not in self.collected_data:
            self.collected_data['children_data'] = []
        self.collected_data['children_data'].append(child_data)
        
        # If all children reported, send to parent
        if not self.children:
            self.lamport_clock.increment_internal()
            self.vector_clock.increment_internal()
            return self._send_ack_to_parent()
        
        return NodeResponse([])

    def _send_to_neighbors(self, msg_type: str, sender: uuid.UUID = None,
                          parent: Optional[uuid.UUID] = None,
                          targets: Optional[List[uuid.UUID]] = None) -> NodeResponse:
        """Send message to specified neighbors."""
        if sender is None:
            sender = self.node_id
        
        if targets is None:
            targets = self.neighbors
        
        self.lamport_clock.increment_internal()
        self.vector_clock.increment_internal()
        
        actions = []
        for target in targets:
            action = Action(
                {
                    'message_type': msg_type,
                    'sender': sender,
                    'parent': parent,
                    'data': self.collected_data.copy(),
                    'lamport_timestamp': self.lamport_clock.get_timestamp(),
                    'vector_timestamp': self.vector_clock.get_vector()
                },
                target,
                uuid.uuid4()
            )
            actions.append(action)
            self.message_count += 1
            print(f"[Averbukh] Node {self.node_id} sending {msg_type} to {target}")
        
        return NodeResponse(actions)

    def _send_ack_to_parent(self) -> NodeResponse:
        """Send ACK/DATA back to parent."""
        if self.parent is None:
            print(f"[Averbukh] Node {self.node_id} is root, algorithm complete")
            self.phase = "finished"
            return NodeResponse([])
        
        self.lamport_clock.increment_internal()
        self.vector_clock.increment_internal()
        
        action = Action(
            {
                'message_type': 'DATA',
                'sender': self.node_id,
                'data': self.collected_data,
                'lamport_timestamp': self.lamport_clock.get_timestamp(),
                'vector_timestamp': self.vector_clock.get_vector()
            },
            self.parent,
            uuid.uuid4()
        )
        
        print(f"[Averbukh] Node {self.node_id} sending DATA to parent {self.parent}")
        self.message_count += 1
        return NodeResponse([action])
