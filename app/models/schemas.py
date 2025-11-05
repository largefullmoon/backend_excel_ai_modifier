"""
Pydantic models and schemas for the Excel AI Modifier application
"""

from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class APIResponse(BaseModel):
    """Base API response model"""
    status: str
    message: str


class OpenAIStatusResponse(APIResponse):
    """OpenAI status response model"""
    configured: bool
    model: Optional[str] = None


class InsuranceValues(BaseModel):
    """Insurance values model"""
    LIMITES: str
    DEDUCIBLES: str


class VehicleInfo(BaseModel):
    """Vehicle information model"""
    description: str
    type: str
    year: Optional[str] = ""
    model: Optional[str] = ""


class EnrichmentResult(BaseModel):
    """Result of enrichment process"""
    success: bool
    rows_processed: int
    errors: List[str] = []
    warnings: List[str] = []


class ExcelProcessingRequest(BaseModel):
    """Excel processing request model"""
    sheet_name: str
    target_column: Optional[str] = "TIPO DE UNIDAD"


class ColumnMapping(BaseModel):
    """Column mapping information"""
    original_name: str
    mapped_name: str
    column_index: int


class ProcessingStats(BaseModel):
    """Processing statistics"""
    total_rows: int
    processed_rows: int
    skipped_rows: int
    new_columns_added: int
    processing_time: float
