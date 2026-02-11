"""
Testes unitários para o sistema de auditoria de registros de ponto
"""

import unittest
from datetime import datetime, date, time, timedelta

from src.models import (
    Employee, TimeRecord, Shift, ShiftTolerance, 
    ClassificationEnum, AuditResult, InconsistencyType
)
from src.repositories.memory import (
    InMemoryEmployeeRepository,
    InMemoryTimeRecordRepository,
    InMemoryShiftRepository
)
from src.services import (
    TimeNormalizer, ShiftIdentifier, MandatoryClockValidator,
    EstimationCalculator
)
from src.strategies import ReferenceData, WeightedAverageStrategy
from src.config import AuditConfig


class TestEmployeeModel(unittest.TestCase):
    """Testes para o modelo Employee"""
    
    def test_employee_creation(self):
        emp = Employee(1, "João", "123.456.789-00", shift_id=1)
        self.assertEqual(emp.id, 1)
        self.assertEqual(emp.name, "João")
        self.assertTrue(emp.active)
    
    def test_employee_equality(self):
        emp1 = Employee(1, "João", "123", shift_id=1)
        emp2 = Employee(1, "Maria", "456", shift_id=2)
        self.assertEqual(emp1, emp2)  # Igualdade por ID
    
    def test_employee_hash(self):
        emp = Employee(1, "João", "123", shift_id=1)
        employees_set = {emp}
        self.assertEqual(len(employees_set), 1)


class TestTimeRecordModel(unittest.TestCase):
    """Testes para o modelo TimeRecord"""
    
    def test_time_record_creation(self):
        record = TimeRecord(
            id=1,
            employee_id=1,
            timestamp=datetime(2026, 1, 15, 8, 0),
            record_date=date(2026, 1, 15)
        )
        self.assertEqual(record.classification, ClassificationEnum.NORMAL)
        self.assertTrue(record.is_normal())
        self.assertFalse(record.is_estimated())
    
    def test_time_record_estimated(self):
        record = TimeRecord(
            id=1,
            employee_id=1,
            timestamp=datetime(2026, 1, 15, 8, 0),
            record_date=date(2026, 1, 15),
            classification=ClassificationEnum.ESTIMATED,
            confidence_score=0.75
        )
        self.assertTrue(record.is_estimated())
        self.assertEqual(record.confidence_score, 0.75)


class TestShiftModel(unittest.TestCase):
    """Testes para o modelo Shift"""
    
    def test_shift_creation(self):
        shift = Shift(
            id=1,
            name="Manhã",
            start_time=time(8, 0),
            end_time=time(17, 0)
        )
        self.assertEqual(shift.name, "Manhã")
        self.assertEqual(shift.get_mandatory_clock_count(), 2)
    
    def test_shift_night(self):
        shift = Shift(
            id=1,
            name="Noite",
            start_time=time(22, 0),
            end_time=time(6, 0),
            is_night_shift=True
        )
        self.assertTrue(shift.is_night_shift)


class TestAuditResultModel(unittest.TestCase):
    """Testes para o modelo AuditResult"""
    
    def test_audit_result_creation(self):
        result = AuditResult(
            employee_id=1,
            audit_date=date.today(),
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31)
        )
        self.assertEqual(result.employee_id, 1)
        self.assertEqual(result.valid_days, 0)
    
    def test_audit_result_validation_rate(self):
        result = AuditResult(
            employee_id=1,
            audit_date=date.today(),
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            total_days_audited=10,
            valid_days=9,
            invalid_days=1
        )
        self.assertAlmostEqual(result.get_validation_rate(), 90.0)
    
    def test_audit_result_approval(self):
        # Aprovado (95%)
        result_approved = AuditResult(
            employee_id=1,
            audit_date=date.today(),
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            total_days_audited=20,
            valid_days=19
        )
        self.assertTrue(result_approved.is_approved())
        
        # Reprovado (90%)
        result_rejected = AuditResult(
            employee_id=1,
            audit_date=date.today(),
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            total_days_audited=20,
            valid_days=18
        )
        self.assertFalse(result_rejected.is_approved())
    
    def test_add_inconsistency(self):
        result = AuditResult(
            employee_id=1,
            audit_date=date.today(),
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31)
        )
        result.add_inconsistency(
            date(2026, 1, 15),
            InconsistencyType.INCOMPLETE_CLOCKS,
            "Faltam 2 batidas"
        )
        self.assertEqual(len(result.inconsistencies), 1)
        self.assertEqual(result.inconsistencies[0]['type'], InconsistencyType.INCOMPLETE_CLOCKS)


