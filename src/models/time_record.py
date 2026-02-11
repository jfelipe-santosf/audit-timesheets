from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional


class ClassificationEnum(Enum):
    """Classificação de batidas"""
    NORMAL = "NORMAL"
    ESTIMATED = "BATIDA ESTIMADA"
    NOT_CLASSIFIED = "NÃO CLASSIFICADA"
    MISSING = "AUSENTE"


@dataclass
class TimeRecord:
    """Modelo de dados para registro de ponto"""
    id: int
    employee_id: int
    timestamp: datetime
    record_date: datetime.date
    shift_id: Optional[int] = None
    classification: ClassificationEnum = ClassificationEnum.NORMAL
    confidence_score: float = 1.0
    reference_sources: list[str] = field(default_factory=list)
    is_valid: bool = True
    observations: str = ""
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, TimeRecord):
            return self.id == other.id
        return False
    
    def is_estimated(self) -> bool:
        return self.classification == ClassificationEnum.ESTIMATED
    
    def is_normal(self) -> bool:
        return self.classification == ClassificationEnum.NORMAL
    
    def is_not_classified(self) -> bool:
        return self.classification == ClassificationEnum.NOT_CLASSIFIED
