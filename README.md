# p2i-sdk

Typed Python client for the local P2I HTTP/JSON API. This repository contains
no tracing implementation and no AI provider integration.

```python
from p2i_sdk import Client

client = Client()  # 127.0.0.1:8000
ir = client.model_ir()
state = client.harness()
preview = client.command("preview", {"type": "set_parameter", "target": "...", "parameter": "p", "value": 0.2})
```

Install `p2i-core`, then `python -m pip install -e .`. `Client.tool(name,
arguments)` uses P2I's provider-neutral structured tool protocol. Network
requests go only to the configured P2I origin; the default is loopback. For
in-process model editing, use `p2i.Harness` directly.

Run the SDK tests with `python -m unittest discover -s tests -v`.

## Model checkpoints

```python
client = Client(timeout=60)
client.save_checkpoint("edited.p2i", expected_revision=1)
client.open_checkpoint("edited.p2i")
```

`save_checkpoint(..., include_inputs=False)` omits examples when only the
weights and structure are needed. Use `p2i.load_model(path)` for a regular
trainable PyTorch model. Browser reopening requires saved inputs; failed
imports leave the live session intact. Custom models use the active server's
original template, or can be restored in Python with
`p2i.Harness.load(path, model=YourModel(...))`.
