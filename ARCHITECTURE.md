# Arquitetura do Sistema de Auditoria de Timesheets

## Visão Geral da Arquitetura

O projeto implementa arquitetura em camadas com separação clara de responsabilidades, seguindo princípios SOLID e padrões de design estabelecidos.

```
┌─────────────────────────────────────────────────────────────┐
│              CAMADA DE APRESENTAÇÃO (main.py)               │
│              ├─ Interface com usuário                       │
│              └─ Orquestração de workflows                   │
├─────────────────────────────────────────────────────────────┤
│              CAMADA DE APLICAÇÃO (services/)                │
│              ├─ TimesheetAuditProcessor (orquestrador)      │
│              ├─ Validators (lógica de validação)            │
│              └─ Calculadores (estimação)                    │
├─────────────────────────────────────────────────────────────┤
│              CAMADA DE DOMÍNIO (models/)                    │
│              ├─ Employee                                    │
│              ├─ TimeRecord                                  │
│              ├─ Shift                                       │
│              └─ AuditResult                                 │
├─────────────────────────────────────────────────────────────┤
│           CAMADA DE INFRAESTRUTURA                          │
│         ┌────────────┬──────────────┬────────────┐          │
│         ↓            ↓              ↓            ↓          │
│    Repositories  Strategies    Config         Utils         │
│    ├─ Memory      ├─ Weighted   ├─ Config      ├─ Reports   │
│    └─ (DB ready)  ├─ RuleBased  │              └─ Logs      │
│                   └─ Hybrid     │                           │
│                                 └─ ConfigManager            │
└─────────────────────────────────────────────────────────────┘
```

## Padrões de Design Utilizados

### 1. **Repository Pattern**
Abstração para acesso a dados com interface consistente.

```python
# Interface
class EmployeeRepository(ABC):
    @abstractmethod
    def get_active_employees(self) -> List[Employee]:
        pass

# Implementação em memória (atual)
class InMemoryEmployeeRepository(EmployeeRepository):
    def get_active_employees(self) -> List[Employee]:
        return [e for e in self.employees.values() if e.active]

# Pronto para implementação com banco de dados
class DatabaseEmployeeRepository(EmployeeRepository):
    def get_active_employees(self) -> List[Employee]:
        # SELECT * FROM employees WHERE active = true
        pass
```

**Benefícios:**
- Desacoplamento da lógica de negócio da persistência
- Facilita testes unitários
- Permite trocar source de dados sem alterar serviços

### 2. **Strategy Pattern**
Diferentes estratégias de estimação de batidas.

```python
class EstimationStrategy(ABC):
    @abstractmethod
    def estimate(self, references, shift, missing_clock_type):
        pass

class WeightedAverageStrategy(EstimationStrategy):
    # Implementação usando média ponderada
    
class RuleBasedStrategy(EstimationStrategy):
    # Implementação usando regras fixas
    
class HybridStrategy(EstimationStrategy):
    # Implementação combinada
```

**Benefícios:**
- Permite selecionar estratégia em tempo de execução
- Facilita adicionar novas estratégias
- Código mais testável e flexible

### 3. **Dependency Injection**
Injeção de dependências via construtor.

```python
class TimesheetAuditProcessor:
    def __init__(
        self,
        employee_repo: EmployeeRepository,      # Injetada
        time_record_repo: TimeRecordRepository,  # Injetada
        shift_repo: ShiftRepository              # Injetada
    ):
        self.employee_repo = employee_repo
        # ...
```

**Benefícios:**
- Facilita testes (pode usar mocks)
- Desacoplamento de componentes
- Configuração flexível

### 4. **Factory Pattern**
Criação de objetos complexos (estratégias, configurações).

```python
# ConfigManager como factory do padrão Singleton
class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### 5. **Service Locator Pattern**
Localização centralizada de configurações.

```python
# ConfigManager gerencia configurações globais
config = ConfigManager().get_config()
```

### 6. **Data Transfer Object (DTO)**
Modelos simples para transferência de dados.

```python
@dataclass
class Employee:
    id: int
    name: str
    cpf: str
    shift_id: int
    active: bool = True

@dataclass
class TimeRecord:
    id: int
    employee_id: int
    timestamp: datetime
    record_date: date
    classification: ClassificationEnum
