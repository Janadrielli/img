# Constitution - DNA Inegociável da Engenharia

> Este documento define os princípios fundamentais, invariantes e restrições absolutas
> que governam **todo** código produzido neste repositório, independentemente da linguagem,
> framework ou domínio de negócio escolhido.

---

## 1. Princípios Fundamentais

| #  | Princípio                        | Descrição                                                                 |
|----|----------------------------------|---------------------------------------------------------------------------|
| P1 | **Correção acima de velocidade** | Código correto e testável tem prioridade sobre entregas rápidas.          |
| P2 | **Segurança por padrão**         | Toda entrada é hostil até prova em contrário (OWASP Top 10).             |
| P3 | **Observabilidade obrigatória**  | Todo componente deve emitir logs estruturados, métricas e traces.         |
| P4 | **Imutabilidade de contratos**   | APIs publicadas seguem versionamento semântico; breaking changes = major. |
| P5 | **Simplicidade intencional**     | Complexidade só é aceita quando justificada por requisito mensurável.     |

---

## 2. Invariantes de Qualidade

### 2.1 Testes
- [ ] Cobertura mínima: **80%** em linhas e branches para código de produção.
- [ ] Testes unitários são obrigatórios para toda lógica de negócio.
- [ ] Testes de integração cobrem contratos entre módulos/serviços.

### 2.2 Segurança
- [ ] Nenhum segredo (chave, token, senha) pode existir em texto claro no repositório.
- [ ] Dependências são auditadas antes de merge (CVE conhecidos = bloqueio).
- [ ] Inputs externos são validados e sanitizados na fronteira do sistema.

### 2.3 Performance
- [ ] Endpoints críticos respondem em < **{{SLA_MS}}** ms no p95.
- [ ] Queries de banco possuem índices documentados; full-scan é proibido em produção.

---

## 3. Convenções de Código

### 3.1 Nomenclatura
- Variáveis e funções: `camelCase` ou `snake_case` conforme idioma da linguagem.
- Constantes: `UPPER_SNAKE_CASE`.
- Classes/Tipos: `PascalCase`.

### 3.2 Estrutura de Commits
```
<tipo>(<escopo>): <descrição curta>

[corpo opcional]

[rodapé opcional: BREAKING CHANGE, refs #issue]
```

Tipos permitidos: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`, `security`.

### 3.3 Branching
- `main` — produção, protegida.
- `develop` — integração contínua.
- `feature/<nome>` — funcionalidades.
- `fix/<nome>` — correções.
- `release/<versão>` — preparação de release.

---

## 4. Restrições Absolutas (Não-Negociáveis)

1. **Nunca** commitar diretamente em `main`.
2. **Nunca** desabilitar linters/formatters sem aprovação documentada.
3. **Nunca** ignorar falhas de CI para fazer merge.
4. **Nunca** expor dados sensíveis em logs (PII, tokens, senhas).
5. **Nunca** usar `// TODO` sem issue vinculada e prazo.

---

## 5. Placeholders para Customização

> Substitua os valores abaixo ao definir o projeto concreto:

| Placeholder            | Descrição                                    | Valor Padrão |
|------------------------|----------------------------------------------|--------------|
| `{{LINGUAGEM}}`        | Linguagem principal do projeto               | —            |
| `{{FRAMEWORK}}`        | Framework principal                          | —            |
| `{{SLA_MS}}`           | SLA de resposta em milissegundos (p95)       | 500          |
| `{{COBERTURA_MIN}}`    | Cobertura mínima de testes (%)               | 80           |
| `{{BANCO_DADOS}}`      | Sistema de banco de dados                    | —            |
| `{{DEPLOY_TARGET}}`    | Ambiente de deploy (cloud, on-prem, hybrid)  | —            |

---

## 6. Governança deste Documento

- Alterações requerem **review de pelo menos 2 pessoas**.
- Toda exceção deve ser registrada como ADR (Architecture Decision Record).
- Revisão obrigatória a cada **trimestre** ou a cada mudança de stack.

---

*Última atualização: {{DATA}}*
*Responsável: {{RESPONSAVEL}}*
