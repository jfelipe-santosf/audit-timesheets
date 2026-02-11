from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, date
from typing import Optional


class InconsistencyType(Enum):
    """Tipos de inconsistências encontradas"""
    INCOMPLETE_CLOCKS = "BATIDAS INCOMPLETAS"
    MISSING_CLOCKS = "BATIDAS AUSENTES"
    INVALID_TIME_INTERVAL = "INTERVALO DE TEMPO INVÁLIDO"
    DUPLICATE_CLOCKS = "BATIDAS DUPLICADAS"
    OUT_OF_SHIFT_TIME = "FORA DO HORÁRIO DO TURNO"


@dataclass
class AuditResult:
    """Resultado da auditoria de um funcionário"""
    employee_id: int
    audit_date: date
    period_start: date
    period_end: date
    total_days_audited: int = 0
    valid_days: int = 0
    invalid_days: int = 0
    estimated_clocks: int = 0
    not_classified_clocks: int = 0
    inconsistencies: list[dict] = field(default_factory=list)
    
    def add_inconsistency(self, day: date, inconsistency_type: InconsistencyType, details: str = ""):
        """Adiciona uma inconsistência ao resultado"""
        self.inconsistencies.append({
            'date': day,
            'type': inconsistency_type,
            'details': details
        })
    
    def get_validation_rate(self) -> float:
        """Retorna taxa de validação em percentual"""
        if self.total_days_audited == 0:
            return 0.0
        return (self.valid_days / self.total_days_audited) * 100
    
    def is_approved(self, min_rate: float = 95.0) -> bool:
        """Verifica se a auditoria foi aprovada"""
        return self.get_validation_rate() >= min_rate
