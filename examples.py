"""
Exemplo avançado de uso do sistema de auditoria
Demonstra configurações customizadas e interações sofisticadas
"""

from datetime import datetime, date, time, timedelta
from src.models import Employee, TimeRecord, Shift, ShiftTolerance, ClassificationEnum
from src.repositories.memory import (
    InMemoryEmployeeRepository,
    InMemoryTimeRecordRepository,
    InMemoryShiftRepository
)
from src.services import TimesheetAuditProcessor
from src.strategies import WeightedAverageStrategy, RuleBasedStrategy, HybridStrategy
from src.utils import AuditReportGenerator
from src.config import AuditConfig, ConfigManager


def example_custom_strategy():
    """Exemplo usando estratégia customizada"""
    print("\n" + "="*60)
    print("EXEMPLO: Usando Estratégia de Estimação Customizada")
    print("="*60 + "\n")
    
    # Setup
    employee_repo = InMemoryEmployeeRepository()
    time_record_repo = InMemoryTimeRecordRepository()
    shift_repo = InMemoryShiftRepository()
    
    # Criar turno
    shift = Shift(
        id=1, name="Turno Padrão",
        start_time=time(8, 0), end_time=time(17, 0)
    )
    shift_repo.add_shift(shift)
    
    # Criar funcionário
    employee = Employee(id=1, name="Teste", cpf="123", shift_id=1)
    employee_repo.add_employee(employee)
    
    # Adicionar alguns registros
    for day in range(1, 8):
        time_record_repo.add_record(TimeRecord(
            id=0, employee_id=1,
            timestamp=datetime(2026, 1, day, 8, 0),
            record_date=date(2026, 1, day),
            shift_id=1
        ))
        time_record_repo.add_record(TimeRecord(
            id=0, employee_id=1,
            timestamp=datetime(2026, 1, day, 17, 0),
            record_date=date(2026, 1, day),
            shift_id=1
        ))
    
    # Processar com estratégia Weighted Average
    processor = TimesheetAuditProcessor(
        employee_repo, time_record_repo, shift_repo
    )
    
    results = processor.process_period(date(2026, 1, 1), date(2026, 1, 7))
    
    print("Processamento concluído com estratégia Weighted Average")
    print(f"Funcionário processado: {results[0].employee_id}")
    print(f"Dias auditados: {results[0].total_days_audited}")


def example_multiple_employees():
    """Exemplo com múltiplos funcionários e turnos"""
    print("\n" + "="*60)
    print("EXEMPLO: Processando Múltiplos Funcionários e Turnos")
    print("="*60 + "\n")
    
    employee_repo = InMemoryEmployeeRepository()
    time_record_repo = InMemoryTimeRecordRepository()
    shift_repo = InMemoryShiftRepository()
    
    # Criar 3 turnos diferentes
    shifts = [
        Shift(1, "Manhã", time(6, 0), time(14, 0)),
        Shift(2, "Tarde", time(14, 0), time(22, 0)),
        Shift(3, "Noite", time(22, 0), time(6, 0), is_night_shift=True),
    ]
    for shift in shifts:
        shift_repo.add_shift(shift)
    
    # Criar 5 funcionários em diferentes turnos
    employees = []
    for i in range(1, 6):
        emp = Employee(
            id=i,
            name=f"Funcionário {i}",
            cpf=f"{i:03d}.{i:03d}.{i:03d}-{i:02d}",
            shift_id=(i % 3) + 1
        )
        employees.append(emp)
        employee_repo.add_employee(emp)
    
    # Adicionar registros para cada funcionário
    start = date(2026, 1, 1)
    for emp in employees:
        current = start
        while current < start + timedelta(days=20):
            # Adiciona entrada
            time_record_repo.add_record(TimeRecord(
                id=0, employee_id=emp.id,
                timestamp=datetime(
                    current.year, current.month, current.day,
                    shifts[emp.shift_id - 1].start_time.hour,
                    shifts[emp.shift_id - 1].start_time.minute
                ),
                record_date=current,
                shift_id=emp.shift_id,
                classification=ClassificationEnum.NORMAL
            ))
            
            # Adiciona saída
            time_record_repo.add_record(TimeRecord(
                id=0, employee_id=emp.id,
                timestamp=datetime(
                    current.year, current.month, current.day,
                    shifts[emp.shift_id - 1].end_time.hour,
                    shifts[emp.shift_id - 1].end_time.minute
                ),
                record_date=current,
                shift_id=emp.shift_id,
                classification=ClassificationEnum.NORMAL
            ))
            
            current += timedelta(days=1)
    
    # Processar
    processor = TimesheetAuditProcessor(
        employee_repo, time_record_repo, shift_repo
    )
    
    results = processor.process_period(
        start, start + timedelta(days=19)
    )
    
    # Gerar relatório
    report = AuditReportGenerator.generate_summary(results)
    print(report)


