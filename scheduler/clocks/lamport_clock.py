"""
Lamport Clock - Logical Clock Implementation for Distributed Systems
"""
from abc import ABC, abstractmethod
from typing import Protocol


class ClockInterface(ABC):
    """Base interface for logical clocks"""

    @abstractmethod
    def increment_internal(self) -> None:
        """Increment clock on internal event"""
        pass

    @abstractmethod
    def send_timestamp(self) -> any:
        """Get timestamp to send with message"""
        pass

    @abstractmethod
    def receive_timestamp(self, timestamp: any) -> None:
        """Update clock on receiving message"""
        pass

    @abstractmethod
    def get_timestamp(self) -> any:
        """Get current clock value"""
        pass


class LamportClock(ClockInterface):
    """
    Lamport's Logical Clock implementation.
    
    A logical clock that provides a total ordering of events in a distributed system.
    Each process maintains a clock value that is incremented:
    - By 1 on internal events
    - By 1 and then updated to max(local_clock, received_clock) on message reception
    """

    def __init__(self, initial_value: int = 0):
        """
        Initialize Lamport clock.
        
        Args:
            initial_value: Initial clock value (usually 0)
        """
        self.clock = initial_value

    def increment_internal(self) -> None:
        """Increment clock on internal event"""
        self.clock += 1

    def send_timestamp(self) -> int:
        """
        Get timestamp to send with message.
        Increments clock before sending.
        
        Returns:
            Current clock value to attach to message
        """
        self.clock += 1
        return self.clock

    def receive_timestamp(self, timestamp: int) -> None:
        """
        Update clock on receiving message.
        Sets clock to max(local_clock, received_clock) + 1
        
        Args:
            timestamp: Clock value received from sender
        """
        self.clock = max(self.clock, timestamp) + 1

    def get_timestamp(self) -> int:
        """Get current clock value"""
        return self.clock

    def __repr__(self) -> str:
        return f"LamportClock({self.clock})"
