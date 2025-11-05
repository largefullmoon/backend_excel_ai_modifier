"""
Excel processing utilities
"""

import pandas as pd
import io
import logging
from typing import Dict, Any, List
from ..core.config import settings

logger = logging.getLogger(__name__)


def detect_header_row(file_content: bytes, sheet_name: str, target_column: str = None) -> int:
    """
    Detect which row contains the actual headers by looking for the target column
    """
    if target_column is None:
        target_column = settings.TARGET_COLUMN
        
    try:
        # Try reading first few rows to find headers
        for header_row in range(0, settings.MAX_HEADER_SEARCH_ROWS):
            try:
                df_test = pd.read_excel(
                    io.BytesIO(file_content), 
                    sheet_name=sheet_name, 
                    header=header_row,
                    nrows=1  # Only read first data row to check headers
                )
                
                # Check if target column exists in this header configuration
                if target_column in df_test.columns:
                    logger.info(f"Found header row at index {header_row}")
                    return header_row
                    
                # Also check for similar column names (case insensitive, with variations)
                column_variations = [
                    target_column.upper(),
                    target_column.lower(), 
                    target_column.title(),
                    target_column.replace(" ", "_"),
                    target_column.replace("_", " ")
                ]
                
                for col in df_test.columns:
                    col_clean = str(col).strip()
                    if any(var in col_clean.upper() for var in [v.upper() for v in column_variations]):
                        logger.info(f"Found similar header '{col}' at row {header_row}")
                        return header_row
                        
            except Exception as e:
                logger.debug(f"Error testing header row {header_row}: {str(e)}")
                continue
                
        # Default to configured default if not found
        logger.warning(f"Could not find '{target_column}' column, defaulting to header row {settings.DEFAULT_HEADER_ROW}")
        return settings.DEFAULT_HEADER_ROW
        
    except Exception as e:
        logger.error(f"Error in header detection: {str(e)}")
        return 0  # Default to first row


def find_column_mapping(df: pd.DataFrame, target_column: str) -> str:
    """
    Find the actual column name that matches the target column (with fuzzy matching)
    """
    # Direct match
    if target_column in df.columns:
        return target_column
    
    # Case insensitive match
    for col in df.columns:
        if str(col).upper().strip() == target_column.upper().strip():
            return col
    
    # Fuzzy match - look for key words
    target_words = target_column.upper().split()
    for col in df.columns:
        col_upper = str(col).upper()
        if all(word in col_upper for word in target_words):
            logger.info(f"Mapped '{target_column}' to '{col}' using fuzzy matching")
            return col
    
    # Look for partial matches
    for col in df.columns:
        col_upper = str(col).upper()
        if "TIPO" in col_upper and "UNIDAD" in col_upper:
            logger.info(f"Mapped '{target_column}' to '{col}' using partial matching")
            return col
    
    raise ValueError(f"Could not find column matching '{target_column}'. Available columns: {list(df.columns)}")


def extract_vehicle_info(row: pd.Series, df: pd.DataFrame) -> Dict[str, str]:
    """
    Extract vehicle information (year, model) from a DataFrame row
    """
    year = ""
    model = ""
    
    # Try to find year and model columns
    for col in df.columns:
        col_upper = str(col).upper()
        if any(keyword in col_upper for keyword in ["MOD", "YEAR", "AÑO", "MODELO"]):
            if not model:
                model = str(row[col]).strip()
        elif any(keyword in col_upper for keyword in ["YEAR", "AÑO"]) and col_upper != model:
            year = str(row[col]).strip()
    
    # If year is in the description, try to extract it
    if not year and 'vehicle_description' in locals():
        import re
        year_match = re.search(r'\b(19|20)\d{2}\b', str(row.iloc[0]))
        if year_match:
            year = year_match.group()
    
    return {"year": year, "model": model}


def validate_excel_file(filename: str) -> bool:
    """
    Validate if the file is a supported Excel format
    """
    return any(filename.endswith(ext) for ext in settings.SUPPORTED_FILE_EXTENSIONS)


def get_sheet_names(file_content: bytes) -> List[str]:
    """
    Get all sheet names from an Excel file
    """
    try:
        excel_data = pd.ExcelFile(io.BytesIO(file_content))
        return excel_data.sheet_names
    except Exception as e:
        logger.error(f"Error reading Excel file: {str(e)}")
        return []
