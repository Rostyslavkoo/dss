import random
import uuid
from typing import List, Any, Dict

from scheduler.abstract.abstract_node import AbstractNode
from scheduler.core.action import Action
from scheduler.core.mailbox import Mailbox
from scheduler.core.node_response import NodeResponse
from scheduler.core.lamport_clock import LamportClock
from scheduler.core.vector_clock import VectorClock


class TarryNode(AbstractNode):

    def __init__(self, node_id: uuid.UUID, neighbors: List[uuid.UUID], all_node_ids: List[uuid.UUID] = None):
        self.node_id = node_id
        self.mailbox = Mailbox()
        self.neighbors = neighbors
        self.data = 0
        self.transactions = []
        self.parent = None
        self.visited_first_time = False
        self.visited = 0
        
        # Initialize clocks
        self.lamport_clock = LamportClock(node_id)
        
        # Vector clock will be initialized when we know all node IDs
        self.all_node_ids = all_node_ids if all_node_ids else neighbors + [node_id]
        self.vector_clock = VectorClock(node_id, self.all_node_ids)

    def process_action(self, message: Action) -> NodeResponse:
        self.visited += 1
        
        # Update clocks on receiving message
        if message.data.get('lamport_timestamp') is not None:
            received_lamport = message.data.get('lamport_timestamp')
            self.lamport_clock.update_on_receive(received_lamport)
        
        if message.data.get('vector_timestamp') is not None:
            received_vector = message.data.get('vector_timestamp')
            self.vector_clock.update_on_receive(received_vector)
        
        new_message = self.process_message(message)
        
        if new_message is None:
            return NodeResponse([])
        
        receiver = list(new_message.keys())[0]
        return NodeResponse([Action(new_message[receiver], receiver, '11111')])

    def process_message(self, message: Action):
        print(f"Node {self.node_id} processing {message}")
        if message.data.get('message_type') == 'New':
            outbox_messages = self.start_wave(message.data)
        elif message.data.get('message_type') == 'Offer':
            outbox_messages = self.receive_offer(message.data)
        else:
            outbox_messages = {}
        print(f"Node {self.node_id} Data {self.data}")
        print(f"Node {self.node_id} Lamport Clock: {self.lamport_clock.get_timestamp()}")
        print(f"Node {self.node_id} Vector Clock: {self.vector_clock.get_vector()}")
        return outbox_messages

    def start_wave(self, message: dict[str, Any]) -> Dict[uuid.UUID, List[Any]]:
        transaction_data = message.get("transaction_data")
        receiver = random.choice(self.neighbors)
        self.data = transaction_data
        self.transactions.append(receiver)
        self.visited_first_time = True
        
        # Increment clocks for local action
        self.lamport_clock.increment()
        self.vector_clock.increment()
        
        offer = {
            'sender_id': self.node_id,
            'transaction_data': transaction_data,
            'message_type': "Offer",
            'lamport_timestamp': self.lamport_clock.get_timestamp(),
            'vector_timestamp': self.vector_clock.get_vector()
        }
        print(f"Node {self.node_id} STARTED ALGORITHM")
        return {receiver: offer}

    def receive_offer(self, message: Dict[Any, Any]) -> Dict[uuid.UUID, List[Any]]:
        if not self.visited_first_time:
            self.visited_first_time = True
            self.parent = message.get("sender_id")
            self.data = message.get("transaction_data")
        
        # Increment clocks for local action
        self.lamport_clock.increment()
        self.vector_clock.increment()
        
        offer = {
            'sender_id': self.node_id,
            'transaction_data': message.get("transaction_data"),
            'message_type': "Offer",
            'lamport_timestamp': self.lamport_clock.get_timestamp(),
            'vector_timestamp': self.vector_clock.get_vector()
        }
        receiver = None
        for neighbor in self.neighbors:
            if neighbor != self.parent and neighbor not in self.transactions:
                receiver = neighbor
                self.transactions.append(receiver)
                break
        if receiver is None and self.parent:
            receiver = self.parent
            print(f"Node {self.node_id} FINISHED")
        if receiver is None:
            print(f"Node {self.node_id} FINISHED ALGORITHM")
            return None
        return {receiver: offer}
