from pydantic import BaseModel, Field
from typing import List, Any

class SystemEdge(BaseModel):
    from_node: str = Field(description="Unique instance ID string of the source peripheral component.")
    from_interface: str = Field(description="Functional interface name on the peripheral, e.g., 'I2C', 'DIGITAL_IO'.")
    to_node: str = Field(description="Unique instance ID of the target microcontroller unit.")
    to_interface: str = Field(description="Targeted hardware bus name on the MCU, e.g., 'I2C_0', 'DIGITAL_IO'.")

class SystemNode(BaseModel):
    id: str = Field(description="Unique instance ID generated for this component in the project layout.")
    part_id: str = Field(description="Exact database part_id corresponding to our registry library match.")

class AbstractCircuitGraph(BaseModel):
    project_name: str = Field(description="A clean slugified name for the circuit project.")
    nodes: List[SystemNode] = Field(description="List of all physical hardware blocks required for the design.")
    edges: List[SystemEdge] = Field(description="List of logical connection nets linking peripherals to the MCU.")

class DesignRequest(BaseModel):
    prompt: str = Field(..., description="Raw text product requirements from the user.")

class PinMapping(BaseModel):
    peripheral_pin: str
    mcu_pin: str

class RoutedConnection(BaseModel):
    from_node: str
    to_node: str
    protocol: str
    connections: List[PinMapping]

class KiCadNet(BaseModel):
    net_name: str
    nodes: List[str]

class CompilationReport(BaseModel):
    success: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    routed_nets: List[RoutedConnection] = Field(default_factory=list)
    kicad_netlist: List[KiCadNet] = Field(default_factory=list)

# UNIFIED FRONTEND WEB DELIVERY METRIC RESPONSE PACK
class ComprehensiveDesignResponse(BaseModel):
    abstract_graph: AbstractCircuitGraph
    routing_report: CompilationReport
    mermaid_script: str = Field(description="Mermaid.js markdown payload string for instant UI block rendering.")
    pcb_preview_svg: str = Field(description="Raw vector SVG graphics map visualizing physical component groupings.")
    design_explanation: str = Field(description="AI-generated engineering documentation justifying choices.")