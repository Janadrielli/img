# On-Demand Context (Manual Inclusion)

> Este arquivo é incluído APENAS quando o desenvolvedor
> solicita explicitamente sua ativação.
> Útil para contextos especializados que não devem poluir
> toda interação.

---

## Contexto: Migração de Sistema Legado

> Ative quando trabalhando em migração de código legado.

### Regras de Migração
- Manter compatibilidade reversa durante período de transição.
- Strangler Fig pattern: substituir incrementalmente, nunca big-bang.
- Testes de paridade: output do sistema novo = output do legado.
- Feature flags para rotear tráfego gradualmente.

### Padrões de Coexistência
- Anti-corruption layer entre legado e novo.
- Adapters para traduzir contratos antigos → novos.
- Logs de divergência para detectar diferenças comportamentais.

---

## Contexto: Refatoração de Grande Escala

> Ative quando realizando refatoração que afeta muitos arquivos.

### Estratégia
- Refatorar em PRs pequenos e focados (< 300 linhas por PR).
- Cada PR deve manter todos os testes passando.
- Extrair → Testar → Substituir (nunca no mesmo PR).
- Documentar decisões em ADRs.

---

## Contexto: Debugging de Produção

> Ative quando investigando issues em produção.

### Checklist de Investigação
1. Verificar dashboards de métricas (latência, errors, saturation).
2. Correlacionar com deploys recentes (últimas 24h).
3. Analisar logs com correlation ID do request.
4. Reproduzir em staging com dados sanitizados.
5. Postmortem obrigatório para incidentes P0/P1.

---

## Contexto: Performance Optimization

> Ative quando focando em otimização de performance.

### Princípios
- Medir antes de otimizar (profile primeiro).
- Otimizar hot paths; ignorar cold paths.
- Caching: definir TTL, invalidação e fallback.
- Benchmark antes/depois com dados representativos.

---

## Placeholder para Contextos Sob Demanda

### Contexto: {{NOME_CONTEXTO}}

> Ative quando {{CONDICAO_ATIVACAO}}.

- {{REGRA_1}}
- {{REGRA_2}}
- {{REGRA_3}}

---

*Inclusão: manual (sob demanda)*
*Última atualização: {{DATA}}*
