"""
Configuration settings for the Excel AI Modifier application
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings"""
    
    # API Configuration
    API_TITLE: str = "Excel AI Modifier"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_MAX_TOKENS: int = 100
    OPENAI_TEMPERATURE: float = 0.3
    
    # Threading Configuration
    MAX_WORKERS: int = 5
    
    # CORS Configuration
    CORS_ORIGINS: list = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]
    
    # File Processing Configuration
    SUPPORTED_FILE_EXTENSIONS: list = ['.xlsx']
    MAX_HEADER_SEARCH_ROWS: int = 5
    DEFAULT_HEADER_ROW: int = 1
    TARGET_COLUMN: str = "TIPO DE UNIDAD"
    
    # Excel Configuration
    NEW_COLUMN_WIDTH: int = 15

# Create settings instance
settings = Settings()

# Sample enrichment rules (moved from main.py)
SAMPLE_RULES: Dict[str, Any] = {
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
