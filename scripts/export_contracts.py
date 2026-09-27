"""Export the actual implementation contracts, rather than a disconnected design file."""
import json
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'backend'))
from app.main import create_app
from app.config import Settings
from app.schemas import Analysis, Plan
app = create_app(Settings(app_env='test', _env_file=None))
(root/'docs/openapi.json').write_text(json.dumps(app.openapi(), indent=2))
(root/'docs/analysis.schema.json').write_text(json.dumps(Analysis.model_json_schema(), indent=2))
(root/'docs/research-plan.schema.json').write_text(json.dumps(Plan.model_json_schema(), indent=2))
print('Exported actual API and model schemas.')
