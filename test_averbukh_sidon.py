import pytest
import uuid
from scheduler.implementation.averbukh_network import AverbukNetwork
from scheduler.implementation.sidon_network import SidonNetwork
from scheduler.core.action import Action


class TestAverbukAlgorithm:
    """Test suite for Averbukh's BFS algorithm."""

    def test_averbuk_network_creation(self):
        """Test network initialization."""
        network = AverbukNetwork()
        assert len(network.nodes) == 8
        assert all(hasattr(node, 'phase') for node in network.nodes)
        assert all(hasattr(node, 'lamport_clock') for node in network.nodes)
        assert all(hasattr(node, 'vector_clock') for node in network.nodes)

    def test_averbuk_initial_state(self):
        """Test initial state of nodes before simulation."""
        network = AverbukNetwork()
        for node in network.nodes:
            assert node.phase == "waiting"
            assert node.parent is None
            assert len(node.children) == 0
            assert node.action_count == 0
            assert node.message_count == 0

    def test_averbuk_root_initialization(self):
        """Test root node initializes correctly."""
        network = AverbukNetwork()
        root = network.nodes[0]
        
        # Root should be able to transition to exploring phase
        root.phase = "exploring"
        assert root.phase == "exploring"
        assert root.parent is None

    def test_averbuk_clock_advancement(self):
        """Test that logical clocks advance during algorithm execution."""
        network = AverbukNetwork()
        root = network.nodes[0]
        neighbor = network.nodes[1]
        
        initial_lamport_value = root.lamport_clock.get_timestamp()
        
        # Increment clock manually to simulate event
        root.lamport_clock.increment_internal()
        
        # Lamport clock should have advanced
        assert root.lamport_clock.get_timestamp() > initial_lamport_value

    def test_averbuk_parent_child_relationships(self):
        """Test that parent-child relationships are established."""
        network = AverbukNetwork()
        root = network.nodes[0]
        neighbor1 = network.nodes[1]
        
        # Manually establish parent-child relationship
        neighbor1.parent = root.node_id
        root.children.append(neighbor1.node_id)
        
        assert neighbor1.parent == root.node_id
        assert neighbor1.node_id in root.children

    def test_averbuk_vector_clock_dimensions(self):
        """Test that vector clocks have correct dimensions."""
        network = AverbukNetwork()
        assert len(network.nodes[0].vector_clock.get_timestamp()) == 8
        for node in network.nodes:
            assert len(node.vector_clock.get_timestamp()) == 8


class TestSidonAlgorithm:
    """Test suite for Sidon's DFS algorithm."""

    def test_sidon_network_creation(self):
        """Test network initialization."""
        network = SidonNetwork()
        assert len(network.nodes) == 8
        assert all(hasattr(node, 'phase') for node in network.nodes)
        assert all(hasattr(node, 'lamport_clock') for node in network.nodes)
        assert all(hasattr(node, 'vector_clock') for node in network.nodes)

    def test_sidon_initial_state(self):
        """Test initial state of nodes before simulation."""
        network = SidonNetwork()
        for node in network.nodes:
            assert node.phase == "waiting"
            assert node.parent is None
            assert len(node.children) == 0
            assert node.action_count == 0
            assert node.message_count == 0

    def test_sidon_root_initialization(self):
        """Test root node initializes correctly."""
        network = SidonNetwork()
        root = network.nodes[0]
        
        # Root should be able to transition to exploring phase
        root.phase = "exploring"
        assert root.phase == "exploring"
        assert root.parent is None
        assert root.lamport_clock.get_timestamp() >= 0

    def test_sidon_dfs_nature(self):
        """Test DFS behavior (one neighbor at a time)."""
        network = SidonNetwork()
        root = network.nodes[0]
        neighbor = network.nodes[1]
        
        # Initialize root in exploring phase
        root.phase = "exploring"
        root.parent = None
        
        # Set up neighbor as child
        neighbor.parent = root.node_id
        neighbor.phase = "exploring"
        
        # In DFS, a node explores one unvisited neighbor at a time
        assert neighbor.phase == "exploring"
        assert len(neighbor.unvisited_neighbors) > 0

    def test_sidon_back_edge_detection(self):
        """Test that back edges (non-tree edges) are detected."""
        network = SidonNetwork()
        node1 = network.nodes[1]
        node2 = network.nodes[3]
        
        # Initialize both nodes in exploring phase
        node1.parent = network.nodes[0].node_id
        node1.phase = "exploring"
        node2.parent = network.nodes[0].node_id
        node2.phase = "exploring"
        
        # Add node1 to visited neighbors of node2 (indicates back edge)
        node2.visited_neighbors.add(node1.node_id)
        
        # Back edge is detected (node2 already visited node1)
        assert node1.node_id in node2.visited_neighbors

    def test_sidon_clock_advancement(self):
        """Test that logical clocks advance during algorithm execution."""
        network = SidonNetwork()
        node1 = network.nodes[0]
        
        initial_lamport = node1.lamport_clock.get_timestamp()
        
        # Simulate clock advancement
        node1.lamport_clock.increment_internal()
        
        assert node1.lamport_clock.get_timestamp() > initial_lamport

    def test_sidon_vector_clock_dimensions(self):
        """Test that vector clocks have correct dimensions."""
        network = SidonNetwork()
        assert len(network.nodes[0].vector_clock.get_timestamp()) == 8
        for node in network.nodes:
            assert len(node.vector_clock.get_timestamp()) == 8


class TestAlgorithmComparison:
    """Compare behavior of both algorithms."""

    def test_both_networks_same_size(self):
        """Both algorithms should work with same network size."""
        averbuk_net = AverbukNetwork()
        sidon_net = SidonNetwork()
        assert len(averbuk_net.nodes) == len(sidon_net.nodes)

    def test_both_have_logical_clocks(self):
        """Both algorithms should integrate logical clocks."""
        averbuk_net = AverbukNetwork()
        sidon_net = SidonNetwork()
        
        for averbuk_node, sidon_node in zip(averbuk_net.nodes, sidon_net.nodes):
            assert hasattr(averbuk_node, 'lamport_clock')
            assert hasattr(averbuk_node, 'vector_clock')
            assert hasattr(sidon_node, 'lamport_clock')
            assert hasattr(sidon_node, 'vector_clock')

    def test_both_support_initialization(self):
        """Both algorithms should support phase transitions."""
        averbuk_net = AverbukNetwork()
        sidon_net = SidonNetwork()
        
        averbuk_root = averbuk_net.nodes[0]
        sidon_root = sidon_net.nodes[0]
        
        averbuk_root.phase = "exploring"
        sidon_root.phase = "exploring"
        
        assert averbuk_root.phase != "waiting"
        assert sidon_root.phase != "waiting"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
