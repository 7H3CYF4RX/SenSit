"""JSON export functionality"""
import json
from pathlib import Path
from datetime import datetime
from models.secret import Finding


class JSONExporter:
    """Export findings to JSON"""
    
    def export(self, finding: Finding, output_path: str = None) -> str:
        """Export finding to JSON file"""
        if not output_path:
            # Generate default filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"sensit_report_{timestamp}.json"
        
        # Convert to dict
        data = finding.to_dict()
        
        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return str(output_file)
    
    def export_string(self, finding: Finding) -> str:
        """Export finding to JSON string"""
        data = finding.to_dict()
        return json.dumps(data, indent=2, ensure_ascii=False)
