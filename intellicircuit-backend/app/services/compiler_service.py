from typing import Dict, Any, List
from app.schemas import AbstractCircuitGraph, CompilationReport, RoutedConnection, PinMapping, KiCadNet

class IntelliCircuitCompiler:
    @staticmethod
    def route_graph(acg: AbstractCircuitGraph, component_registry: Dict[str, Dict[str, Any]]) -> CompilationReport:
        report = CompilationReport(success=True, errors=[], warnings=[], routed_nets=[], kicad_netlist=[])
        node_map = {node.id: node.part_id for node in acg.nodes}
        nets_accumulator: Dict[str, List[str]] = {}

        def add_to_net(net_name: str, connection_str: str):
            if net_name not in nets_accumulator:
                nets_accumulator[net_name] = []
            if connection_str not in nets_accumulator[net_name]:
                nets_accumulator[net_name].append(connection_str)

        # 1. Locate optional level translator or transceiver helper nodes (SUB-CIRCUIT)
        bridge_node_id = None
        for node_id, part_id in node_map.items():
            part_data = component_registry.get(part_id, {})
            is_subcircuit = part_data.get("category") == "SUB-CIRCUIT"
            is_known_bridge = any(k in part_id.lower() for k in ["transceiver", "mcp2551", "shifter"])
            
            if "mcu" not in node_id.lower() and (is_subcircuit or is_known_bridge):
                bridge_node_id = node_id
                break

        # 2. Iterate and Route Graph Edges safely
        for edge in acg.edges:
            node_a_part = node_map.get(edge.from_node)
            node_b_part = node_map.get(edge.to_node)
            
            data_a = component_registry.get(node_a_part, {})
            data_b = component_registry.get(node_b_part, {})

            if not data_a or not data_b:
                report.warnings.append(f"Skipping edge: Missing registry context for {edge.from_node} or {edge.to_node}")
                continue

            # Direction Guard: Determine dynamically which node is the Host MCU vs Peripheral
            if data_a.get("category") == "MCU" or "mcu" in edge.to_interface.lower():
                mcu_node, mcu_data = edge.from_node, data_a
                p_node, p_data = edge.to_node, data_b
                mcu_interface_key = edge.from_interface
                p_interface_key = edge.to_interface
            else:
                mcu_node, mcu_data = edge.to_node, data_b
                p_node, p_data = edge.from_node, data_a
                mcu_interface_key = edge.to_interface
                p_interface_key = edge.from_interface

            p_interfaces = p_data.get("interfaces", {})
            mcu_buses = mcu_data.get("interfaces", {}).get("buses", {})
            
            # Defensive String Extraction to prevent AttributeErrors on None types
            p_protocol = str(p_interfaces.get("protocol") or "").upper()
            p_pins = p_interfaces.get("pins", {})

            # Generate semantic safety search terms for fallback checks
            p_part_id_lower = str(node_map.get(p_node) or "").lower()
            mcu_interface_lower = mcu_interface_key.lower()
            p_interface_lower = p_interface_key.lower()

            # Loose Matcher: Dynamic Substring Alignment Matrix
            mcu_bus = {}
            for bus_key, bus_val in mcu_buses.items():
                if mcu_interface_key.lower() in bus_key.lower() or bus_key.lower() in mcu_interface_key.lower():
                    mcu_bus = bus_val
                    break

            # --- ROUTING RULE: I2C BUS ---
            if p_protocol == "I2C" or "i2c" in p_interface_lower or "i2c" in mcu_interface_lower:
                sda_m = mcu_bus.get("sda_pin") or mcu_bus.get("sda")
                scl_m = mcu_bus.get("scl_pin") or mcu_bus.get("scl")
                if sda_m and scl_m:
                    p_sda = p_pins.get("SDA") or p_pins.get("sda") or "SDA"
                    p_scl = p_pins.get("SCL") or p_pins.get("scl") or "SCL"
                    
                    report.routed_nets.append(RoutedConnection(
                        from_node=p_node, to_node=mcu_node, protocol="I2C",
                        connections=[PinMapping(peripheral_pin=p_sda, mcu_pin=sda_m),
                                     PinMapping(peripheral_pin=p_scl, mcu_pin=scl_m)]
                    ))
                    add_to_net("I2C_SDA", f"{p_node}:{p_sda}")
                    add_to_net("I2C_SDA", f"{mcu_node}:{sda_m}")
                    add_to_net("I2C_SCL", f"{p_node}:{p_scl}")
                    add_to_net("I2C_SCL", f"{mcu_node}:{scl_m}")

            # --- ROUTING RULE: SPI BUS ---
            elif p_protocol == "SPI" or "spi" in p_interface_lower or "spi" in mcu_interface_lower:
                spi_lines = ["CS", "SCLK", "MOSI", "MISO"]
                mappings = []
                for line in spi_lines:
                    mcu_pin = mcu_bus.get(f"{line.lower()}_pin") or mcu_bus.get(line.lower())
                    p_pin = p_pins.get(line) or p_pins.get(line.lower()) or line
                    if mcu_pin:
                        mappings.append(PinMapping(peripheral_pin=p_pin, mcu_pin=mcu_pin))
                        add_to_net(f"SPI_{line}", f"{p_node}:{p_pin}")
                        add_to_net(f"SPI_{line}", f"{mcu_node}:{mcu_pin}")
                if mappings:
                    report.routed_nets.append(RoutedConnection(from_node=p_node, to_node=mcu_node, protocol="SPI", connections=mappings))

            # --- ROUTING RULE: UART BUS ---
            elif p_protocol == "UART" or "uart" in p_interface_lower or "uart" in mcu_interface_lower:
                tx_m = mcu_bus.get("tx_pin") or mcu_bus.get("tx")
                rx_m = mcu_bus.get("rx_pin") or mcu_bus.get("rx")
                if tx_m and rx_m:
                    p_tx = p_pins.get("TX") or p_pins.get("tx") or "TX"
                    p_rx = p_pins.get("RX") or p_pins.get("rx") or "RX"
                    
                    report.routed_nets.append(RoutedConnection(
                        from_node=p_node, to_node=mcu_node, protocol="UART",
                        connections=[PinMapping(peripheral_pin=p_tx, mcu_pin=rx_m),
                                     PinMapping(peripheral_pin=p_rx, mcu_pin=tx_m)]
                    ))
                    add_to_net("UART_TX_TO_RX", f"{p_node}:{p_tx}")
                    add_to_net("UART_TX_TO_RX", f"{mcu_node}:{rx_m}")
                    add_to_net("UART_RX_TO_TX", f"{p_node}:{p_rx}")
                    add_to_net("UART_RX_TO_TX", f"{mcu_node}:{tx_m}")

            # --- ROUTING RULE: INDUSTRIAL CAN BUS (With Part & Interface Substring Fallbacks) ---
            elif any(k in p_protocol for k in ["CAN", "CAN_BUS"]) or "can" in p_interface_lower or "can" in mcu_interface_lower or "mcp2551" in p_part_id_lower:
                tx_m = mcu_bus.get("tx_pin") or mcu_bus.get("tx")
                rx_m = mcu_bus.get("rx_pin") or mcu_bus.get("rx")
                
                target_bridge = bridge_node_id or "mcp2551_0"
                
                if tx_m and rx_m:
                    add_to_net("CAN_TTL_TX", f"{mcu_node}:{tx_m}")
                    add_to_net("CAN_TTL_TX", f"{target_bridge}:TXD")
                    add_to_net("CAN_TTL_RX", f"{mcu_node}:{rx_m}")
                    add_to_net("CAN_TTL_RX", f"{target_bridge}:RXD")
                    
                    p_canh = p_pins.get("CANH") or p_pins.get("canh") or "CANH"
                    p_canl = p_pins.get("CANL") or p_pins.get("canl") or "CANL"
                    
                    add_to_net("CAN_BUS_HIGH", f"{target_bridge}:CANH")
                    add_to_net("CAN_BUS_HIGH", f"{p_node}:{p_canh}")
                    add_to_net("CAN_BUS_LOW", f"{target_bridge}:CANL")
                    add_to_net("CAN_BUS_LOW", f"{p_node}:{p_canl}")
                    
                    report.routed_nets.append(RoutedConnection(
                        from_node=p_node, to_node=mcu_node, protocol="CAN_DIFFERENTIAL",
                        connections=[PinMapping(peripheral_pin=p_canh, mcu_pin=tx_m), 
                                     PinMapping(peripheral_pin=p_canl, mcu_pin=rx_m)]
                    ))

            # --- ROUTING RULE: ANALOG / ADC CHANNELS (With Part & Interface Substring Fallbacks) ---
            elif p_protocol == "ANALOG" or "analog" in p_interface_lower or "analog" in mcu_interface_lower or "adc" in mcu_interface_lower or "lm35" in p_part_id_lower:
                adc_pin = mcu_bus.get("pin") or mcu_bus.get("adc_pin")
                if not adc_pin and isinstance(mcu_bus, str):
                    adc_pin = mcu_bus
                
                if adc_pin:
                    p_out = p_pins.get("OUT") or p_pins.get("VOUT") or p_pins.get("out") or "VOUT"
                    report.routed_nets.append(RoutedConnection(
                        from_node=p_node, to_node=mcu_node, protocol="ANALOG_ADC",
                        connections=[PinMapping(peripheral_pin=p_out, mcu_pin=adc_pin)]
                    ))
                    add_to_net("ANALOG_SIGNAL_NET", f"{p_node}:{p_out}")
                    add_to_net("ANALOG_SIGNAL_NET", f"{mcu_node}:{adc_pin}")

            # --- ROUTING RULE: PWM CONTROL LINES ---
            elif p_protocol == "PWM" or "pwm" in p_interface_lower or "pwm" in mcu_interface_lower:
                pwm_pin = mcu_bus.get("pin") or mcu_bus.get("pwm_pin")
                if pwm_pin:
                    p_pwm = p_pins.get("PWM") or p_pins.get("pwm") or "PWM"
                    report.routed_nets.append(RoutedConnection(
                        from_node=p_node, to_node=mcu_node, protocol="PWM_CONTROL",
                        connections=[PinMapping(peripheral_pin=p_pwm, mcu_pin=pwm_pin)]
                    ))
                    add_to_net("PWM_CONTROL_NET", f"{p_node}:{p_pwm}")
                    add_to_net("PWM_CONTROL_NET", f"{mcu_node}:{pwm_pin}")

        # Accumulate tracking parameters into structured KiCad output structures
        for net_name, node_pins in nets_accumulator.items():
            report.kicad_netlist.append(KiCadNet(net_name=net_name, nodes=node_pins))

        return report

    @staticmethod
    def generate_mermaid_syntax(acg: AbstractCircuitGraph, report: CompilationReport) -> str:
        lines = [
            "graph LR", 
            "    classDef mcu fill:#2d3748,stroke:#4a5568,stroke-width:2px,color:#fff;", 
            "    classDef sensor fill:#2b6cb0,stroke:#3182ce,stroke-width:2px,color:#fff;", 
            "    classDef sub fill:#d69e2e,stroke:#b7791f,stroke-width:2px,color:#fff;"
        ]
        for node in acg.nodes:
            p_id = node.part_id.lower()
            cls = "mcu" if "mcu" in p_id or "esp32" in p_id else "sub" if any(k in p_id for k in ["transceiver", "shifter", "mcp"]) else "sensor"
            lines.append(f'    {node.id}["{node.id.upper()}<br/>{node.part_id}"]::: {cls}')
            
        for net in report.kicad_netlist:
            if len(net.nodes) >= 2:
                for i in range(len(net.nodes) - 1):
                    s_id, start_pin = net.nodes[i].split(":")
                    e_id, end_pin = net.nodes[i+1].split(":")
                    lines.append(f'    {s_id} ===|"{net.net_name} ({start_pin}➔{end_pin})\"|===> {e_id}')
        return "\n".join(lines)

    @staticmethod
    def generate_pcb_preview_svg(acg: AbstractCircuitGraph) -> str:
        svg_width, svg_height = 500, 350
        lines = [
            f'<svg width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}" xmlns="http://www.w3.org/2000/svg">',
            '  <rect x="15" y="15" width="470" height="320" rx="12" fill="#143d28" stroke="#fff" stroke-width="3" />',
            '  <text x="30" y="45" font-family="monospace" font-size="12" fill="#4ade80" font-weight="bold">INTELLICIRCUIT UNIVERSAL COMPONENT MATRIX</text>'
        ]
        for idx, node in enumerate(acg.nodes):
            p_id = node.part_id.lower()
            if "mcu" in p_id or "esp32" in p_id: 
                x, y, w, h, color = 40, 110, 140, 160, "#2d3748"
            elif any(k in p_id for k in ["transceiver", "mcp", "shifter"]): 
                x, y, w, h, color = 210, 140, 100, 85, "#b7791f"
            else: 
                x, y, w, h, color = 360, 90 + (idx * 70), 110, 55, "#1a365d"
                
            lines.append(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{color}" stroke="#fff" stroke-width="1.5" />')
            lines.append(f'  <text x="{x+10}" y="{y+25}" font-family="sans-serif" font-size="10" font-weight="bold" fill="#fff">{node.id.upper()}</text>')
            lines.append(f'  <text x="{x+10}" y="{y+42}" font-family="sans-serif" font-size="8" fill="#cbd5e0">{node.part_id[:18]}</text>')
        lines.append('</svg>')
        return "\n".join(lines)