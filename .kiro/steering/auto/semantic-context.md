# Semantic Context (Auto-Injected)

> Injeção semântica por similaridade vetorial.
> Este arquivo é incluído automaticamente quando o contexto da conversa
> tem alta similaridade com os tópicos aqui definidos.

---

## Quando Falar sobre Banco de Dados

- Preferir migrations versionadas (nunca alterar schema manualmente).
- Indices devem ser documentados com justificativa.
- Queries críticas devem ter EXPLAIN analisado.
- Usar connection pooling; nunca abrir conexões ad-hoc.

---

## Quando Falar sobre APIs

- Seguir padrão RESTful ou gRPC conforme definido no design.
- Versionamento via path (`/v1/`, `/v2/`) ou header.
- Respostas de erro seguem formato padronizado:
  ```json
  {
    "error": { "code": "{{CODE}}", "message": "{{MSG}}", "details": [] }
  }
  ```
- Rate limiting documentado em headers de resposta.

---

## Quando Falar sobre Autenticação

- JWT para APIs stateless; sessions para aplicações web tradicionais.
- Tokens de refresh com rotação automática.
- Logout invalida token no backend (blacklist/revocation).
- MFA recomendado para operações sensíveis.

---

## Quando Falar sobre Testes

- Pirâmide de testes: muitos unit > poucos integration > raros E2E.
- Mocks apenas para dependências externas; evitar mocks internos.
- Testes devem ser determinísticos (sem dependência de hora/rede).
- Nomes de testes: `deve_<resultado>_quando_<condição>`.

---

## Quando Falar sobre Deploy

- CI/CD deve rodar testes + lint + security scan antes de merge.
- Deploy blue/green ou canary para produção.
- Rollback automático se health check falhar em < 5min.
- Feature flags para funcionalidades em desenvolvimento.

---

## Placeholder para Contextos Adicionais

> Adicione blocos temáticos conforme a necessidade do projeto:

### Quando Falar sobre {{TOPICO_1}}
- {{REGRA_1}}
- {{REGRA_2}}

---

*Inclusão: auto (semântica)*
*Última atualização: {{DATA}}*
