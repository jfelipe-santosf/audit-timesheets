from dataclasses import dataclass
from datetime import date


@dataclass
class AuditConfig:
    """Configuração da auditoria"""
    
    # Períodos
    start_date: date
    end_date: date
    
    # Validações
    minimum_confidence_threshold: float = 0.5
    minimum_validation_rate: float = 95.0  # em percentual
    
    # Estratégias
    estimation_strategy: str = "hybrid"  # weighted_average, rule_based, hybrid
    
    # Tolerâncias
    allow_negative_intervals: bool = False
    check_shift_boundaries: bool = True
    
    def is_valid(self) -> bool:
        """Valida configurações"""
        if self.start_date >= self.end_date:
            return False
        if not (0.0 <= self.minimum_confidence_threshold <= 1.0):
            return False
        if not (0.0 <= self.minimum_validation_rate <= 100.0):
            return False
        return True


class ConfigManager:
    """Gerenciador de configurações"""
    
    _instance: 'ConfigManager' = None
    _config: AuditConfig = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def set_config(self, config: AuditConfig) -> None:
        """Define configuração"""
        if not config.is_valid():
            raise ValueError("Configuração inválida")
        self._config = config
    
    def get_config(self) -> AuditConfig:
        """Obtém configuração atual"""
        if self._config is None:
            raise RuntimeError("Configuração não foi definida")
        return self._config
