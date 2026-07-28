# Design - Sub-Funcionalidade 1

> **Requirements:** [requirements.md](./requirements.md)
> **Epic Design:** [epic-design.md](../epic-design.md)
> **Status:** {{STATUS}}

---

## 1. Arquitetura Local

> Como este módulo se integra à arquitetura macro definida no epic-design.

```
┌──────────────────────────────────────────┐
│          Sub-Funcionalidade 1            │
├──────────┬──────────┬────────────────────┤
│ {{LAYER_1}} │ {{LAYER_2}} │ {{LAYER_3}}       │
└──────────┴──────────┴────────────────────┘
       │                    │
       ▼                    ▼
[Camada Compartilhada]  [{{BANCO}}]
```

---

## 2. Componentes Locais

| Componente           | Responsabilidade                 | Interface Exposta               |
|----------------------|----------------------------------|---------------------------------|
| {{COMP_1}}           | {{RESP_1}}                       | {{INTERFACE_1}}                 |
| {{COMP_2}}           | {{RESP_2}}                       | {{INTERFACE_2}}                 |

---

## 3. Contratos de API Locais

### 3.1 APIs Expostas (para outras Sub-Funcs)

```
{{METHOD}} {{PATH}}
```

**Request:** `{{REQUEST_SCHEMA}}`
**Response:** `{{RESPONSE_SCHEMA}}`

### 3.2 APIs Consumidas

| API                  | Provider             | Contrato                        |
|----------------------|----------------------|---------------------------------|
| {{API_CONSUMIDA_1}}  | {{PROVIDER_1}}       | {{REF_CONTRATO_1}}              |

---

## 4. Modelo de Dados Local

```
{{ENTIDADE_LOCAL}} {
  id: UUID [PK]
  {{CAMPO_L1}}: {{TIPO_L1}}
  {{CAMPO_L2}}: {{TIPO_L2}}
  {{FK}}: UUID [FK -> {{ENTIDADE_GLOBAL}}.id]
  created_at: timestamp
  updated_at: timestamp
}
```

---

## 5. Lógica de Negócio Principal

```
1. {{PASSO_1}}
2. {{PASSO_2}}
3. {{PASSO_3}}
   - Se {{CONDICAO_A}}: {{ACAO_A}}
   - Se {{CONDICAO_B}}: {{ACAO_B}}
4. {{PASSO_4}}
```

---

## 6. Tratamento de Erros

| Cenário              | Erro                 | Ação                            | Retry?   |
|----------------------|----------------------|---------------------------------|----------|
| {{CENARIO_1}}        | {{ERRO_1}}           | {{ACAO_ERRO_1}}                 | Sim/Não  |
| {{CENARIO_2}}        | {{ERRO_2}}           | {{ACAO_ERRO_2}}                 | Sim/Não  |

---

## 7. Testes Específicos

| Tipo         | O que testar                     | Prioridade                      |
|--------------|----------------------------------|---------------------------------|
| Unit         | {{TEST_UNIT_1}}                  | Alta                            |
| Integration  | {{TEST_INTEG_1}}                 | Alta                            |
| Contract     | {{TEST_CONTRACT_1}}              | Média                           |

---

*Criado em: {{DATA_CRIACAO}}*
*Última revisão: {{DATA_REVISAO}}*
