"""
FastAPI backend for Excel Viewer & AI Modifier
Handles Excel file processing and AI-based data enrichment
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import json
import io
import tempfile
import os
from typing import Dict, Any, List
import uuid

app = FastAPI(title="Excel AI Modifier", version="1.0.0")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample enrichment rules (as provided in the requirements)
SAMPLE_RULES = {
    "coberturas_por_tipo": {
        "TRACTOS": {
            "tipo_cobertura": "AMPLIA",
            "coberturas": {
                "DANOS MATERIALES": {
                    "LIMITES": "VALOR CONVENIDO",
                    "DEDUCIBLES": "10 %"
                },
                "ROBO TOTAL": {
                    "LIMITES": "VALOR CONVENIDO",
                    "DEDUCIBLES": "10 %"
                },
                "RESPONSABILIDAD CIVIL POR DANOS A TERCEROS": {
                    "LIMITES": "$US 6 000 000",
                    "DEDUCIBLES": "N/A"
                },
                "RESPONSABILIDAD CIVIL POR FALLECIMIENTO A PERSONAS": {
                    "LIMITES": "$US 2 000 000",
                    "DEDUCIBLES": "N/A"
                }
            }
        },
        "REMOLQUES": {
            "tipo_cobertura": "AMPLIA",
            "coberturas": {
                "DANOS MATERIALES": {
                    "LIMITES": "VALOR CONVENIDO",
                    "DEDUCIBLES": "5 %"
                },
                "ROBO TOTAL": {
                    "LIMITES": "VALOR CONVENIDO",
                    "DEDUCIBLES": "5 %"
                }
            }
        }
    },
    "reglas_asignacion": {
        "descripcion": "Se debe agregar las columnas LIMITES y DEDUCIBLES de DANOS MATERIALES y ROBO TOTAL basándose en el TIPO_DE_UNIDAD de cada vehículo",
        "columnas_a_agregar": [
            "DANOS MATERIALES LIMITES",
            "DANOS MATERIALES DEDUCIBLES",
            "ROBO TOTAL LIMITES",
            "ROBO TOTAL DEDUCIBLES"
        ],
        "mapeo_columnas": {
            "columna_referencia": "TIPO DE UNIDAD",
            "columna_referencia_index": "A"
        }
    },
    "ejemplo_output_esperado": {
        "descripcion": "Ejemplo de cómo deben lucir las filas después de la transformación",
        "ejemplos": [
            {
                "fila_original": {
                    "TIPO DE UNIDAD": "TRACTO",
                    "Desci.": "TR FREIGHTLINER NEW CASCADIA DD16 510 STD",
                    "MOD": "2022",
                    "NO.SERIE": "3AKJHPDV7NSNC4904"
                },
                "columnas_agregadas": {
                    "DANOS MATERIALES LIMITES": "VALOR CONVENIDO",
                    "DANOS MATERIALES DEDUCIBLES": "10 %",
                    "ROBO TOTAL LIMITES": "VALOR CONVENIDO",
                    "ROBO TOTAL DEDUCIBLES": "10 %"
                }
            }
        ]
    }
}

def apply_ai_enrichment(df: pd.DataFrame, rules: Dict[str, Any]) -> pd.DataFrame:
    """
    Apply AI-based enrichment rules to the DataFrame
    This simulates LLM processing by applying the JSON rules directly
    """
    # Create a copy to avoid modifying the original
    enriched_df = df.copy()
    
    # Get the reference column for mapping
    reference_column = rules["reglas_asignacion"]["mapeo_columnas"]["columna_referencia"]
    
    if reference_column not in enriched_df.columns:
        raise ValueError(f"Reference column '{reference_column}' not found in data")
    
    # Add new columns for enrichment
    new_columns = rules["reglas_asignacion"]["columnas_a_agregar"]
    for col in new_columns:
        enriched_df[col] = ""
    
    # Apply enrichment rules based on vehicle type
    for index, row in enriched_df.iterrows():
        vehicle_type = str(row[reference_column]).upper().strip()
        
        # Map different vehicle types to the coverage categories
        coverage_type = None
        if "TRACTO" in vehicle_type:
            coverage_type = "TRACTOS"
        elif any(keyword in vehicle_type for keyword in ["TANQUE", "REMOLQUE", "DOLLY", "SEMI"]):
            coverage_type = "REMOLQUES"
        else:
            # Default to TRACTOS for unknown types
            coverage_type = "TRACTOS"
        
        # Get coverage rules for this vehicle type
        if coverage_type in rules["coberturas_por_tipo"]:
            coverages = rules["coberturas_por_tipo"][coverage_type]["coberturas"]
            
            # Apply DANOS MATERIALES rules
            if "DANOS MATERIALES" in coverages:
                enriched_df.at[index, "DANOS MATERIALES LIMITES"] = coverages["DANOS MATERIALES"]["LIMITES"]
                enriched_df.at[index, "DANOS MATERIALES DEDUCIBLES"] = coverages["DANOS MATERIALES"]["DEDUCIBLES"]
            
            # Apply ROBO TOTAL rules
            if "ROBO TOTAL" in coverages:
                enriched_df.at[index, "ROBO TOTAL LIMITES"] = coverages["ROBO TOTAL"]["LIMITES"]
                enriched_df.at[index, "ROBO TOTAL DEDUCIBLES"] = coverages["ROBO TOTAL"]["DEDUCIBLES"]
    
    return enriched_df

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Excel AI Modifier API is running"}

@app.get("/sample-data")
async def get_sample_data():
    """
    Returns the JSON rules for enrichment
    """
    return SAMPLE_RULES

@app.post("/export")
async def export_modified_excel(
    file: UploadFile = File(...),
    sheet_name: str = Form(...)
):
    """
    Receives Excel file and sheet name, applies AI enrichment, and returns modified Excel
    """
    try:
        # Validate file type
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(status_code=400, detail="Only .xlsx files are supported")
        
        # Read the uploaded Excel file
        content = await file.read()
        excel_data = pd.ExcelFile(io.BytesIO(content))
        
        # Validate sheet name exists
        if sheet_name not in excel_data.sheet_names:
            raise HTTPException(
                status_code=400, 
                detail=f"Sheet '{sheet_name}' not found. Available sheets: {excel_data.sheet_names}"
            )
        
        # Read the specific sheet
        df = pd.read_excel(io.BytesIO(content), sheet_name=sheet_name)
        
        # Apply AI enrichment
        enriched_df = apply_ai_enrichment(df, SAMPLE_RULES)
        
        # Create a temporary file for the modified Excel
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_filename = temp_file.name
        temp_file.close()
        
        # Write the enriched data to Excel
        with pd.ExcelWriter(temp_filename, engine='openpyxl') as writer:
            # Write all original sheets first
            for sheet in excel_data.sheet_names:
                if sheet == sheet_name:
                    # Write the enriched version of the selected sheet
                    enriched_df.to_excel(writer, sheet_name=sheet, index=False)
                else:
                    # Write original data for other sheets
                    original_df = pd.read_excel(io.BytesIO(content), sheet_name=sheet)
                    original_df.to_excel(writer, sheet_name=sheet, index=False)
        
        # Generate a unique filename for download
        output_filename = f"modified_{file.filename}"
        
        # Return the file
        return FileResponse(
            path=temp_filename,
            filename=output_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        
        # Clean up temp file if it exists
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            os.unlink(temp_filename)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
