import logging
from typing import Dict, List, Optional
from .graph_schema import NodeType, EdgeType, TaxNode, TaxEdge

logger = logging.getLogger(__name__)

class TaxKnowledgeGraphBuilder:
    """
    Constructs and populates the statutory knowledge graph connecting tax sections,
    schemes, deduction limits, and exclusions.
    Designed for in-memory NetworkX or future Neo4j deployment.
    """
    def __init__(self):
        self.nodes: Dict[str, TaxNode] = {}
        self.edges: List[TaxEdge] = []

    def add_node(self, node_id: str, name: str, node_type: NodeType, properties: Optional[Dict] = None) -> TaxNode:
        node = TaxNode(id=node_id, name=name, node_type=node_type, properties=properties or {})
        self.nodes[node_id] = node
        return node

    def add_edge(self, source_id: str, target_id: str, edge_type: EdgeType, properties: Optional[Dict] = None) -> TaxEdge:
        edge = TaxEdge(source_id=source_id, target_id=target_id, edge_type=edge_type, properties=properties or {})
        self.edges.append(edge)
        return edge

    def build_default_tax_graph(self):
        """Initializes core statutory relationships from the Income Tax Act."""
        # Nodes
        self.add_node("sec_80c", "Section 80C", NodeType.SECTION, {"chapter": "VI-A", "cap": 150000})
        self.add_node("sec_80ccd1b", "Section 80CCD(1B)", NodeType.SECTION, {"chapter": "VI-A", "cap": 50000})
        self.add_node("sec_80d", "Section 80D", NodeType.SECTION, {"chapter": "VI-A", "cap": 100000})
        self.add_node("sec_24b", "Section 24(b)", NodeType.SECTION, {"chapter": "IV-C", "cap": 200000})
        self.add_node("sec_10_13a", "Section 10(13A)", NodeType.SECTION, {"chapter": "III", "type": "exemption"})

        self.add_node("scheme_ppf", "Public Provident Fund (PPF)", NodeType.SCHEME, {"lock_in_years": 15})
        self.add_node("scheme_elss", "ELSS Mutual Funds", NodeType.SCHEME, {"lock_in_years": 3})
        self.add_node("scheme_nps", "National Pension System", NodeType.SCHEME, {"category": "pension"})

        # Edges
        self.add_edge("sec_80c", "scheme_ppf", EdgeType.GOVERNS)
        self.add_edge("sec_80c", "scheme_elss", EdgeType.GOVERNS)
        self.add_edge("sec_80ccd1b", "sec_80c", EdgeType.EXTENDS, {"description": "Additional ₹50,000 over 80C limit"})
        self.add_edge("scheme_nps", "sec_80ccd1b", EdgeType.QUALIFIES_UNDER)

        logger.info(f"Initialized default Tax Knowledge Graph: {len(self.nodes)} nodes, {len(self.edges)} edges.")

tax_graph_builder = TaxKnowledgeGraphBuilder()
