class LamportClock:
    """
    Implementation of Lamport's logical clock for distributed systems.
    
    A simple counter-based clock that satisfies the happens-before relationship:
    - Increment by 1 for each local event
    - On receiving a message, set clock = max(local_clock, received_clock) + 1
    """

    def __init__(self, initial_value: int = 0) -> None:
        """Initialize the Lamport clock.
        
        Args:
            initial_value: Starting value for the clock (default 0)
        """
        self.value = initial_value

    def increment(self) -> None:
        """Increment the clock for a local event."""
        self.value += 1

    def update(self, received_time: int) -> None:
        """Update the clock on receiving a message from another process.
        
        Args:
            received_time: The Lamport clock value from the received message
        """
        self.value = max(self.value, received_time) + 1

    def get_time(self) -> int:
        """Get the current clock value.
        
        Returns:
            Current Lamport clock value
        """
        return self.value

    def __repr__(self) -> str:
        return f"LamportClock({self.value})"
