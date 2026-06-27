import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Cpu, Radio, Network, Code, Terminal, Play, CheckCircle, AlertTriangle, CpuIcon } from 'lucide-react';

// Mock response matching your working backend payload structure
const MOCK_BACKEND_RESPONSE = {
  abstract_graph: {
    project_name: "industrial_grain_silo_telemetry_unit",
    nodes: [
      { id: "esp32_01", part_id: "mcu_esp32_devkit", type: "mcu" },
      { id: "can_transceiver_01", part_id: "sensor_mcp2551_can", type: "sub" },
      { id: "can_encoder_01", part_id: "peripheral_can_encoder", type: "sensor" }
    ]
  },
  routing_report: {
    kicad_netlist: [
      { net_name: "CAN_TTL_TX", nodes: ["esp32_01:GPIO25", "can_transceiver_01:TXD"] },
      { net_name: "CAN_TTL_RX", nodes: ["esp32_01:GPIO26", "can_transceiver_01:RXD"] },
      { net_name: "CAN_BUS_HIGH", nodes: ["can_transceiver_01:CANH", "can_encoder_01:CANH"] },
      { net_name: "CAN_BUS_LOW", nodes: ["can_transceiver_01:CANL", "can_encoder_01:CANL"] }
    ]
  },
  pcb_preview_svg: `<svg width="100%" height="100%" viewBox="0 0 500 350" xmlns="http://www.w3.org/2000/svg">
    <rect x="15" y="15" width="470" height="320" rx="12" fill="#0D261A" stroke="#10B981" stroke-width="2" opacity="0.8"/>
    <g stroke="#10B981" stroke-width="0.5" opacity="0.15">
      <path d="M 0,50 L 500,50 M 0,100 L 500,100 M 0,150 L 500,150 M 0,200 L 500,200 M 0,250 L 500,250 M 0,300 L 500,300" />
      <path d="M 50,0 L 50,350 M 100,0 L 100,350 M 150,0 L 150,350 M 200,0 L 200,350 M 250,0 L 250,350 M 300,0 L 300,350 M 350,0 L 350,350 M 400,0 L 400,350 M 450,0 L 450,350" />
    </g>
    <rect x="40" y="110" width="130" height="150" rx="6" fill="#1E293B" stroke="#38BDF8" stroke-width="1.5" />
    <rect x="210" y="140" width="100" height="85" rx="6" fill="#1E293B" stroke="#F59E0B" stroke-width="1.5" />
    <rect x="350" y="125" width="110" height="110" rx="6" fill="#1E293B" stroke="#A855F7" stroke-width="1.5" />
    <text x="50" y="140" font-family="sans-serif" font-size="11" font-weight="bold" fill="#fff">ESP32_01</text>
    <text x="220" y="165" font-family="sans-serif" font-size="10" font-weight="bold" fill="#fff">TRANSCEIVER</text>
    <text x="360" y="150" font-family="sans-serif" font-size="11" font-weight="bold" fill="#fff">CAN_ENCODER</text>
    <path d="M 170,150 L 210,150 M 170,170 L 210,170" stroke="#38BDF8" stroke-width="2" stroke-linecap="round" fill="none" />
    <path d="M 310,170 L 350,170 M 310,190 L 350,190" stroke="#F59E0B" stroke-width="2" stroke-linecap="round" fill="none" />
  </svg>`
};

