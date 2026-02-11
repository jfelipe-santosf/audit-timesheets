# Sistema de Auditoria de Registros de Ponto

## Visão Geral

Sistema completo para auditoria de registros de ponto (timesheets) que implementa um fluxograma sofisticado de processamento de dados. O sistema valida batidas obrigatórias dos funcionários, identifica inconsistências e estima batidas ausentes usando múltiplas estratégias de cálculo e análise de referências.

## Arquitetura

O projeto segue uma arquitetura em camadas bem definida:

```
audit-timesheets/
├── src/
│   ├── models/             # Modelos de dados (entidades)
│   ├── repositories/       # Camada de acesso a dados
│   ├── services/           # Lógica de negócio
│   ├── strategies/         # Estratégias de estimação
│   ├── utils/              # Utilitários (relatórios, logs)
│   └── config/             # Configurações
├── main.py                 # Ponto de entrada
└── requirements.txt        # Dependências
```

## Modelos de Dados

### Employee
Representa um funcionário com informações de identificação e turno.

```python
Employee(
    id: int,
    name: str,
    cpf: str,
    shift_id: int,
    active: bool = True
)
```

### TimeRecord
Representa um registro de ponto (batida) de um funcionário.

```python
TimeRecord(
    id: int,
    employee_id: int,
    timestamp: datetime,
    record_date: date,
    shift_id: int,
    classification: ClassificationEnum,  # NORMAL, ESTIMATED, NOT_CLASSIFIED
    confidence_score: float,              # 0.0 a 1.0
    reference_sources: list[str]
)
```

### Shift
Define regras de turno e horários.

```python
Shift(
    id: int,
    name: str,
    start_time: time,
    end_time: time,
    mandatory_clocks: int = 2,
    tolerance: ShiftTolerance
)
```

### AuditResult
Resultado da auditoria de um funcionário no período.

```python
AuditResult(
    employee_id: int,
    period_start: date,
    period_end: date,
    valid_days: int,
    invalid_days: int,
    estimated_clocks: int,
    not_classified_clocks: int,
    inconsistencies: list[dict]
)
```

## Fluxograma de Processamento

O sistema implementa o seguinte fluxograma:

```
A → Iniciar processamento
B → Definir período de apuração
C → Carregar funcionários ativos
D → Carregar registros de ponto
E → Carregar regras de turno

F → Para cada funcionário:
  G → Selecionar funcionário
  H → Extrair registros do período
  I → Normalizar horários e agrupar por dia
  J → Identificar tipo de turno
  K → Definir batidas obrigatórias
  
  L → Para cada dia do período:
    M → Validar batidas obrigatórias
    N → Se válido: marcar como válido
       Senão: registrar inconsistência
    
    Q → Se há batidas ausentes:
      R → Selecionar batida ausente
      S → Buscar referências (4 fontes)
      T → Validar referências
      
      U → Se referências válidas:
        W → Calcular horário estimado
        X → Aplicar estratégia de cálculo
        Y → Se confiança >= limite:
          AA → Classificar como ESTIMADA
          AB → Persistir batida estimada
        Senão:
          V → Classificar como NÃO CLASSIFICADA
      Senão:
        V → Classificar como NÃO CLASSIFICADA

Z → Fim do processo
```

## Serviços Principais

### TimesheetAuditProcessor
Orquestrador principal que coordena todo o fluxo de auditoria.

**Métodos:**
- `process_period(start_date, end_date)`: Processa todos os funcionários
- `_process_employee()`: Processa um funcionário específico
- `_process_missing_clock()`: Trata batidas ausentes

### Validators
Serviços de validação:

- **TimeNormalizer**: Agrupa registros por dia em ordem cronológica
- **ShiftIdentifier**: Identifica o turno do funcionário
- **MandatoryClockValidator**: Valida batidas obrigatórias
- **ReferenceSearcher**: Busca referências em 4 fontes
- **ReferenceValidator**: Verifica se há referências válidas
- **EstimationCalculator**: Calcula horários estimados

## Estratégias de Estimação

O sistema suporta diferentes estratégias para estimar batidas ausentes:

### 1. WeightedAverageStrategy
Usa média ponderada de referências com pesos maiores para registros recentes:
- Mesmo dia: 4.0
- Dia anterior: 3.0
- Dia posterior: 2.5
- Outros funcionários: 1.0

