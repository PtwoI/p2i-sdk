# p2i-sdk

Typed, agent-neutral client for P2I's local API and structured tools.

## Boundary

Client requests/responses for model inspection, actions, revisions, skills and evaluation. It must not duplicate tracing, builders, validation or registry logic from [p2i-core](https://github.com/PtwoI/p2i-core). Planned import: `p2i_sdk`; the existing `p2i` import stays with core.

## Migration status

**Repository initialized; no SDK package is released.** Typed models and tool contracts currently live in [PtwoI/p2i](https://github.com/PtwoI/p2i). Continue using that working project until a versioned API is extracted and tested.

[p2i-cli](https://github.com/PtwoI/p2i-cli) and [p2i-ai-plugin](https://github.com/PtwoI/p2i-ai-plugin) may depend on this SDK; core must not.

MIT licensed.
