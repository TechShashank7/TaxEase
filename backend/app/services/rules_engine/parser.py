import json
from pathlib import Path
from typing import Dict, Any, List

class RulesParser:
    def __init__(self, rules_file: str = "rules.json"):
        self.rules_path = Path(__file__).parent / rules_file
        self.rules_data = self._load_rules()
        
    def _load_rules(self) -> Dict[str, Any]:
        try:
            with open(self.rules_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading rules from {self.rules_path}: {e}")
            return {"schemes": []}
            
    def get_all_schemes(self) -> List[Dict[str, Any]]:
        return self.rules_data.get("schemes", [])

    def get_scheme(self, scheme_id: str) -> Dict[str, Any]:
        for scheme in self.get_all_schemes():
            if scheme.get("scheme_id") == scheme_id:
                return scheme
        return {}
