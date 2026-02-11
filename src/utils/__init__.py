from datetime import datetime, date
from typing import List
from src.models import AuditResult, TimeRecord, InconsistencyType


class AuditReportGenerator:
    """Gerador de relatórios de auditoria"""
    
    @staticmethod
    def generate_summary(results: List[AuditResult]) -> str:
        """Gera resumo da auditoria"""
        if not results:
            return "Nenhum resultado de auditoria disponível"
        
        total_employees = len(results)
        total_valid_days = sum(r.valid_days for r in results)
        total_invalid_days = sum(r.invalid_days for r in results)
        total_estimated = sum(r.estimated_clocks for r in results)
        total_not_classified = sum(r.not_classified_clocks for r in results)
        
        total_days = total_valid_days + total_invalid_days
        validation_rate = (total_valid_days / total_days * 100) if total_days > 0 else 0
        
        report = f"""
╔════════════════════════════════════════════════════════════╗
║               RELATÓRIO DE AUDITORIA DE PONTO              ║
╚════════════════════════════════════════════════════════════╝

RESUMO GERAL:
─────────────
• Funcionários auditados: {total_employees}
• Dias auditados: {total_days}
• Dias válidos: {total_valid_days}
• Dias inválidos: {total_invalid_days}
• Taxa de validação: {validation_rate:.2f}%

ESTIMATIVAS:
────────────
• Batidas estimadas: {total_estimated}
• Batidas não classificadas: {total_not_classified}

DETALHES POR FUNCIONÁRIO:
──────────────────────────
"""
        
        for result in results:
            rate = result.get_validation_rate()
            status = "✓ APROVADO" if result.is_approved() else "✗ REPROVADO"
            
            report += f"""
Funcionário ID: {result.employee_id}
  Período: {result.period_start} a {result.period_end}
  Dias auditados: {result.total_days_audited}
  Taxa de validação: {rate:.2f}%
  Status: {status}
  Inconsistências: {len(result.inconsistencies)}
  Batidas estimadas: {result.estimated_clocks}
  Batidas não classificadas: {result.not_classified_clocks}
"""
            
            if result.inconsistencies:
                report += "  Inconsistências:\n"
                for inc in result.inconsistencies:
                    report += f"    - {inc['date']}: {inc['type'].value} ({inc['details']})\n"
        
        return report
    
    @staticmethod
    def generate_detailed_report(result: AuditResult) -> str:
        """Gera relatório detalhado de um funcionário"""
        report = f"""
════════════════════════════════════════════════════════════
                AUDITORIA DETALHADA
════════════════════════════════════════════════════════════

Funcionário: {result.employee_id}
Período: {result.period_start} a {result.period_end}
Data da auditoria: {result.audit_date}

ESTATÍSTICAS:
─────────────
Total de dias auditados: {result.total_days_audited}
Dias válidos: {result.valid_days}
Dias inválidos: {result.invalid_days}
Taxa de validação: {result.get_validation_rate():.2f}%
Status: {"APROVADO" if result.is_approved() else "REPROVADO"}

BATIDAS PROCESSADAS:
────────────────────
Batidas estimadas: {result.estimated_clocks}
Batidas não classificadas: {result.not_classified_clocks}

INCONSISTÊNCIAS ENCONTRADAS:
─────────────────────────────
"""
        
        if not result.inconsistencies:
            report += "Nenhuma inconsistência encontrada.\n"
        else:
            for inc in result.inconsistencies:
                report += f"""
Data: {inc['date']}
Tipo: {inc['type'].value}
Detalhes: {inc['details']}
"""
        
        report += "\n════════════════════════════════════════════════════════════\n"
        return report


class LogFormatter:
    """Formatador de logs do processamento"""
    
    @staticmethod
    def log_processing_start(employee_id: int, start_date: date, end_date: date) -> None:
        print(f"[INFO] Iniciando processamento do funcionário {employee_id} ({start_date} a {end_date})")
    
    @staticmethod
    def log_processing_end(employee_id: int) -> None:
        print(f"[INFO] Processamento do funcionário {employee_id} concluído")
    
    @staticmethod
    def log_missing_clock(employee_id: int, record_date: date, clock_type: str) -> None:
        print(f"[WARN] Funcionário {employee_id}: Batida de {clock_type} ausente em {record_date}")
    
    @staticmethod
    def log_estimated_clock(employee_id: int, record_date: date, confidence: float) -> None:
        print(f"[INFO] Funcionário {employee_id}: Batida estimada em {record_date} (confiança: {confidence:.2%})")
    
    @staticmethod
    def log_not_classified(employee_id: int, record_date: date, reason: str) -> None:
        print(f"[WARN] Funcionário {employee_id}: Batida não classificada em {record_date} ({reason})")
