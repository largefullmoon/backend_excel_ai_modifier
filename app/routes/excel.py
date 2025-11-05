"""
Excel processing routes
"""

import pandas as pd
import io
import os
import logging
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse

from ..core.config import SAMPLE_RULES
from ..utils.excel_utils import detect_header_row, validate_excel_file, get_sheet_names
from ..services.excel_service import ExcelService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/export")
async def export_modified_excel(
    file: UploadFile = File(...),
    sheet_name: str = Form(...)
):
    """
    Receives Excel file and sheet name, applies AI enrichment, and returns modified Excel
    """
    temp_filename = None
    
    try:
        # Validate file type
        if not validate_excel_file(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"Only {', '.join(['.xlsx'])} files are supported"
            )
        
        # Read the uploaded Excel file
        content = await file.read()
        sheet_names = get_sheet_names(content)
        
        # Validate sheet name exists
        if sheet_name not in sheet_names:
            raise HTTPException(
                status_code=400, 
                detail=f"Sheet '{sheet_name}' not found. Available sheets: {sheet_names}"
            )
        
        # Detect the correct header row
        header_row = detect_header_row(content, sheet_name, "TIPO DE UNIDAD")
        logger.info(f"Using header row {header_row} for sheet '{sheet_name}'")
        
        # Read the specific sheet with the correct header row
        df = pd.read_excel(io.BytesIO(content), sheet_name=sheet_name, header=header_row)
        
        # Log available columns for debugging
        logger.info(f"Available columns: {list(df.columns)}")
        
        # Apply AI enrichment
        try:
            logger.info("Starting AI enrichment process...")
            enriched_df = ExcelService.apply_ai_enrichment(df, SAMPLE_RULES)
            logger.info("AI enrichment completed successfully")
        except Exception as enrichment_error:
            logger.error(f"Error during AI enrichment: {str(enrichment_error)}")
            import traceback
            logger.error(f"Enrichment error traceback: {traceback.format_exc()}")
            raise Exception(f"AI enrichment failed: {str(enrichment_error)}")
        
        # Debug: Log the enriched DataFrame structure and sample data
        logger.info(f"Enriched DataFrame columns: {list(enriched_df.columns)}")
        logger.info(f"Enriched DataFrame shape: {enriched_df.shape}")
        
        # Log sample of the new columns data
        new_columns = SAMPLE_RULES["reglas_asignacion"]["columnas_a_agregar"]
        for col in new_columns:
            if col in enriched_df.columns:
                sample_values = enriched_df[col].head(3).tolist()
                logger.info(f"Sample values for '{col}': {sample_values}")
            else:
                logger.error(f"Column '{col}' not found in enriched DataFrame!")
        
        # Create enriched Excel file
        temp_filename = ExcelService.create_enriched_excel(
            content, enriched_df, sheet_name, header_row, SAMPLE_RULES
        )
        
        # Generate a unique filename for download
        output_filename = f"modified_{file.filename}"
        
        # Return the file
        return FileResponse(
            path=temp_filename,
            filename=output_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except HTTPException as he:
        # Re-raise HTTP exceptions (400, etc.)
        logger.error(f"HTTP Exception in export: {he.detail}")
        if temp_filename and os.path.exists(temp_filename):
            os.unlink(temp_filename)
        raise he
    except Exception as e:
        # Log the full error details
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Unexpected error in export endpoint: {str(e)}")
        logger.error(f"Full traceback: {error_details}")
        
        # Clean up temp file if it exists
        if temp_filename and os.path.exists(temp_filename):
            try:
                os.unlink(temp_filename)
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up temp file: {cleanup_error}")
        
        # Return detailed error information
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing file: {str(e)}. Check server logs for details."
        )