class TestRepositories(unittest.TestCase):
    """Testes para os repositórios em memória"""
    
    def test_employee_repository(self):
        repo = InMemoryEmployeeRepository()
        emp = Employee(1, "João", "123", shift_id=1)
        repo.add_employee(emp)
        
        retrieved = repo.get_employee_by_id(1)
        self.assertEqual(retrieved.name, "João")
    
    def test_employee_repository_active_filter(self):
        repo = InMemoryEmployeeRepository()
        emp1 = Employee(1, "João", "123", shift_id=1, active=True)
        emp2 = Employee(2, "Maria", "456", shift_id=1, active=False)
        repo.add_employee(emp1)
        repo.add_employee(emp2)
        
        active = repo.get_active_employees()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].id, 1)
    
    def test_time_record_repository(self):
        repo = InMemoryTimeRecordRepository()
        record = TimeRecord(
            id=0,
            employee_id=1,
            timestamp=datetime(2026, 1, 15, 8, 0),
            record_date=date(2026, 1, 15),
            shift_id=1
        )
        repo.save_record(record)
        
        records = repo.get_records_by_employee_and_period(
            1, date(2026, 1, 15), date(2026, 1, 15)
        )
        self.assertEqual(len(records), 1)
    
    def test_shift_repository(self):
        repo = InMemoryShiftRepository()
        shift = Shift(1, "Manhã", time(8, 0), time(17, 0))
        repo.add_shift(shift)
        
        retrieved = repo.get_shift_by_id(1)
        self.assertEqual(retrieved.name, "Manhã")


class TestTimeNormalizer(unittest.TestCase):
    """Testes para o serviço TimeNormalizer"""
    
    def test_normalize_and_group(self):
        records = [
            TimeRecord(0, 1, datetime(2026, 1, 1, 17, 0), date(2026, 1, 1), 1),
            TimeRecord(0, 1, datetime(2026, 1, 1, 8, 0), date(2026, 1, 1), 1),
            TimeRecord(0, 1, datetime(2026, 1, 2, 9, 0), date(2026, 1, 2), 1),
        ]
        
        grouped = TimeNormalizer.normalize_and_group(records)
        
        # Verifica agrupamento
        self.assertEqual(len(grouped), 2)
        self.assertIn(date(2026, 1, 1), grouped)
        self.assertIn(date(2026, 1, 2), grouped)
        
        # Verifica ordenação
        day1_records = grouped[date(2026, 1, 1)]
        self.assertEqual(day1_records[0].timestamp.hour, 8)
        self.assertEqual(day1_records[1].timestamp.hour, 17)


