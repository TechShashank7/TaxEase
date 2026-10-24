from typing import List, Dict, Any
from .graph_schema import EdgeType, TaxNode, TaxEdge
from .graph_builder import tax_graph_builder

class TaxKnowledgeGraphQuery:
    """
    Executes relational traversals across the tax knowledge graph to find
    dependencies, extensions, and exclusions for given tax sections.
    """
    def __init__(self, builder=tax_graph_builder):
        self.builder = builder

    def get_related_sections(self, section_id: str) -> List[Dict[str, Any]]:
        """Finds all sections that extend, govern, or exclude the given section."""
        results = []
        for edge in self.builder.edges:
            if edge.source_id == section_id:
                target_node = self.builder.nodes.get(edge.target_id)
                if target_node:
                    results.append({
                        "relationship": edge.edge_type.value,
                        "direction": "outgoing",
                        "node": target_node.model_dump(),
                        "properties": edge.properties
                    })
            elif edge.target_id == section_id:
                source_node = self.builder.nodes.get(edge.source_id)
                if source_node:
                    results.append({
                        "relationship": edge.edge_type.value,
                        "direction": "incoming",
                        "node": source_node.model_dump(),
                        "properties": edge.properties
                    })
        return results

tax_graph_query = TaxKnowledgeGraphQuery()
