"""Train your own model on Tamarind: ``import tamarind as tm``.

Decorate the parts of a training script the platform needs to find, keep the rest however you
like, and deploy the folder as a custom tool. See ``docs/finetune.md``.

    import tamarind as tm

    @tm.training_run(gpu="H100", timeout_hours=12,
                     hyperparameters={"lr": tm.Float(1e-4, 1e-6, 1e-2), "epochs": tm.Int(10)},
                     objective=("val/spearman", "max"))
    def main():
        cfg = tm.hyperparameters()
        for step, loss in train(lr=cfg["lr"], epochs=cfg["epochs"]):
            tm.log({"train/loss": loss}, step=step)
        tm.checkpoint(metrics=tm.evaluate(preds, truths))

    @tm.predictor(gpu="L4", inputs={"sequence": "sequence"}, outputs={"affinity": "number"})
    class Model:
        def load(self, artifact_dir): ...
        def predict(self, inputs): ...

    @tm.evaluator(metrics={"spearman": "max"})
    def score(predictions, truths): ...
"""

from tamarind.finetune.compile import (
    CompiledFinetune,
    FinetuneCompileError,
    SyncResult,
    compile_folder,
    compile_sources,
    sync_config_json,
)
from tamarind.finetune.decorators import evaluator, predictor, splitter, training_run
from tamarind.finetune.runtime import (
    artifact_dir,
    checkpoint,
    evaluate,
    hyperparameters,
    is_platform,
    log,
    run_dir,
)
from tamarind.finetune.spec import Bool, Choice, FinetuneSpecError, Float, Int, Str

__all__ = [
    "Bool",
    "Choice",
    "CompiledFinetune",
    "FinetuneCompileError",
    "FinetuneSpecError",
    "Float",
    "Int",
    "Str",
    "SyncResult",
    "artifact_dir",
    "checkpoint",
    "compile_folder",
    "compile_sources",
    "evaluate",
    "evaluator",
    "hyperparameters",
    "is_platform",
    "log",
    "predictor",
    "run_dir",
    "splitter",
    "sync_config_json",
    "training_run",
]
