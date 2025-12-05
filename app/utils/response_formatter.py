from typing import Dict, Any
from datetime import datetime


def format_response(result: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
    return {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "analysis_type": analysis_type,
        "result": result,
        "metadata": {
            "version": "1.0.0",
            "service": "TruthBot"
        }
    }

