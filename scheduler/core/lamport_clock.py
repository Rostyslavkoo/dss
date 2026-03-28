import uuid


class LamportClock:
    """
    Implementation of Lamport's logical clock.
    
    The Lamport clock is a simple counter that:
    1. Increments every time a process performs an action
    2. When receiving a message, it is set to max(local_clock, received_clock) + 1
    """

    def __init__(self, node_id: uuid.UUID):
        """
        Initialize the Lamport clock for a specific node.
        
        :param node_id: The unique identifier of the node
        """
        self.node_id = node_id
        self.timestamp = 0

    def increment(self) -> int:
        """
        Increment the clock (used when performing a local action).
        
        :return: The new timestamp
        """
        self.timestamp += 1
        return self.timestamp

    def update_on_receive(self, received_timestamp: int) -> int:
        """
        Update the clock upon receiving a message.
        
        :param received_timestamp: The timestamp from the received message
        :return: The new timestamp
        """
        self.timestamp = max(self.timestamp, received_timestamp) + 1
        return self.timestamp

    def get_timestamp(self) -> int:
        """
        Get the current timestamp without modifying it.
        
        :return: The current timestamp
        """
        return self.timestamp

    def __repr__(self):
        return f"LamportClock(node={self.node_id}, timestamp={self.timestamp})"
