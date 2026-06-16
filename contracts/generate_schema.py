'''Generates JSON Schema from the Payment model'''
import json
from pathlib import Path
import yaml
from dataguard.models import Payment
from dataguard.logger import get_logger
logger = get_logger(__name__)

def export_json_schema(output_path: Path) -> dict:
    '''Generates JSON Schema from the Payment model, saves it to a file,
    and returns the schema dictionary.'''
    schema_dict = Payment.model_json_schema()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, mode="w", encoding="utf-8") as file:
        json.dump(schema_dict, file, indent=2, ensure_ascii=False)

    return schema_dict

if __name__ == "__main__":
    _PROJECT_ROOT = Path(__file__).resolve().parents[1]
    config_path = _PROJECT_ROOT / "config.yaml"

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    contract_path = _PROJECT_ROOT / config['pipeline']['contracts_path']
    contract_path /= 'transaction_contract.json'
    res = export_json_schema(contract_path)
    logger.debug('Title: %s, type: %s, keys: %s',
                 res['title'], res['type'], res['properties'].keys())
