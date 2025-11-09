"""Audit logging for batch processing operations."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from collections import Counter

from screensanctum.core.regions import Region
from screensanctum.core.detection import PiiType


class AuditLogger:
    """Generates audit logs (receipts) for batch processing jobs.

    This class tracks all files processed in a batch job and generates
    a JSON audit log that summarizes what was redacted. Critical for
    enterprise trust and compliance.
    """

    def __init__(self, output_dir: str, template_id: str):
        """Initialize the audit logger.

        Args:
            output_dir: Directory where the audit log will be saved.
            template_id: ID of the redaction template being used.
        """
        self.output_dir = Path(output_dir)
        self.template_id = template_id
        self.job_started = datetime.now().isoformat()
        self.log_entries: List[Dict[str, Any]] = []

    def log_file(self, original_path: str, new_path: str, regions: List[Region]):
        """Log a processed file with its redaction details.

        Args:
            original_path: Path to the original file.
            new_path: Path to the redacted output file.
            regions: List of Region objects that were redacted.
        """
        # Get relative paths for cleaner logs
        try:
            original_rel = Path(original_path).name
            new_rel = Path(new_path).relative_to(self.output_dir)
        except (ValueError, AttributeError):
            # Fallback to just the filename if relative_to fails
            original_rel = Path(original_path).name
            new_rel = Path(new_path).name

        # Count PII types found in this file
        pii_counts = Counter()
        for region in regions:
            if region.pii_type and region.selected:
                # Convert enum to string for JSON serialization
                pii_type_name = region.pii_type.name.lower() + 's'
                pii_counts[pii_type_name] += 1

        # Create log entry
        entry = {
            "original_file": str(original_rel),
            "redacted_file": str(new_rel),
            "pii_counts": dict(pii_counts),
            "total_redactions": sum(pii_counts.values()),
            "processed_at": datetime.now().isoformat()
        }

        self.log_entries.append(entry)

    def save_log(self) -> str:
        """Save the audit log to a JSON file.

        Returns:
            Path to the saved audit log file.
        """
        # Create unique filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"audit_log_{timestamp}.json"
        log_path = self.output_dir / filename

        # Build the complete audit log structure
        audit_log = {
            "template_id": self.template_id,
            "job_started": self.job_started,
            "job_completed": datetime.now().isoformat(),
            "files_processed": len(self.log_entries),
            "total_redactions": sum(entry["total_redactions"] for entry in self.log_entries),
            "files": self.log_entries
        }

        # Save to JSON file
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(audit_log, f, indent=2, ensure_ascii=False)

        return str(log_path)
