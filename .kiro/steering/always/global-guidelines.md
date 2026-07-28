# Global Guidelines (Always Injected)

> Estas diretrizes são injetadas em TODA interação com o agente,
> independentemente do contexto ou linguagem.

---

## Idioma e Comunicação

- Responder no idioma do usuário (padrão: Português BR).
- Explicações técnicas devem ser concisas e acionáveis.
- Preferir exemplos de código a descrições abstratas.

---

## Padrões de Código

- Todo código gerado DEVE seguir as convenções da [constitution.md](../../constitution.md).
- Nomear variáveis/funções de forma auto-descritiva (evitar abreviações obscuras).
- Incluir tratamento de erro em todo código de produção.
- Nunca gerar código com secrets hardcoded.

---

## Segurança (Sempre Ativo)

- Tratar toda entrada externa como potencialmente maliciosa.
- Usar prepared statements para queries de banco.
- Validar e sanitizar inputs antes de processamento.
- Nunca logar dados sensíveis (PII, tokens, senhas).

---

## Qualidade

- Código gerado deve ser testável (injeção de dependência, interfaces).
- Preferir composição sobre herança.
- Funções com responsabilidade única (SRP).
- Máximo ~30 linhas por função (exceções justificadas).

---

## Documentação

- Toda função pública deve ter docstring/JSDoc/XML-doc.
- Comentários explicam o "porquê", não o "o quê".
- README atualizado quando comportamento público muda.

---

## Placeholder para Customização

> Adicione regras específicas do seu projeto abaixo:

- {{REGRA_ESPECIFICA_1}}
- {{REGRA_ESPECIFICA_2}}

---

*Inclusão: always*
*Última atualização: {{DATA}}*
