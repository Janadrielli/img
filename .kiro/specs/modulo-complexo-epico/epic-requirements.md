# Epic Requirements - Módulo Complexo

> **Estimativa total:** > 80h (Épico) | **Status:** {{STATUS}}
> **Responsável:** {{RESPONSAVEL}} | **Quarter:** {{QUARTER}}

---

## 1. Visão do Épico

> Descrição de alto nível do módulo/sistema completo que será construído.

{{VISAO_EPICO}}

---

## 2. Objetivos Estratégicos

| #  | Objetivo                         | KPI / OKR                       | Meta                            |
|----|----------------------------------|---------------------------------|---------------------------------|
| E1 | {{OBJETIVO_ESTRATEGICO_1}}       | {{KPI_1}}                       | {{META_1}}                      |
| E2 | {{OBJETIVO_ESTRATEGICO_2}}       | {{KPI_2}}                       | {{META_2}}                      |

---

## 3. Escopo Global do Épico

### 3.1 Sub-funcionalidades

| #  | Sub-funcionalidade               | Prioridade | Estimativa | Dependência          |
|----|----------------------------------|------------|------------|----------------------|
| S1 | {{SUB_FUNC_1}}                   | P0         | {{H}}h     | —                    |
| S2 | {{SUB_FUNC_2}}                   | P1         | {{H}}h     | S1                   |
| S3 | {{SUB_FUNC_3}}                   | P1         | {{H}}h     | S1                   |
| S4 | {{SUB_FUNC_4}}                   | P2         | {{H}}h     | S2, S3               |

### 3.2 Fora de Escopo (Global)

- {{FORA_ESCOPO_GLOBAL_1}}
- {{FORA_ESCOPO_GLOBAL_2}}

---

## 4. Requisitos Globais (Cross-Cutting)

> Requisitos que se aplicam a TODAS as sub-funcionalidades.

### 4.1 Compliance e Regulamentação

| ID      | Regulamento           | Requisito                        | Evidência Necessária            |
|---------|-----------------------|----------------------------------|---------------------------------|
| COMP-01 | {{REGULAMENTO_1}}     | {{REQ_COMPLIANCE_1}}             | {{EVIDENCIA_1}}                 |
| COMP-02 | {{REGULAMENTO_2}}     | {{REQ_COMPLIANCE_2}}             | {{EVIDENCIA_2}}                 |

### 4.2 Segurança Global

| ID      | Requisito             | Standard                         | Implementação                   |
|---------|-----------------------|----------------------------------|---------------------------------|
| SEC-01  | {{REQ_SEC_1}}         | {{STANDARD_1}}                   | {{IMPL_1}}                      |
| SEC-02  | {{REQ_SEC_2}}         | {{STANDARD_2}}                   | {{IMPL_2}}                      |

### 4.3 Performance Global

| Métrica              | SLA                              | Medição                         |
|----------------------|----------------------------------|---------------------------------|
| Latência (p95)       | < {{SLA_LATENCIA}} ms            | {{COMO_MEDIR_LAT}}              |
| Throughput           | > {{SLA_THROUGHPUT}} req/s       | {{COMO_MEDIR_THROUGHPUT}}       |
| Disponibilidade      | {{SLA_DISPONIBILIDADE}}%         | {{COMO_MEDIR_DISP}}             |

---

## 5. Integrações

| Sistema Externo      | Protocolo  | Direção    | SLA              | Responsável          |
|----------------------|------------|------------|------------------|----------------------|
| {{SISTEMA_EXT_1}}    | REST/gRPC  | Bidirecional| {{SLA_EXT_1}}   | {{RESP_EXT_1}}       |
| {{SISTEMA_EXT_2}}    | Mensageria | Produtor   | {{SLA_EXT_2}}    | {{RESP_EXT_2}}       |

---

## 6. Dados Compartilhados

### 6.1 Entidades Globais

| Entidade             | Owner                | Consumidores         | Política de Acesso   |
|----------------------|----------------------|----------------------|----------------------|
| {{ENTIDADE_1}}       | {{OWNER_1}}          | S1, S2, S3           | {{POLITICA_1}}       |
| {{ENTIDADE_2}}       | {{OWNER_2}}          | S2, S4               | {{POLITICA_2}}       |

### 6.2 Políticas de Dados

- Retenção: {{POLITICA_RETENCAO}}
- LGPD/GDPR: {{POLITICA_PRIVACIDADE}}
- Backup: {{POLITICA_BACKUP}}

---

## 7. Stakeholders

| Stakeholder          | Papel                | Expectativa                     | Frequência Comunicação |
|----------------------|----------------------|---------------------------------|------------------------|
| {{STAKEHOLDER_1}}    | Product Owner        | {{EXPECTATIVA_1}}               | Semanal                |
| {{STAKEHOLDER_2}}    | Tech Lead            | {{EXPECTATIVA_2}}               | Diária                 |

---

## 8. Riscos do Épico

| Risco                | Probabilidade | Impacto | Mitigação                       | Owner                |
|----------------------|---------------|---------|---------------------------------|----------------------|
| {{RISCO_1}}          | Alta          | Crítico | {{MITIGACAO_1}}                 | {{OWNER_RISCO_1}}    |
| {{RISCO_2}}          | Média         | Alto    | {{MITIGACAO_2}}                 | {{OWNER_RISCO_2}}    |

---

## 9. Cronograma Macro

| Fase                 | Início       | Fim          | Milestone                       |
|----------------------|--------------|--------------|---------------------------------|
| Análise & Design     | {{DATA_I1}}  | {{DATA_F1}}  | Design aprovado                 |
| Implementação S1     | {{DATA_I2}}  | {{DATA_F2}}  | S1 em staging                   |
| Implementação S2-S3  | {{DATA_I3}}  | {{DATA_F3}}  | Integração completa             |
| Testes & Hardening   | {{DATA_I4}}  | {{DATA_F4}}  | QA sign-off                     |
| GA (General Avail.)  | {{DATA_I5}}  | {{DATA_F5}}  | Produção                        |

---

## 10. Critérios de Sucesso do Épico

- [ ] Todos os requisitos de compliance atendidos e auditados
- [ ] Performance dentro dos SLAs definidos
- [ ] Cobertura de testes ≥ {{COBERTURA_MIN}}%
- [ ] Zero vulnerabilidades críticas/altas
- [ ] Documentação completa (API, operacional, runbook)

---

*Criado em: {{DATA_CRIACAO}}*
*Última revisão: {{DATA_REVISAO}}*
