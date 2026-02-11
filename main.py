#!/usr/bin/env python3
"""
Sistema de Auditoria de Registros de Ponto
Implementação baseada no fluxograma de processamento de timesheets
"""

from datetime import datetime, date, time, timedelta
from src.models import (
    Employee, TimeRecord, Shift, ShiftTolerance, ClassificationEnum
)
from src.repositories.memory import (
    InMemoryEmployeeRepository,
    InMemoryTimeRecordRepository,
    InMemoryShiftRepository
)
from src.services import TimesheetAuditProcessor
from src.utils import AuditReportGenerator, LogFormatter
from src.config import AuditConfig, ConfigManager


def setup_test_data():
    """
    Setup de dados de teste
    Cria funcionários, turnos e registros de ponto para exemplo
    """
    
    # Repositórios
    employee_repo = InMemoryEmployeeRepository()
    time_record_repo = InMemoryTimeRecordRepository()
    shift_repo = InMemoryShiftRepository()
    
    # Criar turnos
    shift_morning = Shift(
        id=1,
        name="Turno Manhã",
        start_time=time(8, 0),
        end_time=time(17, 0),
        mandatory_clocks=2,
        tolerance=ShiftTolerance("15 minutos", 15),
        is_night_shift=False
    )
    
    shift_afternoon = Shift(
        id=2,
        name="Turno Tarde",
        start_time=time(13, 0),
        end_time=time(22, 0),
        mandatory_clocks=2,
        tolerance=ShiftTolerance("15 minutos", 15),
        is_night_shift=False
    )
    
    shift_repo.add_shift(shift_morning)
    shift_repo.add_shift(shift_afternoon)
    
    # Criar funcionários
    employee1 = Employee(id=1, name="João Silva", cpf="123.456.789-00", shift_id=1)
    employee2 = Employee(id=2, name="Maria Santos", cpf="987.654.321-00", shift_id=2)
    employee3 = Employee(id=3, name="Pedro Oliveira", cpf="111.222.333-44", shift_id=1, active=False)
    
    employee_repo.add_employee(employee1)
    employee_repo.add_employee(employee2)
    employee_repo.add_employee(employee3)
    
    # Período de auditoria
    start_date = date(2026, 1, 15)
    end_date = date(2026, 1, 22)
    
    # Criar registros de ponto para funcionário 1 (João - Turno Manhã)
    # Dia 15/01 - válido (entrada e saída)
    time_record_repo.add_record(TimeRecord(
        id=0, employee_id=1,
        timestamp=datetime(2026, 1, 15, 8, 5),
        record_date=date(2026, 1, 15),
        shift_id=1,
        classification=ClassificationEnum.NORMAL
    ))
    time_record_repo.add_record(TimeRecord(
        id=0, employee_id=1,
        timestamp=datetime(2026, 1, 15, 17, 0),
        record_date=date(2026, 1, 15),
        shift_id=1,
        classification=ClassificationEnum.NORMAL
    ))
    
    # Dia 16/01 - válido
    time_record_repo.add_record(TimeRecord(
        id=0, employee_id=1,
        timestamp=datetime(2026, 1, 16, 8, 10),
        record_date=date(2026, 1, 16),
        shift_id=1,
        classification=ClassificationEnum.NORMAL
    ))
    time_record_repo.add_record(TimeRecord(
        id=0, employee_id=1,
        timestamp=datetime(2026, 1, 16, 17, 5),
        record_date=date(2026, 1, 16),
        shift_id=1,
        classification=ClassificationEnum.NORMAL
    ))
    
    # Dia 17/01 - apenas entrada (saída ausente)
    time_record_repo.add_record(TimeRecord(
        id=0, employee_id=1,
        timestamp=datetime(2026, 1, 17, 8, 0),
        record_date=date(2026, 1, 17),
        shift_id=1,
        classification=ClassificationEnum.NORMAL
    ))
    
    # Dia 18/01 - válido (fim de semana, pulado)
    
    # Dia 19/01 - válido
    time_record_repo.add_record(TimeRecord(
        id=0, employee_id=1,
        timestamp=datetime(2026, 1, 19, 8, 15),
        record_date=date(2026, 1, 19),
        shift_id=1,
        classification=ClassificationEnum.NORMAL
    ))
    time_record_repo.add_record(TimeRecord(
        id=0, employee_id=1,
        timestamp=datetime(2026, 1, 19, 17, 10),
        record_date=date(2026, 1, 19),
        shift_id=1,
        classification=ClassificationEnum.NORMAL
    ))
    
    # Criar registros de ponto para funcionário 2 (Maria - Turno Tarde)
    # Dia 15/01 - válido
    time_record_repo.add_record(TimeRecord(
        id=0, employee_id=2,
        timestamp=datetime(2026, 1, 15, 13, 5),
        record_date=date(2026, 1, 15),
        shift_id=2,
        classification=ClassificationEnum.NORMAL
    ))
    time_record_repo.add_record(TimeRecord(
        id=0, employee_id=2,
        timestamp=datetime(2026, 1, 15, 22, 0),
        record_date=date(2026, 1, 15),
        shift_id=2,
        classification=ClassificationEnum.NORMAL
    ))
    
    # Dia 16/01 - ausente (nenhuma batida)
    # Será processado como não classificado
    
    # Dia 17/01 - válido
    time_record_repo.add_record(TimeRecord(
        id=0, employee_id=2,
        timestamp=datetime(2026, 1, 17, 13, 10),
        record_date=date(2026, 1, 17),
        shift_id=2,
        classification=ClassificationEnum.NORMAL
    ))
    time_record_repo.add_record(TimeRecord(
        id=0, employee_id=2,
        timestamp=datetime(2026, 1, 17, 22, 5),
        record_date=date(2026, 1, 17),
        shift_id=2,
        classification=ClassificationEnum.NORMAL
    ))
    
    return {
        'employee_repo': employee_repo,
        'time_record_repo': time_record_repo,
        'shift_repo': shift_repo,
        'start_date': start_date,
        'end_date': end_date
    }


