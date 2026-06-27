from typing import Any, Dict

class KiCadNetlistExporter:
    @staticmethod
    def generate_s_expression(project_name: str, nodes: list, routed_nets: list) -> str:
        """
        Converts internal abstract structures into native KiCad v6+ S-Expression Netlist format.
        """
        lines = []
        lines.append(f"(export (version D)")
        lines.append(f"  (design")
        lines.append(f"    (source \"{project_name}.net\")")
        lines.append(f"    (tool \"IntelliCircuit EDA Compiler v1.0\"))")
        
        # 1. Component Footprint Instances Designations
        lines.append("  (components")
        for node in nodes:
            # Establish standard CAD designators based on device types
            prefix = "U" if "mcu" in node.id else "U" if "shifter" in node.id else "SEN"
            lines.append(f"    (comp (ref \"{node.id.upper()}\")")
            lines.append(f"      (value \"{node.part_id}\")")
            lines.append(f"      (footprint \"IntelliCircuit_Library:{node.part_id}_Footprint\"))")
        lines.append("  )")
        
        # 2. Electrical Net Interconnections
        lines.append("  (nets")
        for idx, net in enumerate(routed_nets, start=1):
            lines.append(f"    (net (code \"{idx}\") (name \"{net.net_name}\")")
            for node_pin in net.nodes:
                comp_ref, pin_num = node_pin.split(":")
                lines.append(f"      (node (ref \"{comp_ref.upper()}\") (pin \"{pin_num}\"))")
            lines.append("    )")
        lines.append("  )")
        lines.append(")")
        
        return "\n".join(lines)