export default function CompilerDashboard() {
  const [prompt, setPrompt] = useState("");
  const [isCompiling, setIsCompiling] = useState(false);
  const [data, setData] = useState(null);
  const [activeTab, setActiveTab] = useState("pcb"); // pcb | netlist | schematic

  const handleCompile = async () => {
      if (!prompt.trim()) return;
      
      setIsCompiling(true);
      setData(null); // Clear out old states on new compilation passes

  try {
        const response = await fetch("http://127.0.0.1:8000/api/v1/compile", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            prompt: prompt,
            registered_parts: []
          }),
        });

        if (!response.ok) {
          let cleanErrorMessage = `Server Fault [${response.status}]`;
          try {
            const errorData = await response.json();
            if (errorData.detail) {
              // Stringify if Pydantic throws an array validation trace
              cleanErrorMessage = typeof errorData.detail === 'object' 
                ? JSON.stringify(errorData.detail) 
                : errorData.detail;
            }
          } catch (parseErr) {
            // Fallback parsing container
          }
          throw new Error(cleanErrorMessage);
        }

        const result = await response.json();
        setData(result);

      } catch (error) {
        console.error("Network Compilation Fault:", error);
        alert(`System Interruption: ${error.message}`);
      } finally {
        setIsCompiling(false);
      }
    };

  return (
    <div className="min-h-screen bg-[#070A13] text-slate-100 font-sans selection:bg-emerald-500 selection:text-black antialiased">
      
      {/* Premium Apple-style Subtle Header */}
      <header className="sticky top-0 z-50 border-b border-slate-800/60 bg-[#070A13]/80 backdrop-blur-md px-8 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Cpu className="h-4 w-4 text-black font-bold" />
          </div>
          <span className="text-sm font-semibold tracking-[0.2em] uppercase text-white">INTELLICIRCUIT</span>
          <span className="text-xs font-mono bg-slate-800 px-2 py-0.5 rounded text-emerald-400">v2.5-flash</span>
        </div>
        <div className="flex items-center space-x-6 text-xs font-medium tracking-wider text-slate-400">
          <span className="hover:text-white transition-colors cursor-pointer">ENGINE RECON</span>
          <span className="hover:text-white transition-colors cursor-pointer">DOCUMENTATION</span>
          <div className="h-4 w-px bg-slate-800" />
          <span className="text-emerald-400 font-mono">SYS_ONLINE</span>
        </div>
      </header>

      {/* Main Grid Workspack */}
      <main className="max-w-[1600px] mx-auto p-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Hand Input Panel - 5 Columns */}
        <div className="lg:col-span-5 flex flex-col space-y-6">
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm flex flex-col space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold tracking-[0.15em] text-slate-400 uppercase flex items-center space-x-2">
                <Terminal className="h-3.5 w-3.5 text-emerald-400" />
                <span>Hardware Specifications Input</span>
              </label>
            </div>
            
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g., Design a diagnostic grain silo telemetry hub featuring an ESP32 host engine bound to a differential transceiver tracking high speed nodes..."
              className="w-full h-44 bg-slate-950/60 border border-slate-800 focus:border-emerald-500/60 rounded-xl p-4 text-sm font-sans text-slate-200 placeholder-slate-600 focus:outline-none transition-all duration-300 resize-none focus:ring-1 focus:ring-emerald-500/30"
            />

            <button
              onClick={handleCompile}
              disabled={isCompiling || !prompt.trim()}
              className="w-full bg-slate-100 hover:bg-white text-black font-medium text-sm py-3.5 rounded-xl transition-all duration-300 flex items-center justify-center space-x-2 disabled:opacity-30 disabled:cursor-not-allowed group relative overflow-hidden"
            >
              {isCompiling ? (
                <>
                  <svg className="animate-spin h-4 w-4 text-black" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span className="tracking-wide font-semibold">SYNTHESIZING MATRIX COMPILER...</span>
                </>
              ) : (
                <>
                  <Play className="h-3.5 w-3.5 fill-current group-hover:scale-110 transition-transform" />
                  <span className="tracking-wider font-bold uppercase text-xs">Execute Core Compilation</span>
                </>
              )}
            </button>
          </div>

          {/* Device Registry Manifest Card */}
          <div className="bg-slate-900/20 border border-slate-800/40 rounded-2xl p-6">
            <h3 className="text-xs font-bold tracking-[0.15em] text-slate-400 uppercase mb-4">ACTIVE ROUTER TARGET LIST</h3>
            <div className="space-y-2 font-mono text-xs text-slate-500">
              <div className="flex items-center justify-between p-2.5 bg-slate-950/40 border border-slate-900 rounded-lg">
                <span className="text-slate-300">mcu_esp32_devkit</span>
                <span className="text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded text-[10px]">MCU</span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-slate-950/40 border border-slate-900 rounded-lg">
                <span className="text-slate-300">sensor_mcp2551_can</span>
                <span className="text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded text-[10px]">SUB-CIRCUIT</span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-slate-950/40 border border-slate-900 rounded-lg">
                <span className="text-slate-300">sensor_lm35_analog</span>
                <span className="text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded text-[10px]">PERIPHERAL</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Hand Output Panel - 7 Columns */}
        <div className="lg:col-span-7 flex flex-col h-full min-h-[600px]">
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl backdrop-blur-sm flex flex-col h-full overflow-hidden">
            
            {/* View Switch Tabs */}
            <div className="border-b border-slate-800/80 bg-slate-950/40 p-2 flex items-center justify-between">
              <div className="flex space-x-1">
                {["pcb", "netlist"].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`text-xs font-medium tracking-wider px-4 py-2 rounded-lg transition-all duration-200 capitalize ${
                      activeTab === tab 
                        ? 'bg-slate-800 text-white shadow-sm font-semibold' 
                        : 'text-slate-500 hover:text-slate-300'
                    }`}
                  >
                    {tab === "pcb" ? "PCB Engine Preview" : "KiCad Netlist"}
                  </button>
                ))}
              </div>
              <div className="pr-4">
                <div className={`h-2 w-2 rounded-full ${isCompiling ? 'bg-amber-400 animate-pulse' : data ? 'bg-emerald-400' : 'bg-slate-700'}`} />
              </div>
            </div>

            {/* Display Engine Panels Container */}
            <div className="p-6 flex-1 flex flex-col justify-center relative">
              <AnimatePresence mode="wait">
                {isCompiling && (
                  <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 flex flex-col items-center justify-center bg-[#070A13]/90 z-10 space-y-4"
                  >
                    <div className="relative flex items-center justify-center">
                      <div className="h-12 w-12 border-2 border-emerald-500/20 rounded-full animate-ping" />
                      <div className="absolute h-6 w-6 border-2 border-t-emerald-400 border-r-transparent border-b-transparent border-l-transparent rounded-full animate-spin" />
                    </div>
                    <p className="font-mono text-xs text-slate-400 tracking-[0.2em] uppercase animate-pulse">COMPILING SYNTAX NETS...</p>
                  </motion.div>
                )}

                {!data && !isCompiling && (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center p-12 flex flex-col items-center space-y-3"
                  >
                    <Network className="h-8 w-8 text-slate-700 stroke-[1.5]" />
                    <h4 className="text-sm font-semibold text-slate-400 tracking-wider">Awaiting Synthesis Matrix</h4>
                    <p className="text-xs text-slate-600 max-w-xs mx-auto">Fill the requirements configuration context block on the left and submit to verify physical interconnect footprints.</p>
                  </motion.div>
                )}

                {data && !isCompiling && (
                  <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                    className="w-full h-full"
                  >
                    {activeTab === "pcb" && (
                      <div className="w-full h-full flex items-center justify-center bg-slate-950/40 rounded-xl border border-slate-900 p-4 aspect-video overflow-hidden">
                        <div className="w-full h-full transition-transform duration-500 hover:scale-[1.01]" dangerouslySetInnerHTML={{ __html: data.pcb_preview_svg }} />
                      </div>
                    )}

                    {activeTab === "netlist" && (
                      <div className="bg-slate-950/80 rounded-xl border border-slate-900 p-5 font-mono text-xs text-slate-400 h-96 overflow-y-auto space-y-4 custom-scrollbar">
                        <div className="text-[11px] text-slate-600 border-b border-slate-900 pb-2 flex items-center justify-between">
                          <span># KiCad Eeschema Netlist Matrix Generation Output</span>
                          <span className="text-emerald-500">SUCCESS</span>
                        </div>
                        {data.routing_report.kicad_netlist.map((net, idx) => (
                          <div key={idx} className="p-3 bg-slate-900/30 border border-slate-900/60 rounded-lg space-y-1.5">
                            <div className="text-emerald-400 font-bold flex items-center space-x-2">
                              <Code className="h-3 w-3 text-slate-500" />
                              <span>(net (name "{net.net_name}"))</span>
                            </div>
                            <div className="pl-6 space-y-1 text-[11px] text-slate-500">
                              {net.nodes.map((node, nIdx) => {
                                const [comp, pin] = node.split(':');
                                return <div key={nIdx} className="hover:text-slate-300 transition-colors"> (node (ref "{comp}") (pin "{pin}"))</div>;
                              })}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Bottom Diagnostic Action Footer */}
            {data && (
              <div className="border-t border-slate-800/60 bg-slate-950/20 px-6 py-4 flex items-center justify-between text-xs font-mono text-slate-400">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-emerald-400" />
                  <span>Nets: <strong className="text-slate-200">{data.routing_report.kicad_netlist.length} mapped</strong></span>
                </div>
                <div className="text-[11px] text-slate-500">
                  Execution complete in <span className="text-emerald-400">42ms</span>
                </div>
              </div>
            )}

          </div>
        </div>

      </main>
    </div>
  );
}