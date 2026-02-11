from datetime import date, timedelta, datetime
from typing import List, Optional, Dict
from src.models import (
    Employee, TimeRecord, Shift, ClassificationEnum, AuditResult, InconsistencyType
)
from src.repositories import EmployeeRepository, TimeRecordRepository, ShiftRepository
from src.services.validators import (
    TimeNormalizer, ShiftIdentifier, MandatoryClockValidator,
    ReferenceSearcher, ReferenceValidator, EstimationCalculator
)


class TimesheetAuditProcessor:
    """Orquestrador principal do processo de auditoria"""
    
    def __init__(
        self,
        employee_repo: EmployeeRepository,
        time_record_repo: TimeRecordRepository,
        shift_repo: ShiftRepository
    ):
        self.employee_repo = employee_repo
        self.time_record_repo = time_record_repo
        self.shift_repo = shift_repo
        
        # Serviços
        self.normalizer = TimeNormalizer()
        self.shift_identifier = ShiftIdentifier(shift_repo)
        self.mandatory_validator = MandatoryClockValidator(shift_repo)
        self.reference_searcher = ReferenceSearcher(time_record_repo)
        self.estimation_calculator = EstimationCalculator()
    
    def process_period(self, start_date: date, end_date: date) -> List[AuditResult]:
        """
        Processa todos os funcionários ativos no período
        Segue o fluxograma principal
        """
        results = []
        
        # Passo B: Definir período (já recebido como parâmetro)
        # Passo C: Carregar funcionários ativos
        active_employees = self.employee_repo.get_active_employees()
        
        # Passo F: Loop sobre funcionários
        for employee in active_employees:
            result = self._process_employee(employee, start_date, end_date)
            results.append(result)
        
        return results
    
    def _process_employee(
        self,
        employee: Employee,
        start_date: date,
        end_date: date
    ) -> AuditResult:
        """Processa um único funcionário"""
        
        # Passo H: Extrair registros do período
        raw_records = self.time_record_repo.get_records_by_employee_and_period(
            employee.id, start_date, end_date
        )
        
        # Passo I: Normalizar horários e agrupar por dia
        daily_records = self.normalizer.normalize_and_group(raw_records)
        
        # Passo J: Identificar tipo de turno
        shift = self.shift_identifier.identify_shift(employee.shift_id)
        if not shift:
            return self._create_empty_result(employee, start_date, end_date)
        
        # Passo K: Definir batidas obrigatórias
        mandatory_count = shift.get_mandatory_clock_count()
        
        # Cria resultado de auditoria
        audit_result = AuditResult(
            employee_id=employee.id,
            audit_date=date.today(),
            period_start=start_date,
            period_end=end_date
        )
        
        # Passo L: Loop sobre cada dia do período
        current_date = start_date
        while current_date <= end_date:
            daily_clocks = daily_records.get(current_date, [])
            
            # Passo M: Validar batidas obrigatórias
            is_valid, missing_types = self.mandatory_validator.validate_day(
                shift, daily_clocks
            )
            
            # Passo N: Processar resultado da validação
            if is_valid:
                # Passo O: Marcar dia como válido
                audit_result.valid_days += 1
            else:
                # Passo P: Registrar inconsistência
                audit_result.invalid_days += 1
                audit_result.add_inconsistency(
                    current_date,
                    InconsistencyType.INCOMPLETE_CLOCKS,
                    f"Batidas obrigatórias faltando: {', '.join(missing_types)}"
                )
            
            audit_result.total_days_audited += 1
            
            # Passo Q: Verificar batidas ausentes e processar
            if missing_types:
                for missing_type in missing_types:
                    self._process_missing_clock(
                        employee, current_date, shift, missing_type, audit_result, daily_clocks
                    )
            
            current_date += timedelta(days=1)
        
        return audit_result
    
    def _process_missing_clock(
        self,
        employee: Employee,
        record_date: date,
        shift: Shift,
        missing_clock_type: str,
        audit_result: AuditResult,
        daily_records: List[TimeRecord]
    ) -> None:
        """
        Processa uma batida ausente
        Segue os passos Q-AC do fluxograma
        """
        # Passo R: Selecionar batida ausente (já feito)
        
        # Passo S: Buscar referências de batida
        references = self.reference_searcher.search_references(
            employee.id, record_date, employee.shift_id
        )
        
        # Passo T: Validar referências encontradas
        is_valid = ReferenceValidator.is_valid(references)
        
        if not is_valid:
            # Passo V: Classificar como NÃO CLASSIFICADA
            self._record_not_classified(employee, record_date, missing_clock_type, audit_result)
        else:
            # Passo W: Calcular horário estimado
            estimated_time, confidence = self.estimation_calculator.calculate(
                references, shift, missing_clock_type
            )
            
            # Passo X: Aplicar estratégia de cálculo (já aplicado em calculate)
            
            # Passo Y: Verificar confiança
            if (estimated_time is not None and 
                self.estimation_calculator.meets_confidence_threshold(confidence)):
                # Passo AA: Classificar como BATIDA ESTIMADA
                # Passo AB: Persistir batida estimada
                self._record_estimated_clock(
                    employee, estimated_time, confidence, references, 
                    audit_result, missing_clock_type
                )
            else:
                # Passo V: Classificar como NÃO CLASSIFICADA
                self._record_not_classified(employee, record_date, missing_clock_type, audit_result)
    
    def _record_estimated_clock(
        self,
        employee: Employee,
        estimated_time: datetime,
        confidence: float,
        references,
        audit_result: AuditResult,
        clock_type: str
    ) -> None:
        """Registra uma batida estimada"""
        estimated_record = TimeRecord(
            id=0,
            employee_id=employee.id,
            timestamp=estimated_time,
            record_date=estimated_time.date(),
            shift_id=employee.shift_id,
            classification=ClassificationEnum.ESTIMATED,
            confidence_score=confidence,
            reference_sources=[
                'same_day' if references.same_day_records else '',
                'previous_day' if references.previous_day_records else '',
                'next_day' if references.next_day_records else '',
                'other_employees' if references.other_employees_records else ''
            ],
            observations=f"Horário estimado para {clock_type} baseado em histórico"
        )
        
        self.time_record_repo.save_record(estimated_record)
        audit_result.estimated_clocks += 1
    
    def _record_not_classified(
        self,
        employee: Employee,
        record_date: date,
        clock_type: str,
        audit_result: AuditResult
    ) -> None:
        """Registra uma batida como não classificada"""
        not_classified_record = TimeRecord(
            id=0,
            employee_id=employee.id,
            timestamp=datetime.combine(record_date, datetime.min.time()),
            record_date=record_date,
            shift_id=employee.shift_id,
            classification=ClassificationEnum.NOT_CLASSIFIED,
            confidence_score=0.0,
            observations=f"Batida de {clock_type} não classificada - insuficiência de referências"
        )
        
        self.time_record_repo.save_record(not_classified_record)
        audit_result.not_classified_clocks += 1
        audit_result.add_inconsistency(
            record_date,
            InconsistencyType.MISSING_CLOCKS,
            f"Batida de {clock_type} não pode ser estimada"
        )
    
    def _create_empty_result(
        self,
        employee: Employee,
        start_date: date,
        end_date: date
    ) -> AuditResult:
        """Cria resultado vazio quando não há turno definido"""
        return AuditResult(
            employee_id=employee.id,
            audit_date=date.today(),
            period_start=start_date,
            period_end=end_date,
            total_days_audited=0,
            observations="Funcionário sem turno definido"
        )