def main():
    """
    Função principal que executa o fluxo de auditoria
    """
    print("╔════════════════════════════════════════════════════════════╗")
    print("║       SISTEMA DE AUDITORIA DE REGISTROS DE PONTO           ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    # Passo A: Iniciar processamento
    print("[A] Inicializando processamento de auditoria...\n")
    
    # Setup de dados
    data = setup_test_data()
    employee_repo = data['employee_repo']
    time_record_repo = data['time_record_repo']
    shift_repo = data['shift_repo']
    start_date = data['start_date']
    end_date = data['end_date']
    
    # Passo B: Definir período de apuração
    print(f"[B] Período definido: {start_date} a {end_date}\n")
    
    # Configurar auditoria
    config = AuditConfig(
        start_date=start_date,
        end_date=end_date,
        minimum_confidence_threshold=0.5,
        minimum_validation_rate=95.0,
        estimation_strategy="hybrid"
    )
    ConfigManager().set_config(config)
    
    # Passo C: Carregar funcionários ativos
    print("[C] Carregando funcionários ativos...")
    active_employees = employee_repo.get_active_employees()
    print(f"    ✓ {len(active_employees)} funcionários ativos carregados\n")
    
    # Passo D: Carregar registros de ponto
    print("[D] Carregando registros de ponto...")
    all_records = time_record_repo.get_all_records()
    print(f"    ✓ {len(all_records)} registros carregados\n")
    
    # Passo E: Carregar regras de turno e tolerâncias
    print("[E] Carregando regras de turno e tolerâncias...")
    shifts = shift_repo.get_all_shifts()
    print(f"    ✓ {len(shifts)} turnos carregados\n")
    
    # Passo F: Loop sobre funcionários (implementado no processador)
    print("[F] Processando funcionários...\n")
    
    # Criar processador e executar
    processor = TimesheetAuditProcessor(
        employee_repo,
        time_record_repo,
        shift_repo
    )
    
    # Executar processamento (segue o fluxograma a partir daqui)
    results = processor.process_period(start_date, end_date)
    
    print("\n[Z] Processamento concluído\n")
    
    # Gerar relatórios
    print("════════════════════════════════════════════════════════════")
    report = AuditReportGenerator.generate_summary(results)
    print(report)
    
    # Gerar relatório detalhado para cada funcionário
    print("\n\n")
    for result in results:
        detailed_report = AuditReportGenerator.generate_detailed_report(result)
        print(detailed_report)
    
    # Salvar registros processados (demonstração)
    print("\n════════════════════════════════════════════════════════════")
    print("REGISTROS PROCESSADOS (com classificações)")
    print("════════════════════════════════════════════════════════════\n")
    
    processed_records = time_record_repo.get_all_records()
    for record in processed_records:
        if record.classification != ClassificationEnum.NORMAL:
            print(f"Funcionário {record.employee_id} | {record.record_date} | "
                  f"Classificação: {record.classification.value} | "
                  f"Confiança: {record.confidence_score:.2%}")
    
    print("\n════════════════════════════════════════════════════════════")
    print("Auditoria finalizada com sucesso!")
    print("════════════════════════════════════════════════════════════\n")


if __name__ == "__main__":
    main()
