import uuid
import random
from typing import List, Dict, Optional, Any, Set
from scheduler.abstract.abstract_node import AbstractNode
from scheduler.core.action import Action
from scheduler.core.mailbox import Mailbox
from scheduler.core.node_response import NodeResponse
from scheduler.clocks.lamport_clock import LamportClock
from scheduler.clocks.vector_clock import VectorClock


class SidonAlgorithmNode(AbstractNode):
    """
    Implementation of Sidon's Depth-First Search (DFS) algorithm
    for distributed network traversal and information collection.
    
    The algorithm follows DFS principles in a distributed setting:
    1. An initiator selects a random neighbor to explore
    2. Each node explores one neighbor at a time in depth-first manner
    3. Upon backtracking, returns to parent with collected information
    4. Root aggregates all information from the DFS tree
    """

    def __init__(self, node_id: uuid.UUID, neighbors: List[uuid.UUID], all_node_ids: List[uuid.UUID]):
        self.node_id = node_id
        self.mailbox = Mailbox()
        self.neighbors = neighbors
        self.all_node_ids = all_node_ids
        
        # Algorithm-specific state
        self.parent: Optional[uuid.UUID] = None
        self.children: Set[uuid.UUID] = set()
        self.visited_neighbors: Set[uuid.UUID] = set()
        self.unvisited_neighbors: Set[uuid.UUID] = set(neighbors)
        self.algorithm_started = False
        self.phase = "waiting"  # waiting, exploring, backtracking, finished
        self.current_child_being_explored: Optional[uuid.UUID] = None
        self.children_completed: Set[uuid.UUID] = set()
        
        # Data collection
        self.collected_data: Dict[str, Any] = {
            "node_id": str(node_id),
            "neighbors": [str(n) for n in neighbors],
            "visited_neighbors": [],
            "dfs_level": 0
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
        elif message_type == 'BACK_EDGE':
            return self._handle_back_edge(message)
        elif message_type == 'DATA':
            return self._handle_data(message)
        elif message_type == 'CONTINUE':
            return self._handle_continue(message)
        
        return NodeResponse([])

    def _handle_init(self, message: Action) -> NodeResponse:
        """Initialize algorithm from root."""
        print(f"[Sidon] Node {self.node_id} INITIALIZED as root (DFS)")
        self.algorithm_started = True
        self.phase = "exploring"
        
        # Increment clocks for local action
        self.lamport_clock.increment_internal()
        self.vector_clock.increment_internal()
        
        # Start DFS by selecting a random unvisited neighbor
        if self.unvisited_neighbors:
            next_neighbor = random.choice(list(self.unvisited_neighbors))
            self.unvisited_neighbors.remove(next_neighbor)
            self.visited_neighbors.add(next_neighbor)
            self.children.add(next_neighbor)
            self.current_child_being_explored = next_neighbor
            
            return self._send_explore(next_neighbor, dfs_level=1)
        else:
            # No neighbors, finish immediately
            self.phase = "finished"
            return NodeResponse([])

    def _handle_explore(self, message: Action) -> NodeResponse:
        """Handle EXPLORE message during DFS phase."""
        sender = message.data.get('sender')
        dfs_level = message.data.get('dfs_level', 0)
        
        # Only process if not yet in tree
        if self.parent is not None:
            # Already have a parent, send back edge notification
            print(f"[Sidon] Node {self.node_id} received EXPLORE from {sender} (already in tree)")
            return self._send_back_edge(sender)
        
        print(f"[Sidon] Node {self.node_id} received EXPLORE from {sender}, becoming child in DFS")
        
        self.parent = sender
        self.phase = "exploring"
        self.visited_neighbors.add(sender)
        self.unvisited_neighbors.discard(sender)
        self.collected_data['dfs_level'] = dfs_level + 1
        
        # Increment clocks for local action
        self.lamport_clock.increment_internal()
        self.vector_clock.increment_internal()
        
        # Continue DFS from this node
        if self.unvisited_neighbors:
            next_neighbor = random.choice(list(self.unvisited_neighbors))
            self.unvisited_neighbors.remove(next_neighbor)
            self.visited_neighbors.add(next_neighbor)
            self.children.add(next_neighbor)
            return self._send_explore(next_neighbor, dfs_level=dfs_level + 1)
        else:
            # No more unvisited neighbors, backtrack
            self.phase = "backtracking"
            return self._backtrack()

    def _handle_back_edge(self, message: Action) -> NodeResponse:
        """Handle BACK_EDGE message (indicates cycle in DFS tree)."""
        sender = message.data.get('sender')
        print(f"[Sidon] Node {self.node_id} received BACK_EDGE from {sender}")
        
        # Record back edge
        self.visited_neighbors.add(sender)
        self.unvisited_neighbors.discard(sender)
        
        # Continue with next unvisited neighbor or backtrack
        if self.unvisited_neighbors and self.parent is not None:
            next_neighbor = random.choice(list(self.unvisited_neighbors))
            self.unvisited_neighbors.remove(next_neighbor)
            self.visited_neighbors.add(next_neighbor)
            self.children.add(next_neighbor)
            
            return self._send_explore(next_neighbor, 
                                    dfs_level=self.collected_data.get('dfs_level', 0))
        elif self.parent is not None:
            # No more unvisited neighbors, backtrack
            self.phase = "backtracking"
            return self._backtrack()
        
        return NodeResponse([])

    def _handle_data(self, message: Action) -> NodeResponse:
        """Handle DATA message with aggregated information from children."""
        sender = message.data.get('sender')
        child_data = message.data.get('data', {})
        
        print(f"[Sidon] Node {self.node_id} received DATA from child {sender}")
        
        # Mark child as completed
        self.children_completed.add(sender)
        
        # Aggregate data
        if 'children_data' not in self.collected_data:
            self.collected_data['children_data'] = []
        self.collected_data['children_data'].append(child_data)
        
        # Continue with next unvisited neighbor or backtrack
        if self.unvisited_neighbors:
            self.lamport_clock.increment_internal()
            self.vector_clock.increment_internal()
            
            next_neighbor = random.choice(list(self.unvisited_neighbors))
            self.unvisited_neighbors.remove(next_neighbor)
            self.visited_neighbors.add(next_neighbor)
            self.children.add(next_neighbor)
            
            return self._send_explore(next_neighbor,
                                    dfs_level=self.collected_data.get('dfs_level', 0))
        elif len(self.children_completed) == len(self.children):
            # All children have reported
            if self.parent is not None:
                self.phase = "backtracking"
                return self._backtrack()
            else:
                # Root node, algorithm finished
                self.phase = "finished"
                print(f"[Sidon] Node {self.node_id} (root) finished. DFS complete!")
                return NodeResponse([])
        
        return NodeResponse([])

    def _handle_continue(self, message: Action) -> NodeResponse:
        """Handle CONTINUE message to proceed with next neighbor."""
        # Acknowledge and continue with DFS
        if self.unvisited_neighbors:
            self.lamport_clock.increment_internal()
            self.vector_clock.increment_internal()
            
            next_neighbor = random.choice(list(self.unvisited_neighbors))
            self.unvisited_neighbors.remove(next_neighbor)
            self.visited_neighbors.add(next_neighbor)
            self.children.add(next_neighbor)
            
            return self._send_explore(next_neighbor,
                                    dfs_level=self.collected_data.get('dfs_level', 0))
        elif self.parent is not None:
            self.phase = "backtracking"
            return self._backtrack()
        
        return NodeResponse([])

    def _send_explore(self, target: uuid.UUID, dfs_level: int = 0) -> NodeResponse:
        """Send EXPLORE message to start DFS from this node."""
        self.lamport_clock.increment_internal()
        self.vector_clock.increment_internal()
        
        action = Action(
            {
                'message_type': 'EXPLORE',
                'sender': self.node_id,
                'dfs_level': dfs_level,
                'data': self.collected_data.copy(),
                'lamport_timestamp': self.lamport_clock.get_timestamp(),
                'vector_timestamp': self.vector_clock.get_vector()
            },
            target,
            uuid.uuid4()
        )
        
        self.message_count += 1
        print(f"[Sidon] Node {self.node_id} sending EXPLORE to {target} (DFS level {dfs_level})")
        return NodeResponse([action])

    def _send_back_edge(self, target: uuid.UUID) -> NodeResponse:
        """Send BACK_EDGE message to indicate this is not a tree edge."""
        self.lamport_clock.increment_internal()
        self.vector_clock.increment_internal()
        
        action = Action(
            {
                'message_type': 'BACK_EDGE',
                'sender': self.node_id,
                'lamport_timestamp': self.lamport_clock.get_timestamp(),
                'vector_timestamp': self.vector_clock.get_vector()
            },
            target,
            uuid.uuid4()
        )
        
        self.message_count += 1
        print(f"[Sidon] Node {self.node_id} sending BACK_EDGE to {target}")
        return NodeResponse([action])

    def _backtrack(self) -> NodeResponse:
        """Send aggregated data back to parent (backtracking in DFS)."""
        if self.parent is None:
            print(f"[Sidon] Node {self.node_id} (root) finished DFS")
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
        
        print(f"[Sidon] Node {self.node_id} backtracking, sending DATA to parent {self.parent}")
        self.message_count += 1
        return NodeResponse([action])