class TestMandatoryClockValidator(unittest.TestCase):
    """Testes para o validador de batidas obrigatórias"""
    
    def test_validate_complete_day(self):
        shift = Shift(1, "Turno", time(8, 0), time(17, 0), mandatory_clocks=2)
        validator = MandatoryClockValidator(InMemoryShiftRepository())
        
        records = [
            TimeRecord(1, 1, datetime(2026, 1, 1, 8, 0), date(2026, 1, 1), 1),
            TimeRecord(2, 1, datetime(2026, 1, 1, 17, 0), date(2026, 1, 1), 1),
        ]
        
        is_valid, missing = validator.validate_day(shift, records)
        self.assertTrue(is_valid)
        self.assertEqual(len(missing), 0)
    
    def test_validate_incomplete_day(self):
        shift = Shift(1, "Turno", time(8, 0), time(17, 0), mandatory_clocks=2)
        validator = MandatoryClockValidator(InMemoryShiftRepository())
        
        records = [
            TimeRecord(1, 1, datetime(2026, 1, 1, 8, 0), date(2026, 1, 1), 1),
        ]
        
        is_valid, missing = validator.validate_day(shift, records)
        self.assertFalse(is_valid)
        self.assertIn('saída', missing)


class TestEstimationCalculator(unittest.TestCase):
    """Testes para o calculador de estimativas"""
    
    def test_estimation_with_references(self):
        shift = Shift(1, "Turno", time(8, 0), time(17, 0))
        calculator = EstimationCalculator()
        
        references = ReferenceData()
        references.same_day_records = [
            TimeRecord(1, 1, datetime(2026, 1, 1, 8, 10), date(2026, 1, 1), 1),
        ]
        
        estimated, confidence = calculator.calculate(
            references, shift, 'entrada'
        )
        
        self.assertIsNotNone(estimated)
        self.assertGreater(confidence, 0)
    
    def test_estimation_no_references(self):
        shift = Shift(1, "Turno", time(8, 0), time(17, 0))
        calculator = EstimationCalculator()
        
        references = ReferenceData()
        
        estimated, confidence = calculator.calculate(
            references, shift, 'entrada'
        )
        
        self.assertIsNone(estimated)
        self.assertEqual(confidence, 0.0)
    
    def test_confidence_threshold(self):
        calculator = EstimationCalculator()
        
        self.assertTrue(calculator.meets_confidence_threshold(0.5))
        self.assertFalse(calculator.meets_confidence_threshold(0.4))


class TestAuditConfig(unittest.TestCase):
    """Testes para a configuração de auditoria"""
    
    def test_valid_config(self):
        config = AuditConfig(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            minimum_confidence_threshold=0.5
        )
        self.assertTrue(config.is_valid())
    
    def test_invalid_dates(self):
        config = AuditConfig(
            start_date=date(2026, 1, 31),
            end_date=date(2026, 1, 1),  # Invertido
            minimum_confidence_threshold=0.5
        )
        self.assertFalse(config.is_valid())
    
    def test_invalid_confidence(self):
        config = AuditConfig(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            minimum_confidence_threshold=1.5  # > 1.0
        )
        self.assertFalse(config.is_valid())


class TestWeightedAverageStrategy(unittest.TestCase):
    """Testes para a estratégia de média ponderada"""
    
    def test_same_day_priority(self):
        strategy = WeightedAverageStrategy()
        shift = Shift(1, "Turno", time(8, 0), time(17, 0))
        
        references = ReferenceData()
        # Registros do mesmo dia (maior peso)
        references.same_day_records = [
            TimeRecord(1, 1, datetime(2026, 1, 1, 8, 20), date(2026, 1, 1), 1),
            TimeRecord(2, 1, datetime(2026, 1, 1, 8, 30), date(2026, 1, 1), 1),
        ]
        # Registros de outro dia (menor peso)
        references.other_employees_records = [
            TimeRecord(3, 2, datetime(2026, 1, 1, 9, 0), date(2026, 1, 1), 1),
        ]
        
        estimated, confidence = strategy.estimate(references, shift, 'entrada')
        
        # A estimativa deve estar mais próxima dos registros do mesmo dia (8:25)
        self.assertIsNotNone(estimated)
        self.assertGreaterEqual(estimated.hour, 8)
        self.assertGreaterEqual(estimated.minute, 20)  # Deve estar próximo de 8:25


if __name__ == '__main__':
    unittest.main(verbosity=2)
