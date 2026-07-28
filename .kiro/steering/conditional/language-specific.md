# Language-Specific Guidelines (Conditional)

> Ativado por glob pattern. Cada seção aplica-se apenas quando
> os arquivos em edição correspondem ao padrão indicado.

---

## Condição: `**/*.py` (Python)

- Usar type hints em toda assinatura de função.
- Formatter: `ruff format` | Linter: `ruff check`.
- Imports organizados: stdlib → third-party → local.
- Dataclasses/Pydantic para DTOs; evitar dicts soltos.
- Async por padrão para I/O-bound.

---

## Condição: `**/*.ts`, `**/*.tsx` (TypeScript/React)

- Strict mode habilitado (`strict: true` no tsconfig).
- Componentes funcionais com hooks; evitar class components.
- Props tipadas com interfaces (prefixo `I` opcional conforme time).
- CSS-in-JS ou CSS Modules; evitar CSS global.
- Server Components por padrão (Next.js); `'use client'` apenas quando necessário.

---

## Condição: `**/*.pas`, `**/*.dfm` (Delphi/Object Pascal)

- Prefixo `T` para classes, `I` para interfaces, `E` para exceptions.
- Uses organizados: interface → implementation.
- Liberar recursos com try/finally ou ownership (ARC/manual).
- DataModules para acesso a dados; separar lógica de UI.

---

## Condição: `**/*.go` (Go)

- Erros retornados, nunca ignorados (`_ = err` é proibido).
- Interfaces pequenas (1-3 métodos).
- Package names: singular, curto, sem underscores.
- Context propagado em toda chain de chamadas.

---

## Condição: `**/*.sql`

- Keywords em UPPERCASE (`SELECT`, `FROM`, `WHERE`).
- Aliases significativos (não `t1`, `t2`).
- Comentar queries complexas com propósito de negócio.
- Nunca usar `SELECT *` em código de produção.

---

## Condição: `**/Dockerfile`, `**/*.yml` (Infra)

- Multi-stage builds para reduzir imagem final.
- Non-root user no container.
- Health checks definidos.
- Secrets via environment variables ou mounted secrets.

---

## Placeholder para Linguagens Adicionais

### Condição: `**/*.{{EXT}}` ({{LINGUAGEM}})
- {{REGRA_1}}
- {{REGRA_2}}
- {{REGRA_3}}

---

*Inclusão: conditional (glob pattern)*
*Última atualização: {{DATA}}*