```

## Princípios SOLID

### Single Responsibility (S)
Cada classe tem uma única responsabilidade:
- `TimeNormalizer`: Apenas normaliza e agrupa registros
- `MandatoryClockValidator`: Apenas valida batidas obrigatórias
- `ReferenceSearcher`: Apenas busca referências

### Open/Closed (O)
Classes abertas para extensão, fechadas para modificação:
- Pode-se criar novas estratégias sem alterar código existente
- Pode-se criar novos repositórios sem alterar serviços

### Liskov Substitution (L)
Subclasses podem substituir a classe base:
- Qualquer `EstimationStrategy` pode ser usada
- Qualquer `Repository` pode ser usado

### Interface Segregation (I)
Interfaces focadas e mínimas:
- `EmployeeRepository` tem apenas métodos de funcionários
- `TimeRecordRepository` tem apenas métodos de registros

### Dependency Inversion (D)
Depender de abstrações, não de implementações concretas:
- `TimesheetAuditProcessor` depende de interfaces (`EmployeeRepository`)
- Não depende de implementações concretas

## Estrutura de Dados

### Fluxo de Dados no Processamento

```
Entrada:
├─ Repositório de Funcionários
├─ Repositório de Registros de Ponto
└─ Repositório de Turnos
    ↓
Processamento (TimesheetAuditProcessor):
├─ Carregar dados
├─ Normalizar por dia
├─ Validar batidas obrigatórias
├─ Buscar referências
├─ Calcular estimativas
└─ Classificar batidas
    ↓
Saída:
├─ Registros atualizados (com classificações)
└─ Resultados de auditoria (estatísticas)
```

### Estado Mutável vs Imutável

**Mutável (modificado durante processamento):**
- `TimeRecord.classification` - é atualizada
- `TimeRecord.confidence_score` - é preenchida

**Imutável (nunca modificado):**
- `Employee` - apenas leitura
- `Shift` - apenas leitura

## Fluxo de Execução Detalhado

```
main() 
├─ Carregar dados (setup_test_data)
│  ├─ Criar repositórios em memória
│  ├─ Criar turnos
│  ├─ Criar funcionários
│  └─ Criar registros de ponto
│
├─ Configurar auditoria
│  └─ ConfigManager.set_config()
│
└─ Criar e executar processador
   └─ processor.process_period(start, end)
      ├─ Para cada funcionário ativo
      │  └─ _process_employee()
      │     ├─ Extrair registros do período
      │     ├─ Normalizar por dia
      │     ├─ Identificar turno
      │     │
      │     └─ Para cada dia do período
      │        ├─ Validar batidas obrigatórias
      │        │
      │        └─ Se hay batidas ausentes
      │           ├─ Buscar referências (4 fontes)
      │           ├─ Validar referências
      │           │
      │           ├─ Se válidas
      │           │  ├─ Calcular estimativa
      │           │  ├─ Verificar confiança
      │           │  │
      │           │  ├─ Se >= limite
      │           │  │  └─ Registrar como ESTIMADA
      │           │  │
      │           │  └─ Senão
      │           │     └─ Registrar como NÃO CLASSIFICADA
      │           │
      │           └─ Senão
      │              └─ Registrar como NÃO CLASSIFICADA
      │
      └─ Retornar resultados de auditoria

Gerar Relatório
└─ AuditReportGenerator.generate_summary(results)
```

## Extensibilidade

### Adicionar Nova Estratégia de Estimação

1. Criar classe que estenda `EstimationStrategy`
2. Implementar método `estimate()`
3. Usar no processador

```python
class MyNewStrategy(EstimationStrategy):
    def estimate(self, references, shift, missing_clock_type):
        # Sua implementação
        return estimated_time, confidence_score
```

### Usar Banco de Dados

1. Criar classe `DatabaseEmployeeRepository(EmployeeRepository)`
2. Implementar acesso ao banco
3. Passar ao processador

```python
db_repo = DatabaseEmployeeRepository(connection_string)
processor = TimesheetAuditProcessor(db_repo, ...)
```

### Adicionar Validação Customizada

1. Estender `MandatoryClockValidator`
2. Adicionar lógica de validação
3. Usar no processador

## Performance

### Otimizações Presentes

1. **Agrupamento em memória**: Registros já agrupados por dia
2. **Índices de busca**: Repositórios mantêm índices
3. **Cálculos em batch**: Processa período inteiro de uma vez

### Possíveis Melhorias

1. Implementar paginação para períodos longos
2. Cache de dados frequentemente acessados
3. Processamento paralelo por funcionário
4. Índices em banco de dados

## Testes

### Estratégia de Testes

- **Unitários**: Para cada serviço/modelo isolado
- **Integração**: Para fluxo completo (em examples.py)
- **Dados**: Usando repositórios em memória

### Cobertura

Principais cenários cobertos:
- Validação de batidas completas ✓
- Batidas ausentes e estimação ✓
- Múltiplos funcionários ✓
- Erros de configuração ✓
- Cálculos de taxa de validação ✓

## Próximas Melhorias

1. **Persistência Real**: Implementar com SQLAlchemy
2. **API REST**: Expor funcionalidades via FastAPI
3. **Autenticação**: Adicionar autenticação de usuários
4. **Logging**: Usar logging estruturado (structlog)
5. **Documentação**: Gerar docs com Sphinx
6. **Performance**: Adicionar paginação e cache
7. **Monitoramento**: Integrar com APM tools
8. **CI/CD**: Setup com GitHub Actions
