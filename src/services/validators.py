from datetime import date, timedelta, datetime
from typing import List, Optional, Dict
from src.models import (
    Employee, TimeRecord, Shift, ClassificationEnum, AuditResult, InconsistencyType
)
from src.repositories import EmployeeRepository, TimeRecordRepository, ShiftRepository
from src.strategies import ReferenceData, EstimationStrategy, HybridStrategy


class TimeNormalizer:
    """Serviço para normalizar horários e agrupar por dia"""
    
    @staticmethod
    def normalize_and_group(records: List[TimeRecord]) -> Dict[date, List[TimeRecord]]:
        """
        Agrupa registros por dia
        Returns: Dict com data como chave e lista de registros ordernados por hora
        """
        grouped = {}
        
        for record in records:
            if record.record_date not in grouped:
                grouped[record.record_date] = []
            grouped[record.record_date].append(record)
        
        # Ordena registros de cada dia por hora
        for day in grouped:
            grouped[day].sort(key=lambda r: r.timestamp)
        
        return grouped


class ShiftIdentifier:
    """Serviço para identificar tipo de turno"""
    
    def __init__(self, shift_repository: ShiftRepository):
        self.shift_repository = shift_repository
    
    def identify_shift(self, shift_id: int) -> Optional[Shift]:
        """Identifica o turno baseado no ID do funcionário"""
        return self.shift_repository.get_shift_by_id(shift_id)


class MandatoryClockValidator:
    """Serviço para validar batidas obrigatórias"""
    
    def __init__(self, shift_repository: ShiftRepository):
        self.shift_repository = shift_repository
    
    def validate_day(
        self,
        shift: Shift,
        daily_records: List[TimeRecord]
    ) -> tuple[bool, List[str]]:
        """
        Valida se as batidas obrigatórias estão presentes
        
        Returns:
            Tuple[valid, missing_clocks_types]
        """
        if len(daily_records) < shift.get_mandatory_clock_count():
            missing = []
            if len(daily_records) == 0:
                missing = ['entrada', 'saída']
            elif len(daily_records) == 1:
                missing = ['saída']  # Assumindo que primeira batida é entrada
            return False, missing
        
        return True, []


class ReferenceSearcher:
    """Serviço para buscar referências de batida"""
    
    def __init__(self, time_record_repository: TimeRecordRepository):
        self.repository = time_record_repository
    
    def search_references(
        self,
        employee_id: int,
        record_date: date,
        shift_id: int
    ) -> ReferenceData:
        """
        Busca referências em 4 fontes:
        1. Mesmo funcionário, mesmo dia
        2. Mesmo funcionário, dia anterior
        3. Mesmo funcionário, dia posterior
        4. Outros funcionários, mesmo turno
        """
        references = ReferenceData()
        
        # 1. Mesmo funcionário, mesmo dia
        references.same_day_records = self.repository.get_records_by_employee_and_period(
            employee_id, record_date, record_date
        )
        
        # 2. Mesmo funcionário, dia anterior
        previous_day = record_date - timedelta(days=1)
        references.previous_day_records = self.repository.get_records_by_employee_and_period(
            employee_id, previous_day, previous_day
        )
        
        # 3. Mesmo funcionário, dia posterior
        next_day = record_date + timedelta(days=1)
        references.next_day_records = self.repository.get_records_by_employee_and_period(
            employee_id, next_day, next_day
        )
        
        # 4. Outros funcionários, mesmo turno
        references.other_employees_records = self.repository.get_records_by_shift_and_date(
            shift_id, record_date
        )
        # Remove registros do mesmo funcionário
        references.other_employees_records = [
            r for r in references.other_employees_records
            if r.employee_id != employee_id
        ]
        
        return references


class ReferenceValidator:
    """Serviço para validar referências encontradas"""
    
    MINIMUM_REFERENCES = 1
    
    @staticmethod
    def is_valid(references: ReferenceData) -> bool:
        """Verifica se há referências válidas suficientes"""
        total_references = (
            len(references.same_day_records) +
            len(references.previous_day_records) +
            len(references.next_day_records) +
            len(references.other_employees_records)
        )
        return total_references >= ReferenceValidator.MINIMUM_REFERENCES


class EstimationCalculator:
    """Serviço para calcular horários estimados"""
    
    # Limites de confiança
    MINIMUM_CONFIDENCE = 0.5
    HIGH_CONFIDENCE_THRESHOLD = 0.8
    
    def __init__(self, strategy: Optional[EstimationStrategy] = None):
        self.strategy = strategy or HybridStrategy()
    
    def calculate(
        self,
        references: ReferenceData,
        shift: Shift,
        missing_clock_type: str
    ) -> tuple[Optional[datetime], float]:
        """Calcula horário estimado usando estratégia configurada"""
        return self.strategy.estimate(references, shift, missing_clock_type)
    
    def meets_confidence_threshold(self, confidence: float) -> bool:
        """Verifica se confiança atende ao limite mínimo"""
        return confidence >= self.MINIMUM_CONFIDENCE
