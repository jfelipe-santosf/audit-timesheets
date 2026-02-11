from dataclasses import dataclass
from typing import Optional
from datetime import date


@dataclass
class Employee:
    """Modelo de dados para funcionário"""
    id: int
    name: str
    cpf: str
    shift_id: int
    active: bool = True
    hire_date: Optional[date] = None
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, Employee):
            return self.id == other.id
        return False
