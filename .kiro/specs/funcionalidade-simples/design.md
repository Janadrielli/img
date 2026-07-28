# Design - Funcionalidade Simples

> **Spec vinculada:** [requirements.md](./requirements.md)
> **Status:** {{STATUS}} | **Revisores:** {{REVISORES}}

---

## 1. Visão Geral da Arquitetura

> Diagrama ou descrição textual da arquitetura proposta.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  {{CAMADA_1}} │────▶│  {{CAMADA_2}} │────▶│  {{CAMADA_3}} │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Decisões Arquiteturais (ADRs)

| ADR   | Decisão                          | Justificativa                   | Alternativas Descartadas        |
|-------|----------------------------------|---------------------------------|---------------------------------|
| ADR-1 | {{DECISAO_1}}                    | {{JUSTIFICATIVA_1}}             | {{ALTERNATIVA_1}}               |

---

## 2. Componentes

| Componente           | Responsabilidade                 | Tecnologia                      |
|----------------------|----------------------------------|---------------------------------|
| {{COMPONENTE_1}}     | {{RESPONSABILIDADE_1}}           | {{TECH_1}}                      |
| {{COMPONENTE_2}}     | {{RESPONSABILIDADE_2}}           | {{TECH_2}}                      |

---

## 3. Contratos de API

### 3.1 {{ENDPOINT_1}}

```
{{METHOD}} {{PATH}}
```

**Request:**
```json
{
  "{{CAMPO_1}}": "{{TIPO_1}}",
  "{{CAMPO_2}}": "{{TIPO_2}}"
}
```

**Response (200):**
```json
{
  "{{CAMPO_RESP_1}}": "{{TIPO_RESP_1}}",
  "{{CAMPO_RESP_2}}": "{{TIPO_RESP_2}}"
}
```

**Erros:**
| Código | Descrição                        | Quando                          |
|--------|----------------------------------|---------------------------------|
| 400    | {{ERRO_400}}                     | {{CONDICAO_400}}                |
| 404    | {{ERRO_404}}                     | {{CONDICAO_404}}                |
| 500    | {{ERRO_500}}                     | {{CONDICAO_500}}                |

---

## 4. Modelo de Dados

### 4.1 Entidades

```
{{ENTIDADE_1}} {
  id: UUID [PK]
  {{CAMPO_A}}: {{TIPO_A}}
  {{CAMPO_B}}: {{TIPO_B}}
  created_at: timestamp
  updated_at: timestamp
}
```

### 4.2 Relacionamentos

```
{{ENTIDADE_1}} ||--o{ {{ENTIDADE_2}} : "{{RELACAO}}"
```

---

## 5. Fluxo de Dados

```
1. {{PASSO_1}}
2. {{PASSO_2}}
3. {{PASSO_3}}
4. {{PASSO_4}}
```

---

## 6. Segurança

| Aspecto              | Abordagem                        | Referência                      |
|----------------------|----------------------------------|---------------------------------|
| Autenticação         | {{AUTH_METODO}}                   | {{AUTH_REF}}                    |
| Autorização          | {{AUTHZ_METODO}}                 | {{AUTHZ_REF}}                  |
| Criptografia         | {{CRYPTO_METODO}}                | {{CRYPTO_REF}}                 |

---

## 7. Observabilidade

| Tipo       | Ferramenta         | O que monitorar                 |
|------------|--------------------|---------------------------------|
| Logs       | {{LOG_TOOL}}       | {{LOG_ITEMS}}                   |
| Métricas   | {{METRIC_TOOL}}    | {{METRIC_ITEMS}}                |
| Traces     | {{TRACE_TOOL}}     | {{TRACE_ITEMS}}                 |
| Alertas    | {{ALERT_TOOL}}     | {{ALERT_CONDICOES}}             |

---

## 8. Estratégia de Testes

| Nível        | Escopo                           | Ferramenta                      |
|--------------|----------------------------------|---------------------------------|
| Unitário     | {{ESCOPO_UNIT}}                  | {{TOOL_UNIT}}                   |
| Integração   | {{ESCOPO_INTEG}}                 | {{TOOL_INTEG}}                  |
| E2E          | {{ESCOPO_E2E}}                   | {{TOOL_E2E}}                    |

---

## 9. Plano de Rollout

| Fase         | Descrição                        | Critério de Avanço              |
|--------------|----------------------------------|---------------------------------|
| Canary       | {{DESC_CANARY}}                  | {{CRITERIO_CANARY}}             |
| Gradual      | {{DESC_GRADUAL}}                 | {{CRITERIO_GRADUAL}}            |
| GA           | {{DESC_GA}}                      | {{CRITERIO_GA}}                 |

---

## 10. Riscos Técnicos

| Risco                | Probabilidade | Impacto | Mitigação                       |
|----------------------|---------------|---------|---------------------------------|
| {{RISCO_1}}          | Alta          | Alto    | {{MITIGACAO_1}}                 |
| {{RISCO_2}}          | Média         | Médio   | {{MITIGACAO_2}}                 |

---

*Criado em: {{DATA_CRIACAO}}*
*Última revisão: {{DATA_REVISAO}}*
