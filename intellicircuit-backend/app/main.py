import traceback
import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi.responses import Response
from google.genai.errors import ServerError, APIError

from app.config import settings
from app.database import get_db
from app.schemas import DesignRequest, ComprehensiveDesignResponse
from app.services.gemini_service import GeminiHardwareService
from app.services.compiler_service import IntelliCircuitCompiler
from app.services.kicad_exporter import KiCadNetlistExporter

# Standardize system telemetry using the Uvicorn runtime log engine
logger = logging.getLogger("uvicorn.error")

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, docs_url="/docs")

# Global CORS Configuration 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai_service = GeminiHardwareService()

@app.get("/health", tags=["System Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database pool failure: {str(e)}")


@app.post("/api/v1/compile", response_model=ComprehensiveDesignResponse, tags=["Compiler Core"])
async def generate_circuit_architecture(request: DesignRequest, db: AsyncSession = Depends(get_db)):
    """
    Core Compilation Endpoint:
    Ingests text spec inputs, provisions part schemas, maps unknown components, 
    routes pin nets deterministically, and builds out CAD / visual layers.
    """
    try:
        # 1. Gather all baseline components from PostgreSQL using clean dictionary mapping
        query_result = await db.execute(text(
            "SELECT part_id, display_name, category, logic_level_v, interfaces FROM components"
        ))
        rows = query_result.fetchall()
        
        component_registry = {}
        registered_parts = []
        for row in rows:
            # Safe tuple unpacking mapping standard configurations
            part_id, disp_name, cat, volt, inter = row
            registered_parts.append(part_id)
            component_registry[part_id] = {
                "part_id": part_id, "display_name": disp_name, "category": cat, "logic_level_v": volt, "interfaces": inter
            }
            
        if not registered_parts:
            logger.warning("Database component table contains 0 records. Utilizing dynamic discovery mode entirely.")

        # 2. Extract targeted component requirements block topology using primary service engines
        # Synchronized to request.user_prompt to prevent attribute validation faults!
        try:
            circuit_graph = await ai_service.parse_requirements(
                user_prompt=request.prompt,
                registered_parts=registered_parts
            )
        except (ServerError, APIError) as e:
            logger.warning(f"Primary compiler hit execution anomalies: {str(e)}. Attempting secondary fallback pipeline...")
            circuit_graph = await ai_service.parse_requirements_fallback(
                user_prompt=request.prompt,
                registered_parts=registered_parts
            )
        
        # 3. INTERCEPTOR LOOP: Dynamic runtime discovery for unlisted parts
        for node in circuit_graph.nodes:
            logger.info(f"[Telemetry Tracer] Node found in Graph: ID='{node.part_id}', Name='{getattr(node, 'display_name', 'None')}'")
            if node.part_id not in component_registry:
                logger.info(f"Discovery Engine intercept triggered: Spec-hunting for {node.part_id}...")
                try:
                    discovered_spec = await ai_service.discover_unknown_component(node.part_id)
                except Exception as discovery_err:
                    logger.warning(f"Component discovery failed for {node.part_id}: {str(discovery_err)}. Running predictive protocol allocation.")
                    from app.schemas import SyntheticComponentSpec
                    
                    # 🧠 Predictive Interface Inference Engine
                    part_id_lower = node.part_id.lower()
                    if any(x in part_id_lower for x in ["stepper", "tmc", "drv", "spi", "display_tft"]):
                        inferred_interfaces = {
                            "protocol": "SPI",
                            "pins": {"SCLK": "SCLK", "MOSI": "MOSI", "MISO": "MISO", "CS": "CS"}
                        }
                    elif any(x in part_id_lower for x in ["motor", "pwm", "servo", "fet", "gate"]):
                        inferred_interfaces = {
                            "protocol": "PWM",
                            "pins": {"PWM_IN": "PWM_IN", "GND": "GND"}
                        }
                    else:
                        inferred_interfaces = {
                            "protocol": "I2C",
                            "pins": {"SDA": "SDA", "SCL": "SCL"}
                        }

                    discovered_spec = SyntheticComponentSpec(
                        part_id=node.part_id,
                        display_name=f"Generic {node.part_id.upper().replace('_', ' ')}",
                        category="PERIPHERAL",
                        logic_level_v=3.3,
                        interfaces=inferred_interfaces
                    )
                
                component_registry[discovered_spec.part_id] = {
                    "part_id": discovered_spec.part_id,
                    "display_name": discovered_spec.display_name,
                    "category": discovered_spec.category,
                    "logic_level_v": discovered_spec.logic_level_v,
                    "interfaces": discovered_spec.interfaces
                }
                node.part_id = discovered_spec.part_id

        # 4. Route physical tracking networks deterministically 
        routing_report = IntelliCircuitCompiler.route_graph(circuit_graph, component_registry)
        
        # 5. Extract UI render specs
        mermaid_script = IntelliCircuitCompiler.generate_mermaid_syntax(circuit_graph, routing_report)
        pcb_preview_svg = IntelliCircuitCompiler.generate_pcb_preview_svg(circuit_graph)
        
        # 6. Safe Justification Compilation Layer
        try:
            explanation_prompt = (
                f"Write a 2-paragraph hardware design justification analysis for user requirement: '{request.prompt}'. "
                f"Explain components: {[node.part_id for node in circuit_graph.nodes]} and how their bus layouts interact."
            )
            explanation_response = await ai_service.client.aio.models.generate_content(
                model='gemini-2.5-flash', contents=explanation_prompt
            )
            design_explanation = explanation_response.text if explanation_response.text else "System parsed successfully."
        except Exception as expl_err:
            logger.warning(f"Context explanation generation dropped offline: {str(expl_err)}. Reverting to fallback summary.")
            design_explanation = (
                f"Circuit successfully compiled. Hardware layout contains "
                f"{len(circuit_graph.nodes)} devices interconnected via automated bus topologies."
            )

        return ComprehensiveDesignResponse(
            abstract_graph=circuit_graph,
            routing_report=routing_report,
            mermaid_script=mermaid_script,
            pcb_preview_svg=pcb_preview_svg,
            design_explanation=design_explanation
        )
        
    except Exception as e:
        logger.error("=== INTELLICIRCUIT COMPILER PIPELINE CRASH ===")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Architecture Synthesis Fault: {str(e)}"
        )


