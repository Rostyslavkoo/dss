from typing import List


class VectorClock:
    """
    Implementation of Vector clock for distributed systems.
    
    A vector of logical clocks, one for each process in the system.
    Used to track causal relationships between events:
    - Increment own process's clock for each local event
    - On receiving a message, set each own clock[i] = max(own clock[i], received[i]) for all i, 
      then increment own process's clock
    """

    def __init__(self, process_id: int, num_processes: int) -> None:
        """Initialize the Vector clock.
        
        Args:
            process_id: The ID of this process (0 to num_processes-1)
            num_processes: Total number of processes in the system
        """
        self.process_id = process_id
        self.clock: List[int] = [0] * num_processes

    def increment(self) -> None:
        """Increment the clock for a local event."""
        self.clock[self.process_id] += 1

    def update(self, received_time: List[int]) -> None:
        """Update the clock on receiving a message from another process.
        
        Args:
            received_time: The vector clock from the received message
        """
        # Update each component with the max value
        for i in range(len(self.clock)):
            self.clock[i] = max(self.clock[i], received_time[i])
        # Then increment own clock
        self.clock[self.process_id] += 1

    def get_time(self) -> List[int]:
        """Get the current clock value.
        
        Returns:
            Copy of the current vector clock
        """
        return self.clock.copy()

    def happens_before(self, other: List[int]) -> bool:
        """Check if this clock happens-before another clock.
        
        For VC1 < VC2, all components of VC1 must be <= corresponding components of VC2,
        and at least one component must be strictly <.
        
        Args:
            other: Another vector clock to compare with
            
        Returns:
            True if this clock happens-before the other clock
        """
        all_less_equal = all(a <= b for a, b in zip(self.clock, other))
        at_least_one_less = any(a < b for a, b in zip(self.clock, other))
        return all_less_equal and at_least_one_less

    def concurrent_with(self, other: List[int]) -> bool:
        """Check if this clock is concurrent with another clock.
        
        Two clocks are concurrent if neither happens-before the other.
        
        Args:
            other: Another vector clock to compare with
            
        Returns:
            True if clocks are concurrent
        """
        # Check if self < other
        self_less = all(a <= b for a, b in zip(self.clock, other)) and \
                    any(a < b for a, b in zip(self.clock, other))
        
        # Check if other < self
        other_less = all(b <= a for a, b in zip(self.clock, other)) and \
                     any(b < a for a, b in zip(self.clock, other))
        
        # Concurrent if neither happens before the other
        return not self_less and not other_less

    def __repr__(self) -> str:
        return f"VectorClock({self.clock})"

    def __eq__(self, other) -> bool:
        """Check if two vector clocks are equal."""
        if not isinstance(other, VectorClock):
            return False
        return self.clock == other.clock

    def __lt__(self, other) -> bool:
        """Check if this clock is less than another (happens-before)."""
        if not isinstance(other, VectorClock):
            return NotImplemented
        return self.happens_before(other.clock)
