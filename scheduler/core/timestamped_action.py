"""
Extended Action class that includes timestamp information for logical clocks
"""
import uuid
from typing import Any, Optional, List, Union


class TimestampedAction:
    """
    Action message with timestamp information for logical clocks.
    
    This extends the base Action with support for Lamport and Vector clocks.
    """

    def __init__(
        self,
        data: dict,
        sender_id: uuid.UUID,
        receiver_id: uuid.UUID,
        action_id: uuid.UUID = None,
        lamport_timestamp: int = None,
        vector_timestamp: List[int] = None
    ):
        """
        Initialize a timestamped action.
        
        Args:
            data: Message data/payload
            sender_id: UUID of sending node
            receiver_id: UUID of receiving node
            action_id: Unique action identifier
            lamport_timestamp: Lamport clock value
            vector_timestamp: Vector clock value
        """
        self.data = data
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.action_id = action_id or uuid.uuid4()
        self.lamport_timestamp = lamport_timestamp
        self.vector_timestamp = vector_timestamp

    def __repr__(self):
        lc_str = f"LC:{self.lamport_timestamp}" if self.lamport_timestamp else ""
        vc_str = f"VC:{self.vector_timestamp}" if self.vector_timestamp else ""
        ts_info = f" [{lc_str}{' ' if lc_str and vc_str else ''}{vc_str}]" if (lc_str or vc_str) else ""
        return (
            f"Message(from:{self.sender_id.hex[:8]} to:{self.receiver_id.hex[:8]} "
            f"data:{self.data}{ts_info})"
        )

    def __str__(self):
        return self.__repr__()