### 2. RuleBasedStrategy
Usa horários fixos do turno (entrada no `start_time`, saída no `end_time`)

### 3. HybridStrategy
Combina ambas as estratégias: tenta média ponderada primeiro, fallback para regras

## Referências para Estimação

Quando uma batida está ausente, o sistema busca referências em 4 fontes:

1. **Mesmo funcionário, mesmo dia**: Registros do próprio funcionário no mesmo dia
2. **Mesmo funcionário, dia anterior**: Padrão de horário do dia anterior
3. **Mesmo funcionário, dia posterior**: Padrão de horário do dia seguinte
4. **Outros funcionários, mesmo turno**: Comparação com colegas no mesmo turno

## Instalação

```bash
# Clonar ou fazer download do projeto
cd audit-timesheets

# Instalar dependências
pip install -r requirements.txt
```

## Uso

### Execução Básica

```bash
python main.py
```

### Exemplo de Uso Programático

```python
from src.models import Employee, Shift
from src.repositories.memory import InMemoryEmployeeRepository, InMemoryTimeRecordRepository, InMemoryShiftRepository
from src.services import TimesheetAuditProcessor
from datetime import date

# Criar repositórios
employee_repo = InMemoryEmployeeRepository()
time_record_repo = InMemoryTimeRecordRepository()
shift_repo = InMemoryShiftRepository()

# Preencher dados...

# Criar processador
processor = TimesheetAuditProcessor(
    employee_repo,
    time_record_repo,
    shift_repo
)

# Processar período
results = processor.process_period(
    start_date=date(2026, 1, 1),
    end_date=date(2026, 1, 31)
)

# Gerar relatórios
from src.utils import AuditReportGenerator
report = AuditReportGenerator.generate_summary(results)
print(report)
```

## Configuração

Use a classe `AuditConfig` para customizar o comportamento:

```python
from src.config import AuditConfig, ConfigManager
from datetime import date

config = AuditConfig(
    start_date=date(2026, 1, 1),
    end_date=date(2026, 1, 31),
    minimum_confidence_threshold=0.5,      # Mínimo 50% de confiança
    minimum_validation_rate=95.0,          # Mínimo 95% dias válidos
    estimation_strategy="hybrid",          # Estratégia de estimação
    allow_negative_intervals=False,        # Não permite intervalo negativo
    check_shift_boundaries=True            # Valida limites do turno
)

ConfigManager().set_config(config)
```

## Extensibilidade

### Adicionar Nova Estratégia de Estimação

```python
from src.strategies import EstimationStrategy, ReferenceData

class MyCustomStrategy(EstimationStrategy):
    def estimate(
        self,
        references: ReferenceData,
        shift: Shift,
        missing_clock_type: str
    ) -> tuple[Optional[datetime], float]:
        # Sua lógica aqui
        return estimated_time, confidence_score
```

### Usar Repositório Customizado

```python
from src.repositories import EmployeeRepository

class MyDatabaseRepository(EmployeeRepository):
    def get_active_employees(self):
        # Buscar do banco de dados
        pass
    
    # Implementar outros métodos...
```

## Relatórios

O sistema gera dois tipos de relatório:

### Relatório Resumido
Visão geral de todos os funcionários processados

### Relatório Detalhado
Análise completa por funcionário incluindo:
- Taxa de validação
- Inconsistências encontradas
- Batidas estimadas
- Batidas não classificadas

## Classificações de Batidas

- **NORMAL**: Batida registrada normalmente
- **BATIDA ESTIMADA**: Estimada baseado em referências com confiança suficiente
- **NÃO CLASSIFICADA**: Não pode ser estimada por falta de referências
- **AUSENTE**: Batida completamente ausente

## Estrutura de Dados - Inconsistências

Cada resultado de auditoria pode conter inconsistências:

```python
{
    'date': date,
    'type': InconsistencyType,  # INCOMPLETE_CLOCKS, MISSING_CLOCKS, etc
    'details': str              # Descrição da inconsistência
}
```

## Licença

MIT

## Autor

Desenvolvido para demonstar sistema de auditoria de timesheets em Python.

---

**Nota**: Este é um sistema educacional/exemplo. Para uso em produção, considere:
- Implementar persistência em banco de dados real
- Adicionar autenticação e autorização
- Implementar testes unitários e de integração
- Adicionar tratamento mais robusto de erros
- Implementar cache de dados
- Adicionar logging estruturado
