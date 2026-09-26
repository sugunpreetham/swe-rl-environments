from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
import time

class Verdict(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"
    CHEATING_DETECTED = "CHEATING_DETECTED"

@dataclass
class VerifierTierResult:
    tier_name: str
    passed: bool
    duration_ms: float
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TaskEvaluationResult:
    task_id: str
    language: str
    verdict: Verdict
    total_duration_ms: float
    tier_results: List[VerifierTierResult] = field(default_factory=list)
    memory_peak_mb: Optional[float] = None
    applied_patch: Optional[str] = None
    error_summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "language": self.language,
            "verdict": self.verdict.value,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "tiers": [
                {
                    "tier": t.tier_name,
                    "passed": t.passed,
                    "duration_ms": round(t.duration_ms, 2),
                    "message": t.message,
                }
                for t in self.tier_results
            ],
            "memory_peak_mb": round(self.memory_peak_mb, 2) if self.memory_peak_mb else None,
            "error_summary": self.error_summary,
        }