def example_invalid_configuration():
    """Exemplo tratando erro de configuração inválida"""
    print("\n" + "="*60)
    print("EXEMPLO: Tratamento de Erro de Configuração")
    print("="*60 + "\n")
    
    try:
        # Tentar criar configuração inválida
        invalid_config = AuditConfig(
            start_date=date(2026, 1, 31),      # Data fim
            end_date=date(2026, 1, 1),         # Data início (invertida!)
            minimum_confidence_threshold=1.5   # Inválido (> 1.0)
        )
        
        if not invalid_config.is_valid():
            raise ValueError("Configuração inválida!")
            
    except ValueError as e:
        print(f"❌ Erro capturado: {e}")
        print("✓ Sistema detectou configuração inválida corretamente\n")
    
    # Criar configuração válida
    valid_config = AuditConfig(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        minimum_confidence_threshold=0.5,
        minimum_validation_rate=90.0
    )
    
    if valid_config.is_valid():
        print("✓ Configuração válida criada com sucesso")
        ConfigManager().set_config(valid_config)
        print(f"✓ Período: {valid_config.start_date} a {valid_config.end_date}")
        print(f"✓ Confiança mínima: {valid_config.minimum_confidence_threshold:.0%}")
        print(f"✓ Taxa mínima de validação: {valid_config.minimum_validation_rate:.0f}%\n")


def example_analysis_missing_clocks():
    """Exemplo analisando batidas ausentes e estimadas"""
    print("\n" + "="*60)
    print("EXEMPLO: Análise de Batidas Ausentes e Estimadas")
    print("="*60 + "\n")
    
    employee_repo = InMemoryEmployeeRepository()
    time_record_repo = InMemoryTimeRecordRepository()
    shift_repo = InMemoryShiftRepository()
    
    # Criar turno simples
    shift = Shift(1, "Turno", time(9, 0), time(18, 0))
    shift_repo.add_shift(shift)
    
    # Criar funcionário
    emp = Employee(1, "João", "123", shift_id=1)
    employee_repo.add_employee(emp)
    
    # Criar semana com batidas faltando em 3 dias
    days_to_process = [
        (1, True),   # dia 1: completo
        (2, False),  # dia 2: faltando saída
        (3, True),   # dia 3: completo
        (4, False),  # dia 4: faltando entrada
        (5, True),   # dia 5: completo
    ]
    
    for day, has_complete in days_to_process:
        record_date = date(2026, 1, day)
        
        # Entrada
        time_record_repo.add_record(TimeRecord(
            id=0, employee_id=1,
            timestamp=datetime(2026, 1, day, 9, 0),
            record_date=record_date,
            shift_id=1
        ))
        
        # Saída (apenas se completo)
        if has_complete:
            time_record_repo.add_record(TimeRecord(
                id=0, employee_id=1,
                timestamp=datetime(2026, 1, day, 18, 0),
                record_date=record_date,
                shift_id=1
            ))
    
    # Processar
    processor = TimesheetAuditProcessor(
        employee_repo, time_record_repo, shift_repo
    )
    
    results = processor.process_period(
        date(2026, 1, 1), date(2026, 1, 5)
    )
    
    result = results[0]
    print(f"Funcionário: {emp.name}")
    print(f"Dias processados: {result.total_days_audited}")
    print(f"Dias válidos: {result.valid_days}")
    print(f"Dias inválidos: {result.invalid_days}")
    print(f"Taxa de validação: {result.get_validation_rate():.1f}%")
    
    print(f"\nBatidas processadas:")
    print(f"  - Batidas estimadas: {result.estimated_clocks}")
    print(f"  - Batidas não classificadas: {result.not_classified_clocks}")
    
    if result.inconsistencies:
        print(f"\nInconsistências encontradas:")
        for inc in result.inconsistencies:
            print(f"  - {inc['date']}: {inc['type'].value}")


if __name__ == "__main__":
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║     EXEMPLOS AVANÇADOS - SISTEMA DE AUDITORIA             ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    example_invalid_configuration()
    example_custom_strategy()
    example_multiple_employees()
    example_analysis_missing_clocks()
    
    print("\n" + "="*60)
    print("Todos os exemplos foram executados com sucesso!")
    print("="*60 + "\n")
