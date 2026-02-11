# Estrutura do Projeto - Sistema de Auditoria de Timesheets

## Árvore de Diretórios

```
audit-timesheets/
├── src/                                  # Código-fonte principal
│   ├── __init__.py
│   ├── models/                           # Modelos de dados
│   │   ├── __init__.py
│   │   ├── employee.py                   # Modelo de funcionário
│   │   ├── time_record.py                # Modelo de registro de ponto
│   │   ├── shift.py                      # Modelo de turno
│   │   └── audit_result.py               # Modelo de resultado de auditoria
│   │
│   ├── repositories/                     # Camada de acesso a dados
│   │   ├── __init__.py                   # Interfaces de repositórios
│   │   └── memory.py                     # Implementação em memória
│   │                                     # (Pronto para adicionar: database.py)
│   │
│   ├── services/                         # Lógica de negócio
│   │   ├── __init__.py                   # Exportações públicas
│   │   ├── validators.py                 # Serviços de validação
│   │   │   ├── TimeNormalizer
│   │   │   ├── ShiftIdentifier
│   │   │   ├── MandatoryClockValidator
│   │   │   ├── ReferenceSearcher
│   │   │   ├── ReferenceValidator
│   │   │   └── EstimationCalculator
│   │   └── processor.py                 # Orquestrador principal
│   │       └── TimesheetAuditProcessor
│   │
│   ├── strategies/                      # Estratégias de estimação
│   │   └── __init__.py
│   │       ├── ReferenceData            # DTO para dados de referência
│   │       ├── EstimationStrategy       # Interface abstrata
│   │       ├── WeightedAverageStrategy  # Estratégia de média ponderada
│   │       ├── RuleBasedStrategy        # Estratégia baseada em regras
│   │       └── HybridStrategy           # Estratégia híbrida
│   │
│   ├── utils/                           # Utilitários
│   │   ├── __init__.py
│   │   ├── AuditReportGenerator         # Geração de relatórios
│   │   └── LogFormatter                 # Formatação de logs
│   │
│   └── config/                          # Configurações
│       └── __init__.py
│           ├── AuditConfig              # Configuração de auditoria
│           └── ConfigManager            # Gerenciador de configurações (Singleton)
│
├── main.py                              # Ponto de entrada com exemplo completo
├── examples.py                          # Exemplos avançados de uso
├── tests.py                             # Testes unitários (25 testes)
├── requirements.txt                     # Dependências do projeto
├── README.md                            # Documentação principal do projeto
├── ARCHITECTURE.md                      # Documentação de arquitetura
├── PROJECT_STRUCTURE.md                 # Este arquivo
└── .gitignore                           # Arquivo de exclusão Git
```

## Arquivos Principais e Responsabilidades

### Código Fonte (src/)

#### Models (src/models/)
- **employee.py**: Define `Employee` - funcionário com ID, nome, CPF, turno e status ativo
- **time_record.py**: Define `TimeRecord` e `ClassificationEnum` - registro de ponto com classificação
- **shift.py**: Define `Shift` e `ShiftTolerance` - turno com horários e tolerâncias
- **audit_result.py**: Define `AuditResult` e `InconsistencyType` - resultado da auditoria

#### Repositories (src/repositories/)
- **__init__.py**: Interfaces abstratas (`EmployeeRepository`, `TimeRecordRepository`, `ShiftRepository`)
- **memory.py**: Implementações em memória dos repositórios
  - `InMemoryEmployeeRepository`
  - `InMemoryTimeRecordRepository`
  - `InMemoryShiftRepository`

#### Services (src/services/)
- **validators.py**: Serviços de validação e normalização
  - `TimeNormalizer`: Normaliza e agrupa registros por dia
  - `ShiftIdentifier`: Identifica turno do funcionário
  - `MandatoryClockValidator`: Valida batidas obrigatórias
  - `ReferenceSearcher`: Busca referências para estimação
  - `ReferenceValidator`: Valida qualidade das referências
  - `EstimationCalculator`: Calcula estimativas

- **processor.py**: Orquestrador principal
  - `TimesheetAuditProcessor`: Coordena todo o fluxo de auditoria
    - `process_period()`: Processa todos os funcionários
    - `_process_employee()`: Processa funcionário individual
    - `_process_missing_clock()`: Trata batidas ausentes

#### Strategies (src/strategies/)
- **__init__.py**: Estratégias de estimação de batidas
  - `ReferenceData`: DTO para dados de referência
  - `EstimationStrategy`: Interface abstrata
  - `WeightedAverageStrategy`: Média ponderada (4 pesos diferentes)
  - `RuleBasedStrategy`: Horários fixos do turno
  - `HybridStrategy`: Combinação das anteriores

#### Utils (src/utils/)
- **__init__.py**: Utilitários gerais
  - `AuditReportGenerator`: Gera relatórios resumidos e detalhados
  - `LogFormatter`: Formata mensagens de log

#### Config (src/config/)
- **__init__.py**: Configurações e gerenciamento
  - `AuditConfig`: Dataclass com configurações de auditoria
  - `ConfigManager`: Singleton para gerenciar configurações globais

### Arquivos de Execução

- **main.py**: Demonstração completa do sistema
  - Setup de dados de teste
  - Execução do fluxo completo
  - Geração de relatórios

- **examples.py**: Exemplos avançados
  - Estratégias customizadas
  - Múltiplos funcionários e turnos
  - Tratamento de erros
  - Análise de batidas ausentes

