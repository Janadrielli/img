# Epic Design - Arquitetura Macro

> **Spec vinculada:** [epic-requirements.md](./epic-requirements.md)
> **Status:** {{STATUS}} | **Arquiteto:** {{ARQUITETO}}

---

## 1. Arquitetura de Alto Nível

> Visão macro do sistema completo mostrando todos os sub-módulos e suas interações.

```
┌────────────────────────────────────────────────────────────────┐
│                      {{NOME_SISTEMA}}                           │
├──────────────────┬──────────────────┬──────────────────────────┤
│  Sub-Func 1      │  Sub-Func 2      │  Sub-Func N              │
│  {{DESC_S1}}     │  {{DESC_S2}}     │  {{DESC_SN}}             │
├──────────────────┴──────────────────┴──────────────────────────┤
│                  Camada Compartilhada                           │
│  [Auth] [Logging] [Mensageria] [Cache] [Config]               │
├────────────────────────────────────────────────────────────────┤
│                  Infraestrutura                                 │
│  [{{BANCO}}] [{{FILA}}] [{{CACHE}}] [{{STORAGE}}]             │
└────────────────────────────────────────────────────────────────┘
```

---

## 2. Decisões Arquiteturais (ADRs)

### ADR-001: {{TITULO_ADR_1}}

| Aspecto       | Detalhe                                                      |
|---------------|--------------------------------------------------------------|
| **Contexto**  | {{CONTEXTO_ADR_1}}                                           |
| **Decisão**   | {{DECISAO_ADR_1}}                                            |
| **Razão**     | {{RAZAO_ADR_1}}                                              |
| **Trade-offs**| {{TRADEOFFS_ADR_1}}                                          |
| **Status**    | Aceito                                                       |

### ADR-002: {{TITULO_ADR_2}}

| Aspecto       | Detalhe                                                      |
|---------------|--------------------------------------------------------------|
| **Contexto**  | {{CONTEXTO_ADR_2}}                                           |
| **Decisão**   | {{DECISAO_ADR_2}}                                            |
| **Razão**     | {{RAZAO_ADR_2}}                                              |
| **Trade-offs**| {{TRADEOFFS_ADR_2}}                                          |
| **Status**    | Aceito                                                       |

---

## 3. Banco de Dados Compartilhado

### 3.1 Estratégia de Schema

| Opção escolhida       | Justificativa                                                |
|-----------------------|--------------------------------------------------------------|
| {{ESTRATEGIA_DB}}     | {{JUSTIFICATIVA_DB}}                                         |

### 3.2 Modelo ER (Entidades Globais)

```
{{ENTIDADE_GLOBAL_1}} {
  id: UUID [PK]
  {{CAMPO_G1}}: {{TIPO_G1}}
  {{CAMPO_G2}}: {{TIPO_G2}}
  created_at: timestamp
  updated_at: timestamp
}

{{ENTIDADE_GLOBAL_2}} {
  id: UUID [PK]
  {{FK_CAMPO}}: UUID [FK -> {{ENTIDADE_GLOBAL_1}}.id]
  {{CAMPO_G3}}: {{TIPO_G3}}
}
```

### 3.3 Estratégia de Migração

| Fase         | Migração                         | Rollback                        |
|--------------|----------------------------------|---------------------------------|
| {{FASE_1}}   | {{MIGRACAO_1}}                   | {{ROLLBACK_1}}                  |

---

## 4. Comunicação entre Sub-Módulos

### 4.1 Síncrona (Request/Response)

| Origem       | Destino      | Protocolo  | Contrato                        |
|--------------|--------------|------------|---------------------------------|
| {{S1}}       | {{S2}}       | REST/gRPC  | {{CONTRATO_REF_1}}              |

### 4.2 Assíncrona (Eventos/Mensagens)

| Produtor     | Tópico/Fila  | Consumidor | Schema do Evento                |
|--------------|--------------|------------|---------------------------------|
| {{S1}}       | {{TOPICO_1}} | {{S2}}     | {{SCHEMA_EVENTO_1}}             |

