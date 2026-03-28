"""
Vector Clock (Terr's Algorithm) - Causal Ordering in Distributed Systems
"""
from typing import List, Dict
from scheduler.clocks.lamport_clock import ClockInterface


class VectorClock(ClockInterface):
    """
    Vector Clock implementation based on Terr's Algorithm.
    
    A vector of logical clocks, one for each process, that provides causal ordering
    of events in a distributed system. It allows us to determine if two events are
    causally related.
    
    Each process maintains a vector where:
    - position i contains the process's knowledge of process i's clock
    - On internal events: increment position for own process
    - On sending: increment own position, attach entire vector
    - On receiving: for each position, take max(local[i], received[i])
    """

    def __init__(self, process_id: int, num_processes: int):
        """
        Initialize Vector Clock.
        
        Args:
            process_id: Unique identifier for this process (0-indexed)
            num_processes: Total number of processes in the system
        """
        self.process_id = process_id
        self.num_processes = num_processes
        # Initialize vector with zeros for all processes
        self.vector: List[int] = [0] * num_processes

    def increment_internal(self) -> None:
        """Increment clock on internal event"""
        self.vector[self.process_id] += 1

    def send_timestamp(self) -> List[int]:
        """
        Get timestamp to send with message.
        Increments own position in vector before sending.
        
        Returns:
            Copy of current vector to attach to message
        """
        self.vector[self.process_id] += 1
        return self.vector.copy()

    def receive_timestamp(self, timestamp: List[int]) -> None:
        """
        Update clock on receiving message.
        For each position, takes max(local[i], received[i]) and then
        increments own position.
        
        Args:
            timestamp: Vector clock received from sender
        """
        if len(timestamp) != self.num_processes:
            raise ValueError(
                f"Received vector of size {len(timestamp)}, "
                f"expected {self.num_processes}"
            )
        
        # Update each position with max
        for i in range(self.num_processes):
            self.vector[i] = max(self.vector[i], timestamp[i])
        
        # Increment own position
        self.vector[self.process_id] += 1

    def get_timestamp(self) -> List[int]:
        """Get current clock value as list"""
        return self.vector.copy()

    def happened_before(self, other: List[int]) -> bool:
        """
        Check if this vector clock happened before another.
        A < B iff A[i] <= B[i] for all i and A != B
        
        Args:
            other: Another vector clock to compare with
            
        Returns:
            True if this vector clock happened before other
        """
        if len(other) != self.num_processes:
            raise ValueError(
                f"Cannot compare with vector of size {len(other)}, "
                f"expected {self.num_processes}"
            )
        
        less_or_equal = all(self.vector[i] <= other[i] for i in range(self.num_processes))
        not_equal = self.vector != other
        return less_or_equal and not_equal

    def concurrent_with(self, other: List[int]) -> bool:
        """
        Check if events are concurrent (causally independent).
        A and B are concurrent iff A did not happen before B and B did not happen before A
        
        Args:
            other: Another vector clock to compare with
            
        Returns:
            True if events are concurrent
        """
        if len(other) != self.num_processes:
            raise ValueError(
                f"Cannot compare with vector of size {len(other)}, "
                f"expected {self.num_processes}"
            )
        
        # Check if self <= other (not strictly)
        self_less_or_equal = all(self.vector[i] <= other[i] for i in range(self.num_processes))
        # Check if other <= self (not strictly)
        other_less_or_equal = all(other[i] <= self.vector[i] for i in range(self.num_processes))
        
        # Concurrent if neither is less than or equal to the other
        return not (self_less_or_equal or other_less_or_equal)

    def __repr__(self) -> str:
        return f"VectorClock({self.vector})"

    def __str__(self) -> str:
        return f"VC[{', '.join(str(v) for v in self.vector)}]"
