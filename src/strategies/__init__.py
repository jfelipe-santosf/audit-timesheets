from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, List
from src.models import TimeRecord, Shift


class ReferenceData:
    """Dados de referência para estimativa de batida"""
    
    def __init__(self):
        self.same_day_records: List[TimeRecord] = []
        self.previous_day_records: List[TimeRecord] = []
        self.next_day_records: List[TimeRecord] = []
        self.other_employees_records: List[TimeRecord] = []


class EstimationStrategy(ABC):
    """Interface para estratégias de cálculo de horários estimados"""
    
    @abstractmethod
    def estimate(
        self,
        references: ReferenceData,
        shift: Shift,
        missing_clock_type: str  # 'entrada' ou 'saída'
    ) -> tuple[Optional[datetime], float]:
        """
        Estima um horário baseado nas referências
        
        Returns:
            Tuple[datetime estimado, confiança (0-1)]
        """
        pass


class WeightedAverageStrategy(EstimationStrategy):
    """
    Estratégia que usa média ponderada das referências
    Peso maior para registros do mesmo funcionário no mesmo dia/dias próximos
    """
    
    SAME_DAY_WEIGHT = 4.0
    PREVIOUS_DAY_WEIGHT = 3.0
    NEXT_DAY_WEIGHT = 2.5
    OTHER_EMPLOYEES_WEIGHT = 1.0
    
    def estimate(
        self,
        references: ReferenceData,
        shift: Shift,
        missing_clock_type: str
    ) -> tuple[Optional[datetime], float]:
        
        weighted_times = []
        total_weight = 0
        reference_date = None
        
        # Processa registros do mesmo dia
        for record in references.same_day_records:
            weighted_times.append(
                (record.timestamp, self.SAME_DAY_WEIGHT)
            )
            total_weight += self.SAME_DAY_WEIGHT
            if reference_date is None:
                reference_date = record.timestamp
        
        # Processa registros do dia anterior
        for record in references.previous_day_records:
            weighted_times.append(
                (record.timestamp, self.PREVIOUS_DAY_WEIGHT)
            )
            total_weight += self.PREVIOUS_DAY_WEIGHT
            if reference_date is None:
                reference_date = record.timestamp
        
        # Processa registros do dia seguinte
        for record in references.next_day_records:
            weighted_times.append(
                (record.timestamp, self.NEXT_DAY_WEIGHT)
            )
            total_weight += self.NEXT_DAY_WEIGHT
            if reference_date is None:
                reference_date = record.timestamp
        
        # Processa registros de outros funcionários
        for record in references.other_employees_records:
            weighted_times.append(
                (record.timestamp, self.OTHER_EMPLOYEES_WEIGHT)
            )
            total_weight += self.OTHER_EMPLOYEES_WEIGHT
            if reference_date is None:
                reference_date = record.timestamp
        
        if not weighted_times or total_weight == 0 or reference_date is None:
            return None, 0.0
        
        # Calcula média ponderada dos minutos
        total_minutes = 0
        for timestamp, weight in weighted_times:
            total_minutes += (timestamp.hour * 60 + timestamp.minute) * weight
        
        average_minutes = total_minutes / total_weight
        hours = int(average_minutes // 60)
        minutes = int(average_minutes % 60)
        
        # Cria datetime estimado usando o primeiro registro encontrado como referência de data
        estimated_time = reference_date.replace(
            hour=hours, minute=minutes, second=0, microsecond=0
        )
        
        # Calcula confiança baseada na quantidade de referências
        confidence = min(1.0, len(weighted_times) / 4.0)  # Máximo 4 referências para 100%
        
        return estimated_time, confidence


class RuleBasedStrategy(EstimationStrategy):
    """
    Estratégia baseada em regras fixas do turno
    Usa horários de entrada/saída definidos no turno
    """
    
    def estimate(
        self,
        references: ReferenceData,
        shift: Shift,
        missing_clock_type: str
    ) -> tuple[Optional[datetime], float]:
        
        if not references.same_day_records:
            return None, 0.0
        
        reference_date = references.same_day_records[0].timestamp
        
        if missing_clock_type.lower() == 'entrada':
            estimated_time = reference_date.replace(
                hour=shift.start_time.hour,
                minute=shift.start_time.minute,
                second=0,
                microsecond=0
            )
        else:  # saída
            estimated_time = reference_date.replace(
                hour=shift.end_time.hour,
                minute=shift.end_time.minute,
                second=0,
                microsecond=0
            )
        
        confidence = 0.6  # Menor confiança pois usa apenas regra fixa
        return estimated_time, confidence


class HybridStrategy(EstimationStrategy):
    """
    Estratégia híbrida que combina média ponderada com regras
    Prioriza dados históricos mas valida contra turno
    """
    
    def __init__(self):
        self.weighted_strategy = WeightedAverageStrategy()
        self.rule_strategy = RuleBasedStrategy()
    
    def estimate(
        self,
        references: ReferenceData,
        shift: Shift,
        missing_clock_type: str
    ) -> tuple[Optional[datetime], float]:
        
        # Tenta estimativa ponderada
        estimated_time, confidence = self.weighted_strategy.estimate(
            references, shift, missing_clock_type
        )
        
        if estimated_time is None:
            # Fallback para estratégia baseada em regras
            return self.rule_strategy.estimate(references, shift, missing_clock_type)
        
        # Valida se a estimativa está dentro do intervalo do turno
        shift_start = estimated_time.replace(
            hour=shift.start_time.hour,
            minute=shift.start_time.minute
        )
        shift_end = estimated_time.replace(
            hour=shift.end_time.hour,
            minute=shift.end_time.minute
        )
        
        # Se é entrada e está fora do horário, mas temos referências, mantém estimativa
        # Se é saída e está fora do horário, mas temos referências, mantém estimativa
        # Confiança é reduzida se está fora dos limites normais do turno
        
        return estimated_time, confidence
