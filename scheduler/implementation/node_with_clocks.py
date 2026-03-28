"""
Node implementation with Logical Clock support
"""
import uuid
from typing import List, Optional

from scheduler.abstract.abstract_node import AbstractNode
from scheduler.core.action import Action
from scheduler.core.mailbox import Mailbox
from scheduler.core.node_response import NodeResponse
from scheduler.core.timestamped_action import TimestampedAction
from scheduler.clocks.lamport_clock import LamportClock
from scheduler.clocks.vector_clock import VectorClock


class ClockType:
    """Enumeration of clock types"""
    LAMPORT = "lamport"
    VECTOR = "vector"
    BOTH = "both"


class NodeWithClocks(AbstractNode):
    """
    Node implementation with support for Lamport Clock and Vector Clock.
    
    This node maintains logical clocks to establish causal ordering of events
    in the distributed system.
    """

    def __init__(
        self,
        node_id: uuid.UUID,
        neighbors: List[uuid.UUID],
        process_index: int = 0,
        num_processes: int = 1,
        enable_lamport: bool = True,
        enable_vector: bool = True
    ):
        """
        Initialize node with clock support.
        
        Args:
            node_id: Unique identifier for this node
            neighbors: List of neighbor node IDs
            process_index: Index of this process (for vector clock)
            num_processes: Total number of processes (for vector clock)
            enable_lamport: Enable Lamport clock
            enable_vector: Enable Vector clock
        """
        self.node_id = node_id
        self.mailbox = Mailbox()
        self.neighbors = neighbors
        self.process_index = process_index
        self.num_processes = num_processes
        
        # Initialize clocks
        self.lamport_clock = LamportClock() if enable_lamport else None
        self.vector_clock = VectorClock(process_index, num_processes) if enable_vector else None
        
        # Event history for logging
        self.events = []

    def process_action(self, message) -> NodeResponse:
        """
        Process incoming action/message and update logical clocks.
        
        Args:
            message: Incoming action to process
            
        Returns:
            NodeResponse with outgoing messages
        """
        # Handle both regular Action and TimestampedAction
        if isinstance(message, TimestampedAction):
            return self._process_timestamped_action(message)
        else:
            return self._process_regular_action(message)

    def _process_regular_action(self, message: Action) -> NodeResponse:
        """Process regular action without timestamp information"""
        # Increment clocks on internal event
        if self.lamport_clock:
            self.lamport_clock.increment_internal()
        if self.vector_clock:
            self.vector_clock.increment_internal()
        
        # Log event
        self.events.append({
            'type': 'process',
            'lamport': self.lamport_clock.get_timestamp() if self.lamport_clock else None,
            'vector': self.vector_clock.get_timestamp() if self.vector_clock else None,
            'data': str(message.data) if hasattr(message, 'data') else str(message)
        })
        
        return NodeResponse([])

    def _process_timestamped_action(self, message: TimestampedAction) -> NodeResponse:
        """Process timestamped action and update clocks based on sender's timestamps"""
        # Update clocks with received timestamps
        if message.lamport_timestamp is not None and self.lamport_clock:
            self.lamport_clock.receive_timestamp(message.lamport_timestamp)
        
        if message.vector_timestamp is not None and self.vector_clock:
            self.vector_clock.receive_timestamp(message.vector_timestamp)
        
        # Log event
        self.events.append({
            'type': 'receive',
            'from': message.sender_id.hex[:8],
            'lamport': self.lamport_clock.get_timestamp() if self.lamport_clock else None,
            'vector': self.vector_clock.get_timestamp() if self.vector_clock else None,
            'data': message.data
        })
        
        # Generate response messages to neighbors (optional)
        responses = []
        for neighbor_id in self.neighbors:
            if neighbor_id != message.sender_id:  # Don't send back to sender
                response = self._create_outgoing_message(
                    data=f"ack_{message.action_id.hex[:8]}",
                    receiver_id=neighbor_id
                )
                responses.append(response)
        
        return NodeResponse(responses)

    def _create_outgoing_message(
        self,
        data: any,
        receiver_id: uuid.UUID
    ) -> TimestampedAction:
        """
        Create outgoing message with current clock timestamps.
        
        Args:
            data: Message payload
            receiver_id: Receiver node ID
            
        Returns:
            TimestampedAction with current timestamps
        """
        lamport_ts = self.lamport_clock.send_timestamp() if self.lamport_clock else None
        vector_ts = self.vector_clock.send_timestamp() if self.vector_clock else None
        
        return TimestampedAction(
            data=data,
            sender_id=self.node_id,
            receiver_id=receiver_id,
            lamport_timestamp=lamport_ts,
            vector_timestamp=vector_ts
        )

    def send_message_to(self, neighbor_id: uuid.UUID, data: any) -> TimestampedAction:
        """
        Send message to a specific neighbor with current timestamps.
        
        Args:
            neighbor_id: Receiver node ID
            data: Message payload
            
        Returns:
            TimestampedAction ready to send
        """
        if neighbor_id not in self.neighbors:
            raise ValueError(f"Node {neighbor_id} is not a neighbor")
        
        return self._create_outgoing_message(data, neighbor_id)

    def get_clock_info(self) -> dict:
        """Get current clock values"""
        return {
            'lamport': self.lamport_clock.get_timestamp() if self.lamport_clock else None,
            'vector': self.vector_clock.get_timestamp() if self.vector_clock else None
        }

    def get_events(self) -> List[dict]:
        """Get history of events at this node"""
        return self.events

    def __repr__(self):
        return (
            f"NodeWithClocks({self.node_id.hex[:8]} "
            f"LC:{self.lamport_clock.get_timestamp() if self.lamport_clock else 'N/A'} "
            f"VC:{self.vector_clock.vector if self.vector_clock else 'N/A'})"
        )
