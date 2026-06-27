from google import genai
from google.genai import types
from app.schemas import AbstractCircuitGraph
from app.config import settings
import logging

logger = logging.getLogger("uvicorn.error")

class GeminiHardwareService:
    def __init__(self):
        if not settings.GEMINI_API_KEY or "YourActual" in settings.GEMINI_API_KEY:
            raise ValueError("CRITICAL: GEMINI_API_KEY is unset or invalid in your .env file.")
        
        # Initialize the native Google GenAI client standard instance
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def parse_requirements(self, user_prompt: str, registered_parts: list[str]) -> AbstractCircuitGraph:
        system_instruction = f"""
        You are the Core System Architect for IntelliCircuit. Your job is to convert raw user product ideas into structured hardware block diagrams.
        
        STRICT COMPILER CONSTRAINTS:
        1. You can ONLY select parts whose 'part_id' values match items in this exact list: {registered_parts}.
        2. Do not hallucinate or manufacture part_ids outside of the provided list.
        3. Create logical edges connecting the peripheral's communication 'from_interface' to the MCU's 'to_interface'.
        """

        # Ensure the model config matches strict schema parameter declarations
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=AbstractCircuitGraph,
            temperature=0.1,
        )

        # Track compilation exceptions transparently
        primary_fault_log = ""

        # --- PRIMARY ATTEMPT: GEMINI 2.5 FLASH ---
        try:
            logger.info(f"Attempting compilation via Primary Engine ({settings.PRIMARY_MODEL})...")
            
            response = self.client.models.generate_content(
                model=settings.PRIMARY_MODEL,
                contents=user_prompt,
                config=config,
            )
            
            if response and response.text:
                return AbstractCircuitGraph.model_validate_json(response.text)
            else:
                raise ValueError("Upstream compiler engine returned an empty response string.")
                
        except Exception as primary_error:
            primary_fault_log = str(primary_error)
            logger.warning(f"Primary Engine ({settings.PRIMARY_MODEL}) failed internally: {primary_fault_log}")

        # --- FALLBACK ATTEMPT: SWAP MODEL TO GEMINI-2.5-FLASH DIRECTLY TO BYPASS 404 ---
        # Since 1.5-flash is failing on the v1beta endpoint, we fallback to a safe, alternate initialization
        try:
            logger.info("Running secondary validation pass using safe model fallback routing...")
            
            # Using standard text configuration without parsing options as a safety baseline if schema initialization failed
            fallback_config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=AbstractCircuitGraph,
                temperature=0.2,
            )
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=user_prompt,
                config=fallback_config,
            )
            return AbstractCircuitGraph.model_validate_json(response.text)
            
        except Exception as secondary_error:
            logger.error("All hardware compiler matrix generation layers are exhausted.")
            # Surface BOTH errors so we can diagnose exactly what the primary block disliked!
            raise RuntimeError(
                f"AI Infrastructure Service Interruption.\n"
                f" -> Primary Engine Fault: {primary_fault_log}\n"
                f" -> Fallback Engine Fault: {str(secondary_error)}"
            )