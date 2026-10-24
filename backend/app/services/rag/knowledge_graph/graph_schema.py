from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class NodeType(str, Enum):
    SECTION = "Section"
    DEDUCTION = "Deduction"
    EXEMPTION = "Exemption"
    SCHEME = "Scheme"
    CONDITION = "Condition"

class EdgeType(str, Enum):
    GOVERNS = "GOVERNS"
    REQUIRES = "REQUIRES"
    EXCLUDES = "EXCLUDES"
    EXTENDS = "EXTENDS"
    QUALIFIES_UNDER = "QUALIFIES_UNDER"

class TaxNode(BaseModel):
    id: str = Field(..., description="Unique node identifier (e.g. sec_80c, scheme_ppf)")
    name: str = Field(..., description="Display name")
    node_type: NodeType
    properties: Dict[str, Any] = Field(default_factory=dict)

class TaxEdge(BaseModel):
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    properties: Dict[str, Any] = Field(default_factory=dict)
