# Design - Sub-Funcionalidade 2

> **Requirements:** [requirements.md](./requirements.md)
> **Epic Design:** [epic-design.md](../epic-design.md)
> **Status:** {{STATUS}}

---

## 1. Arquitetura Local

```
┌──────────────────────────────────────────┐
│          Sub-Funcionalidade 2            │
├──────────┬──────────┬────────────────────┤
│ {{LAYER_1}} │ {{LAYER_2}} │ {{LAYER_3}}       │
└──────────┴──────────┴────────────────────┘
       │                    │
       ▼                    ▼
[Sub-Func-1 API]        [{{BANCO}}]
```

---

## 2. Componentes Locais

| Componente           | Responsabilidade                 | Interface Exposta               |
|----------------------|----------------------------------|---------------------------------|
| {{COMP_1}}           | {{RESP_1}}                       | {{INTERFACE_1}}                 |
| {{COMP_2}}           | {{RESP_2}}                       | {{INTERFACE_2}}                 |

---

## 3. Contratos de API Locais

### 3.1 APIs Expostas

```
{{METHOD}} {{PATH}}
```

**Request:** `{{REQUEST_SCHEMA}}`
**Response:** `{{RESPONSE_SCHEMA}}`

### 3.2 APIs Consumidas

| API                  | Provider             | Contrato                        |
|----------------------|----------------------|---------------------------------|
| {{API_DE_S1}}        | Sub-Func-1           | {{REF_CONTRATO_S1}}             |

---

## 4. Modelo de Dados Local

```
{{ENTIDADE_LOCAL}} {
  id: UUID [PK]
  {{CAMPO_L1}}: {{TIPO_L1}}
  {{FK}}: UUID [FK -> {{ENTIDADE_S1}}.id]
  created_at: timestamp
  updated_at: timestamp
}
```

---

## 5. Tratamento de Erros

| Cenário              | Erro                 | Ação                            |
|----------------------|----------------------|---------------------------------|
| {{CENARIO_1}}        | {{ERRO_1}}           | {{ACAO_ERRO_1}}                 |

---

*Criado em: {{DATA_CRIACAO}}*
*Última revisão: {{DATA_REVISAO}}*