- **tests.py**: Suite de testes unitários
  - 25 testes cobrindo modelos, repositories, services e strategies
  - Testes de validação de configuração
  - Testes de normalização e estimação

### Documentação

- **README.md**: Documentação completa
  - Visão geral do projeto
  - Guia de instalação
  - Exemplos de uso
  - Documentação das APIs

- **ARCHITECTURE.md**: Documentação técnica
  - Padrões de design utilizados (Repository, Strategy, DI, etc.)
  - Princípios SOLID implementados
  - Fluxo de dados e execução
  - Guias de extensibilidade
  - Análise de performance

- **PROJECT_STRUCTURE.md**: Este arquivo
  - Descrição da estrutura do projeto
  - Responsabilidades de cada arquivo
  - Guia rápido de navegação

### Configuração

- **requirements.txt**: Dependências (atualmente apenas python-dateutil)
- **.gitignore**: Padrões de arquivos ignorados pelo Git

## Fluxo de Dados

```
Entrada:
├─ Funcionários (Employee)
├─ Registros de Ponto (TimeRecord)
└─ Turnos (Shift)
     ↓
[TimesheetAuditProcessor]
     ├─ Carrega dados via repositories
     ├─ Normaliza registros por dia
     ├─ Valida batidas obrigatórias
     ├─ Busca referências para batidas ausentes
     ├─ Calcula estimativas com estratégias
     └─ Classifica batidas (NORMAL/ESTIMADA/NÃO CLASSIFICADA)
     ↓
Saída:
├─ TimeRecords atualizados (com classificações)
└─ AuditResults (estatísticas e inconsistências)
```

## Principais Classes e Interfaces

### No Padrão Repository

```
EmployeeRepository (interface)
└── InMemoryEmployeeRepository (implementação atual)

TimeRecordRepository (interface)
└── InMemoryTimeRecordRepository (implementação atual)

ShiftRepository (interface)
└── InMemoryShiftRepository (implementação atual)
```

### No Padrão Strategy

```
EstimationStrategy (interface)
├── WeightedAverageStrategy
├── RuleBasedStrategy
└── HybridStrategy
```

### Serviços de Validação

Cada serviço tem responsabilidade única:
- `TimeNormalizer`: Apenas normaliza
- `ShiftIdentifier`: Apenas identifica turno
- `MandatoryClockValidator`: Apenas valida
- `ReferenceSearcher`: Apenas busca
- `ReferenceValidator`: Apenas valida referências
- `EstimationCalculator`: Apenas calcula

### Modelos de Dados

```
Employee → TimeRecord
   ↓           ↓
  Shift   ClassificationEnum
   
AuditResult → InconsistencyType
```

## Como Navegar o Projeto

### Para Entender o Fluxo Completo
1. Leia `main.py` - começa aqui
2. Entenda `TimesheetAuditProcessor` em `src/services/processor.py`
3. Veja os serviços individuais em `src/services/validators.py`

### Para Entender a Arquitetura
1. Leia `ARCHITECTURE.md`
2. Examine `src/repositories/__init__.py` para ver padrão Repository
3. Examine `src/strategies/__init__.py` para ver padrão Strategy

### Para Adicionar Nova Funcionalidade
1. Crie nova classe herdando de interface abstrata
2. Injete via construtor no serviço que a usa
3. Adicione testes em `tests.py`
4. Atualize documentação relevante

### Para Testar
1. Execute `python3 tests.py` para testes unitários
2. Execute `python3 main.py` para teste integrado
3. Execute `python3 examples.py` para exemplos avançados

## Distribuição de Responsabilidades

### Modelos (models/)
- Apenas estrutura de dados
- Sem lógica de negócio
- Métodos auxiliares (helpers)

### Repositories (repositories/)
- Abstração de acesso a dados
- Atual: em memória
- Pronto para: banco de dados

### Services (services/)
- Toda a lógica de negócio
- Orquestração de fluxos
- Composição de funcionalidades

### Strategies (strategies/)
- Algoritmos de negócio
- Facilmente substituíveis
- Independentes e testáveis

### Utils (utils/)
- Formatação e geração de output
- Logging e relatórios
- Utilitários gerais

### Config (config/)
- Gerenciamento de configuração
- Padrão Singleton
- Validação de config

## Pontos de Extensão

1. **Novos repositórios**: Implemente `*Repository` interface
2. **Novas estratégias**: Estenda `EstimationStrategy`
3. **Novos serviços**: Crie em `services/` e injete
4. **Novos modelos**: Adicione em `models/`
5. **Novos relatórios**: Estenda `AuditReportGenerator`

## Convenções do Projeto

- **Nomes de classes**: PascalCase
- **Nomes de arquivos**: snake_case
- **Métodos privados**: prefixo `_`
- **Interfaces**: classe abstrata com sufixo (ex: `*Repository`)
- **Implementações**: classe concreta com nome descritivo
- **Testes**: prefixo `test_` em métodos
- **Docstrings**: Presentes em classes e métodos públicos

## Performance e Escalabilidade

Otimizações atuais:
- Agrupamento em memória
- Índices simples nos repositórios
- Processamento em batch

Possíveis melhorias:
- Cache de dados
- Paginação para períodos longos
- Processamento paralelo por funcionário
- Índices em banco de dados
- Compressão de dados históricos

---

Este projeto demonstra princípios sólidos de engenharia de software e está pronto para evolução e manutenção.
