# Tasks - Funcionalidade Simples

> **Spec vinculada:** [requirements.md](./requirements.md) | [design.md](./design.md)
> **Estimativa total:** {{HORAS_TOTAL}}h | **Status geral:** {{STATUS}}

---

## Legenda de Status

| Ícone | Status       |
|-------|--------------|
| ⬜    | Não iniciada |
| 🔄    | Em progresso |
| ✅    | Concluída    |
| ❌    | Bloqueada    |
| ⏭️    | Pulada       |

---

## Fase 1: Setup e Infraestrutura

| #  | Task                             | Status | Estimativa | Dependências | Responsável |
|----|----------------------------------|--------|------------|--------------|-------------|
| 1  | {{TASK_SETUP_1}}                 | ⬜     | {{H}}h     | —            | {{RESP}}    |
| 2  | {{TASK_SETUP_2}}                 | ⬜     | {{H}}h     | #1           | {{RESP}}    |

---

## Fase 2: Implementação Core

| #  | Task                             | Status | Estimativa | Dependências | Responsável |
|----|----------------------------------|--------|------------|--------------|-------------|
| 3  | {{TASK_CORE_1}}                  | ⬜     | {{H}}h     | #2           | {{RESP}}    |
| 4  | {{TASK_CORE_2}}                  | ⬜     | {{H}}h     | #3           | {{RESP}}    |
| 5  | {{TASK_CORE_3}}                  | ⬜     | {{H}}h     | #3           | {{RESP}}    |

---

## Fase 3: Testes e Validação

| #  | Task                             | Status | Estimativa | Dependências | Responsável |
|----|----------------------------------|--------|------------|--------------|-------------|
| 6  | Escrever testes unitários        | ⬜     | {{H}}h     | #4, #5       | {{RESP}}    |
| 7  | Escrever testes de integração    | ⬜     | {{H}}h     | #4, #5       | {{RESP}}    |
| 8  | Testes E2E (se aplicável)        | ⬜     | {{H}}h     | #6, #7       | {{RESP}}    |

---

## Fase 4: Documentação e Deploy

| #  | Task                             | Status | Estimativa | Dependências | Responsável |
|----|----------------------------------|--------|------------|--------------|-------------|
| 9  | Atualizar documentação           | ⬜     | {{H}}h     | #4, #5       | {{RESP}}    |
| 10 | Configurar CI/CD                 | ⬜     | {{H}}h     | #6, #7       | {{RESP}}    |
| 11 | Deploy canary/staging            | ⬜     | {{H}}h     | #8, #10      | {{RESP}}    |
| 12 | Validação em produção            | ⬜     | {{H}}h     | #11          | {{RESP}}    |

---

## Notas de Implementação

### Critérios de "Done" por Task
- [ ] Código implementado e revisado
- [ ] Testes passando (unit + integração)
- [ ] Sem warnings de linter
- [ ] Documentação atualizada (se API pública)
- [ ] PR aprovado por pelo menos 1 reviewer

### Dependências Externas
| Dependência          | Responsável Externo  | Prazo     | Status    |
|----------------------|----------------------|-----------|-----------|
| {{DEP_EXTERNA_1}}    | {{RESP_EXT_1}}       | {{PRAZO}} | Pendente  |

---

## Histórico de Progresso

| Data       | Tasks Concluídas | Observações                     |
|------------|------------------|---------------------------------|
| {{DATA_1}} | —                | Início do desenvolvimento       |

---

*Criado em: {{DATA_CRIACAO}}*
*Última atualização: {{DATA_ATUALIZACAO}}*
