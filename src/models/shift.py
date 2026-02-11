from dataclasses import dataclass, field
from datetime import time
from typing import Optional


@dataclass
class ShiftTolerance:
    """Tolerância de tempo para um turno"""
    name: str
    minutes: int
    is_justified: bool = False


@dataclass
class Shift:
    """Modelo de dados para turno"""
    id: int
    name: str
    start_time: time
    end_time: time
    mandatory_clocks: int = 2  # Entrada e saída no mínimo
    tolerance: Optional[ShiftTolerance] = None
    is_night_shift: bool = False  # Para turnos que cruzam meia-noite
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, Shift):
            return self.id == other.id
        return False
    
    def get_mandatory_clock_count(self) -> int:
        """Retorna quantidade de batidas obrigatórias"""
        return self.mandatory_clocks