### 4.3 Padrões de Resiliência

| Padrão              | Aplicação                        | Configuração                    |
|---------------------|----------------------------------|---------------------------------|
| Circuit Breaker     | {{ONDE_CB}}                      | {{CONFIG_CB}}                   |
| Retry               | {{ONDE_RETRY}}                   | {{CONFIG_RETRY}}                |
| Timeout             | {{ONDE_TIMEOUT}}                 | {{CONFIG_TIMEOUT}}              |
| Bulkhead            | {{ONDE_BULKHEAD}}                | {{CONFIG_BULKHEAD}}             |

---

## 5. Infraestrutura

### 5.1 Ambientes

| Ambiente     | Propósito                        | Escala                          |
|--------------|----------------------------------|---------------------------------|
| dev          | Desenvolvimento local            | Mínimo                          |
| staging      | Testes de integração             | ~10% de prod                    |
| production   | Atendimento real                 | {{ESCALA_PROD}}                 |

### 5.2 Stack de Infraestrutura

| Componente           | Tecnologia           | Justificativa                   |
|----------------------|----------------------|---------------------------------|
| Orquestração         | {{ORCH_TECH}}        | {{ORCH_JUST}}                   |
| Banco de dados       | {{DB_TECH}}          | {{DB_JUST}}                     |
| Cache                | {{CACHE_TECH}}       | {{CACHE_JUST}}                  |
| Mensageria           | {{MSG_TECH}}         | {{MSG_JUST}}                    |
| Object Storage       | {{STORAGE_TECH}}     | {{STORAGE_JUST}}                |

---

## 6. Segurança (Arquitetural)

### 6.1 Boundaries e Trust Zones

```
[Internet] ──── [WAF/CDN] ──── [API Gateway] ──── [Services] ──── [Data Layer]
  Untrusted       DMZ            Semi-trusted       Trusted          Restricted
```

### 6.2 Autenticação e Autorização

| Camada               | Mecanismo            | Token                           |
|----------------------|----------------------|---------------------------------|
| Externa (Usuário)    | {{AUTH_EXT}}         | {{TOKEN_EXT}}                   |
| Interna (Serviço)    | {{AUTH_INT}}         | {{TOKEN_INT}}                   |

---

## 7. Observabilidade (Global)

### 7.1 Padrão de Correlação

- Correlation ID: propagado via header `X-Correlation-ID`
- Formato: UUID v4
- Gerado no: API Gateway / primeiro ponto de entrada

### 7.2 Stack de Observabilidade

| Pilar        | Ferramenta           | Retenção                        |
|--------------|----------------------|---------------------------------|
| Logs         | {{LOG_STACK}}        | {{LOG_RETENCAO}}                |
| Métricas     | {{METRIC_STACK}}     | {{METRIC_RETENCAO}}             |
| Traces       | {{TRACE_STACK}}      | {{TRACE_RETENCAO}}              |
| Dashboards   | {{DASH_STACK}}       | N/A                             |

---

## 8. Estratégia de Deployment

| Aspecto              | Abordagem                        | Detalhes                        |
|----------------------|----------------------------------|---------------------------------|
| Deploy strategy      | {{DEPLOY_STRATEGY}}              | {{DEPLOY_DETALHE}}              |
| Rollback             | {{ROLLBACK_STRATEGY}}            | {{ROLLBACK_DETALHE}}            |
| Feature flags        | {{FF_TOOL}}                      | {{FF_DETALHE}}                  |

---

## 9. Mapa de Dependência entre Sub-Funcionalidades

```
Sub-Func-1 (Fundação)
    │
    ├──▶ Sub-Func-2 (depende de S1)
    │       │
    │       └──▶ Sub-Func-4 (depende de S2 + S3)
    │
    └──▶ Sub-Func-3 (depende de S1)
            │
            └──▶ Sub-Func-4 (depende de S2 + S3)
```

---

*Criado em: {{DATA_CRIACAO}}*
*Última revisão: {{DATA_REVISAO}}*
