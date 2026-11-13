# Train your own model on Tamarind

A training script becomes a Tamarind tool by adding a few decorators and deploying the folder
as a custom tool. The platform runs the script on the GPU you ask for, injects the
hyperparameters you declare, records what you log, and keeps the trained model as a versioned
tool you can run, put in a pipeline, or benchmark against Tamarind's own models.

You keep the training loop. Nothing here owns your data loader, your loss, or your framework.

## The script

```python
import tamarind as tm

@tm.training_run(
    gpu="A100",
    timeout_hours=12,
    hyperparameters={
        "lr": tm.Float(1e-4, 1e-6, 1e-2),
        "epochs": tm.Int(10),
        "rank": tm.Choice(8, [4, 8, 16, 32]),
    },
    objective=("val/spearman", "max"),
    artifact="checkpoints/best",
)
def main():
    hp = tm.hyperparameters()                     # {"lr": ..., "epochs": ..., "rank": ...}
    model = build(rank=hp["rank"])
    for step, batch in enumerate(loader):
        loss = train_step(model, batch, lr=hp["lr"])
        tm.log({"train/loss": loss}, step=step)
        if step % 500 == 0:
            metrics = tm.evaluate(model.predict(val_x), val_y)
            tm.log(metrics, step=step)
            save(model, tm.checkpoint(step=step, metrics=metrics))

@tm.predictor(gpu="L4", inputs={"sequence": "sequence"}, outputs={"affinity": "number"})
class BindingModel:
    def load(self, artifact_dir): ...
    def predict(self, inputs): ...
    def embed(self, inputs): ...                   # optional: powers feature extraction

@tm.evaluator(metrics={"spearman": "max", "mae": "min"})
def score(predictions, truths):
    return {"spearman": ..., "mae": ...}

if __name__ == "__main__":
    main()
```

| Decorator | On | What the platform does with it |
|---|---|---|
| `@tm.training_run` | the function to invoke | Schedules the run with `gpu`/`memory`/`cpu`, caps it at `timeout_hours`, offers each hyperparameter as a submit setting and a sweep axis, ranks runs by `objective`, registers `artifact` as the model |
| `@tm.predictor` | a class with `load()` and `predict()` | Serves the artifact as a tool with the declared `inputs` and `outputs`; `embed()` is optional |
| `@tm.evaluator` | `score(predictions, truths)` | The same scoring for validation during training and for benchmarks |
| `@tm.splitter` | `split(dataset)` | A custom train/validation split |

Every decorator argument must be a literal: a number, string, bool, list, tuple or dict of
those, or `tm.Float` / `tm.Int` / `tm.Str` / `tm.Bool` / `tm.Choice` with literal arguments.
The platform's build reads the folder without importing it (the block is needed before the
image that holds your dependencies exists), so `gpu=os.environ["GPU"]` fails the build with the
file and line.

## At run time

| Call | Does |
|---|---|
| `tm.hyperparameters()` | The chosen values, typed. On the platform, from the run's file; locally, the declared defaults with environment-variable overrides (`epochs=3 python train.py`) |
| `tm.log({...}, step=n)` | Appends a JSON line to the run's metrics file. Never raises; non-finite numbers become null |
| `tm.checkpoint(path=None, step=, metrics=)` | Returns the directory to save into (the artifact dir by default) and records the step and metrics, so the platform can pick the best checkpoint |
| `tm.evaluate(predictions, truths)` | Calls your `@tm.evaluator` |
| `tm.artifact_dir()` / `tm.run_dir()` | Where the model and the run's outputs go (`/app/out/...` on the platform, `./tamarind_run/...` locally) |
| `tm.is_platform()` | True inside a Tamarind run |

The platform sets `TAMARIND_RUN_DIR`, `TAMARIND_HYPERPARAMETERS` (a JSON file),
`TAMARIND_METRICS_FILE` and `TAMARIND_ARTIFACT_DIR` (the directory the run's `artifact` names,
which `tm.artifact_dir()` returns, so a hand-written block works without decorators). Off the platform the SDK only writes local files, so the same script
runs on a laptop unchanged.

## Deploy

A training tool is a custom tool: a folder with a `Dockerfile`, a `run.sh` that starts your
script, and a `config.json`. Deploy it like any other custom tool:

```
tamarind custom-tools build my-trainer ./my-trainer
```

At build, the platform reads the decorators out of your `.py` files and stores the `finetune`
block they describe on the version it builds. Your files are never rewritten: `config.json` needs
no `finetune` block, and the block lives on the version and on every run submitted against it.
An agent deploying through `deployCustomTool`, the SDK's `CustomTool.build()` and the web editor
all go through that same build, so there is one reading of the decorators and it is the
platform's. A decorator the build cannot read (a non-literal argument, say) fails the build with
the file and line.

You can also write the block by hand in `config.json`, in any language, and skip the decorators
entirely. If a folder has both, they must agree; a block that contradicts the decorators fails
the build naming both, rather than one silently winning:

```json
"finetune": {
  "entrypoint": "train.py:main",
  "timeoutHours": 12,
  "hyperparameters": {
    "lr": {"type": "float", "default": 1e-4, "min": 1e-6, "max": 1e-2},
    "epochs": {"type": "int", "default": 10},
    "rank": {"type": "int", "default": 8, "options": [4, 8, 16, 32]}
  },
  "objective": {"metric": "val/spearman", "mode": "max"},
  "artifact": "checkpoints/best",
  "predictor": {"class": "model.py:BindingModel", "gpuType": "L4", ...},
  "evaluator": "train.py:score"
}
```

The Dockerfile stays yours. Base model weights go into the image at build time; the runtime
has no network. The trained artifact goes out through `tm.artifact_dir()`, never into the image.
