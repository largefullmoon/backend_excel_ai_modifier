"""
OpenAI service for AI-powered vehicle classification and insurance value generation
"""

import json
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List
from openai import OpenAI

from ..core.config import settings
from ..models.schemas import InsuranceValues, VehicleInfo

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

# Thread pool for async OpenAI calls
executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)


class OpenAIService:
    """Service for OpenAI operations"""
    
    @staticmethod
    def is_configured() -> bool:
        """Check if OpenAI is properly configured"""
        return client is not None and bool(settings.OPENAI_API_KEY)
    
    @staticmethod
    def test_connection() -> Dict[str, any]:
        """Test OpenAI API connectivity"""
        if not OpenAIService.is_configured():
            return {
                "status": "error",
                "message": "OPENAI_API_KEY environment variable not set",
                "configured": False
            }
        
        try:
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            return {
                "status": "success",
                "message": "OpenAI API is configured and accessible",
                "configured": True,
                "model": settings.OPENAI_MODEL
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"OpenAI API error: {str(e)}",
                "configured": False
            }
    
    @staticmethod
    def generate_insurance_values(vehicle_info: VehicleInfo, coverage_type: str) -> InsuranceValues:
        """
        Use OpenAI to generate specific insurance values based on vehicle details
        """
        if not OpenAIService.is_configured():
            logger.warning("OpenAI not configured, using fallback values")
            return OpenAIService._get_fallback_values(vehicle_info.type)
        
        try:
            # Build context about the vehicle
            vehicle_context = f"Vehicle: {vehicle_info.description}"
            if vehicle_info.year:
                vehicle_context += f", Year: {vehicle_info.year}"
            if vehicle_info.model:
                vehicle_context += f", Model: {vehicle_info.model}"
            
            prompt = f"""
            You are an expert insurance underwriter specializing in commercial vehicle insurance in Latin America.
            
            Vehicle Information:
            {vehicle_context}
            Vehicle Type: {vehicle_info.type}
            Coverage: {coverage_type}
            
            Generate realistic insurance values for this vehicle. Consider:
            - Vehicle type, age, and value
            - Market conditions in Latin America
            - Commercial vehicle insurance standards
            - Currency should be in USD for limits
            
            For DANOS MATERIALES (Physical Damage):
            - TRACTOS: Limits typically $80,000-$150,000 USD, Deductibles 8-12%
            - REMOLQUES: Limits typically $40,000-$80,000 USD, Deductibles 5-8%
            - Newer vehicles (2020+): Higher limits, lower deductibles
            - Older vehicles (pre-2015): Lower limits, higher deductibles
            - Premium brands (Freightliner, Volvo, etc.): Higher values
            
            For ROBO TOTAL (Total Theft):
            - TRACTOS: Limits typically $80,000-$150,000 USD, Deductibles 8-12%  
            - REMOLQUES: Limits typically $40,000-$80,000 USD, Deductibles 5-8%
            - Consider vehicle age and theft risk
            - High-value vehicles: Higher limits and deductibles
            
            Respond ONLY in this exact JSON format:
            {{
                "LIMITES": "$US XXX,XXX",
                "DEDUCIBLES": "X.X %"
            }}
            
            Make the values realistic and specific to this vehicle.
            """
            
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert insurance underwriter. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE
            )
            
            # Parse the JSON response
            response_text = response.choices[0].message.content.strip()
            
            # Clean up the response to ensure it's valid JSON
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            values = json.loads(response_text)
            
            # Validate the response has required keys
            if "LIMITES" in values and "DEDUCIBLES" in values:
                logger.info(f"Generated insurance values: {values}")
                return InsuranceValues(**values)
            else:
                raise ValueError("Invalid response format from OpenAI")
                
        except Exception as e:
            import traceback
            logger.error(f"Error generating insurance values: {str(e)}")
            logger.error(f"OpenAI error traceback: {traceback.format_exc()}")
            logger.warning(f"Falling back to default values for {vehicle_info.type}")
            
            return OpenAIService._get_fallback_values(vehicle_info.type)
    
    @staticmethod
    def classify_vehicle(vehicle_description: str, available_types: List[str]) -> str:
        """
        Use OpenAI to intelligently classify vehicle type based on description
        """
        if not OpenAIService.is_configured():
            logger.warning("OpenAI not configured, using fallback classification")
            return OpenAIService._fallback_classification(vehicle_description, available_types)
        
        try:
            prompt = f"""
            You are an expert in vehicle classification for insurance purposes.
            
            Given the following vehicle description: "{vehicle_description}"
            
            Available vehicle categories are: {', '.join(available_types)}
            
            Based on the description, classify this vehicle into one of the available categories.
            Consider the following guidelines:
            - TRACTOS: Truck tractors, prime movers, cab units that pull trailers
            - REMOLQUES: Trailers, semi-trailers, tankers, dollies, any towed equipment
            
            Respond with ONLY the category name (exactly as provided in the list).
            If uncertain, default to TRACTOS.
            """
            
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a vehicle classification expert for insurance purposes."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            classification = response.choices[0].message.content.strip().upper()
            
            # Validate the response is one of our available types
            if classification in available_types:
                return classification
            else:
                logger.warning(f"OpenAI returned unexpected classification '{classification}', defaulting to TRACTOS")
                return "TRACTOS"
                
        except Exception as e:
            logger.error(f"Error in OpenAI classification: {str(e)}")
            return OpenAIService._fallback_classification(vehicle_description, available_types)
    
    @staticmethod
    async def classify_vehicle_async(vehicle_description: str, available_types: List[str]) -> str:
        """
        Async wrapper for OpenAI vehicle classification
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor, 
            OpenAIService.classify_vehicle, 
            vehicle_description, 
            available_types
        )
    
    @staticmethod
    def _get_fallback_values(vehicle_type: str) -> InsuranceValues:
        """Get fallback insurance values when OpenAI is not available"""
        if vehicle_type == "TRACTOS":
            return InsuranceValues(
                LIMITES="$US 120,000",
                DEDUCIBLES="10.0 %"
            )
        else:  # REMOLQUES
            return InsuranceValues(
                LIMITES="$US 60,000", 
                DEDUCIBLES="6.0 %"
            )
    
    @staticmethod
    def _fallback_classification(vehicle_description: str, available_types: List[str]) -> str:
        """Fallback rule-based classification when OpenAI is not available"""
        vehicle_upper = vehicle_description.upper().strip()
        if "TRACTO" in vehicle_upper:
            return "TRACTOS"
        elif any(keyword in vehicle_upper for keyword in ["TANQUE", "REMOLQUE", "DOLLY", "SEMI"]):
            return "REMOLQUES"
        else:
            return "TRACTOS"