@app.post("/api/v1/export/kicad", tags=["CAD Export Core"])
async def export_to_kicad_file(request: DesignRequest, db: AsyncSession = Depends(get_db)):
    """
    Transforms the underlying system configuration map directly into a downloadable KiCad physical .net file stream.
    """
    try:
        query_result = await db.execute(text("SELECT part_id, display_name, category, logic_level_v, interfaces FROM components"))
        component_registry = {
            row[0]: {"part_id": row[0], "display_name": row[1], "category": row[2], "logic_level_v": row[3], "interfaces": row[4]} 
            for row in query_result.fetchall()
        }
        
        circuit_graph = await ai_service.parse_requirements(
            user_prompt=request.prompt, 
            registered_parts=list(component_registry.keys())
        )
        routing_report = IntelliCircuitCompiler.route_graph(circuit_graph, component_registry)
        
        s_expr_netlist = KiCadNetlistExporter.generate_s_expression(
            project_name=circuit_graph.project_name,
            nodes=circuit_graph.nodes,
            routed_nets=routing_report.kicad_netlist
        )
        
        headers = {"Content-Disposition": f"attachment; filename={circuit_graph.project_name}.net"}
        return Response(content=s_expr_netlist, media_type="text/plain", headers=headers)
        
    except Exception as e:
        logger.error(f"CAD compilation processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CAD Compilation Export Fault: {str(e)}")