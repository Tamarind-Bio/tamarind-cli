"""config.json — the tool manifest, checked before a build is spent on it.

The server validates this file too, and its answer is authoritative. This exists
because of WHEN it answers: a manifest mistake surfaces after packaging, uploading,
extracting and building, which is minutes of waiting to be told about a typo. These
are the rules that can be decided from the file alone, so they are decided instantly.

Two kinds of finding, and the distinction matters:

* An ERROR is something the server will reject. Deploying is pointless.
* A WARNING is something the server ACCEPTS and then ignores. Those are worse in
  practice — the deploy succeeds, the tool runs, and a feature the author asked for
  silently isn't there. `usesMsa` at the top level is the canonical one: nothing
  reads it, so the tool builds happily and never aligns anything.

Deliberately NOT a reimplementation of the server's validator. It mirrors the rules
that are stable and cheap (enums, ranges, the flag placements), and stays silent on
anything it cannot decide locally — an unknown input type is the server's call, not
this file's. Being incomplete is fine; being wrong is not, so when in doubt it says
nothing.

Pure: no network, no clock, no filesystem. The caller reads the file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..errors import ValidationError

# Mirrors of the server's enums (models/custom_tool.py). If the platform adds a GPU
# or a memory size, this list goes stale and reports a false error — so each check
# below says which value it saw, and every message names the server as the authority.
GPU_TYPES = ("None", "T4", "L4", "L40S", "A10", "A100")
LEGACY_GPU_ALIASES = {"A10g": "A10"}
MEMORY_OPTIONS = (
    "8Gi",
    "12Gi",
    "24Gi",
    "32Gi",
    "48Gi",
    "64Gi",
    "90Gi",
    "96Gi",
    "180Gi",
)
MIN_CPU, MAX_CPU = 1, 8
MIN_HOME_DISK_GI, MAX_HOME_DISK_GI = 1, 50
MIN_RUNTIME_SECONDS, MAX_RUNTIME_SECONDS = 60, 24 * 3600

# Top-level keys the server reads. Anything else is passed through untouched, so an
# unknown key is only worth a warning when it LOOKS like a misplaced input flag.
_STRING_FIELDS = ("displayName", "description", "estTime", "paperUrl")
_STRING_LIST_FIELDS = ("functions", "tags")

# Flags that belong on an INPUT and are silently ignored at the top level. This is
# the misplacement that costs a rebuild to discover.
_INPUT_ONLY_FLAGS = ("usesMsa", "designBatching", "designsPerBatch")


@dataclass(frozen=True)
class Findings:
    """What the manifest check concluded."""

    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    # Echoed back so a caller can report what it is about to deploy.
    facts: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


def check(data: Any) -> Findings:
    """Validate a parsed config.json. Never raises — findings are the return value."""
    errors: list[str] = []
    warnings: list[str] = []
    facts: dict[str, Any] = {}

    if not isinstance(data, dict):
        return Findings(errors=(f"config.json must be a JSON object, not {type(data).__name__}.",))

    for key in _STRING_FIELDS:
        value = data.get(key)
        if value is not None and not isinstance(value, str):
            errors.append(f"{key} must be a string, not {type(value).__name__}.")

    for key in _STRING_LIST_FIELDS:
        value = data.get(key)
        if value is not None and (
            not isinstance(value, list) or not all(isinstance(v, str) for v in value)
        ):
            errors.append(f"{key} must be an array of strings.")

    _check_resources(data, errors, warnings)
    _check_est_time(data, errors)
    _check_paper_url(data, errors)
    _check_env_vars(data, errors)
    _check_max_runtime(data, errors)

    # A flag on the wrong level is accepted and ignored — a warning, not an error,
    # because the deploy genuinely succeeds. Saying so here is the whole point.
    for flag in _INPUT_ONLY_FLAGS:
        if flag in data:
            warnings.append(
                f"Top-level {flag!r} is ignored. It belongs on the input it applies "
                f'to, e.g. {{"name": "sequence", "type": "sequence", '
                f'"{flag}": ...}} — as written, the tool will deploy without it.'
            )

    inputs = data.get("inputs", [])
    if inputs is not None and not isinstance(inputs, list):
        errors.append("inputs must be an array.")
        inputs = []
    outputs = data.get("producedOutputs", [])
    if outputs is not None and not isinstance(outputs, list):
        errors.append("producedOutputs must be an array.")
        outputs = []

    _check_inputs(inputs or [], errors)
    _check_msa(inputs or [], errors, facts)
    _check_batching(inputs or [], errors, facts)
    _check_outputs(outputs or [], errors)

    facts["inputs"] = len([i for i in (inputs or []) if isinstance(i, dict)])
    return Findings(errors=tuple(errors), warnings=tuple(warnings), facts=facts)


def _check_resources(data: dict, errors: list[str], warnings: list[str]) -> None:
    gpu = data.get("gpuType")
    if gpu not in (None, ""):
        if not isinstance(gpu, str):
            errors.append("gpuType must be a string.")
        elif LEGACY_GPU_ALIASES.get(gpu, gpu) not in GPU_TYPES:
            errors.append(f"gpuType {gpu!r} is not one of {list(GPU_TYPES)}.")

    memory = data.get("memory")
    if memory not in (None, ""):
        if not isinstance(memory, str):
            errors.append("memory must be a string.")
        elif memory not in MEMORY_OPTIONS:
            errors.append(f"memory {memory!r} is not one of {list(MEMORY_OPTIONS)}.")

    # Asymmetric on purpose, because the server is: it REJECTS a cpu above the cap
    # and silently CLAMPS one below the floor. Reporting both as errors would fail a
    # config that deploys fine; reporting neither hides that the author asked for
    # something they will not get.
    cpu = data.get("cpu")
    if cpu is not None:
        if not _is_int(cpu):
            warnings.append(f"cpu {cpu!r} is not an integer; the server will use {MIN_CPU}.")
        elif int(cpu) > MAX_CPU:
            errors.append(f"cpu must be between {MIN_CPU} and {MAX_CPU}, got {cpu}.")
        elif int(cpu) < MIN_CPU:
            warnings.append(f"cpu {cpu} is below {MIN_CPU}; the server will use {MIN_CPU}.")

    # homeDiskGi is clamped at both ends rather than rejected, so it is never an error.
    disk = data.get("homeDiskGi")
    if disk is not None and (
        not _is_int(disk) or not (MIN_HOME_DISK_GI <= int(disk) <= MAX_HOME_DISK_GI)
    ):
        warnings.append(
            f"homeDiskGi {disk!r} is outside {MIN_HOME_DISK_GI}-{MAX_HOME_DISK_GI}; "
            f"the server will clamp it rather than fail the deploy."
        )


def _check_est_time(data: dict, errors: list[str]) -> None:
    est = data.get("estTime")
    if not isinstance(est, str) or not est:
        return
    parts = est.split(":")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        errors.append(f'estTime must be "H:M:S" (e.g. "5:0:0"), got {est!r}.')
        return
    _, minutes, seconds = (int(p) for p in parts)
    if minutes > 59 or seconds > 59:
        errors.append("estTime minutes and seconds must be 0-59.")


def _check_paper_url(data: dict, errors: list[str]) -> None:
    url = data.get("paperUrl")
    if isinstance(url, str) and url and not url.startswith(("http://", "https://")):
        errors.append("paperUrl must start with http:// or https://.")


def _check_env_vars(data: dict, errors: list[str]) -> None:
    """Shape, and then the harder rule: the VALUES must not live in this file.

    config.json is uploaded verbatim and becomes part of the image layer, so anything
    written here is permanently readable by everyone who can read the tool's source —
    and `envVars` is where API keys go. The filename-based exclusions cannot help: this
    is a file the tool genuinely needs, holding a field the server genuinely reads.

    So the check is on content rather than on a name, and it is an ERROR. `ct config
    --env` stores the same variables server-side without committing them, so refusing
    here removes no capability; it redirects one.
    """
    env = data.get("envVars")
    if env is None:
        return
    if not isinstance(env, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in env.items()
    ):
        errors.append("envVars must be an object mapping string to string.")
        return
    populated = sorted(k for k, v in env.items() if v)
    if populated:
        errors.append(
            f"envVars in config.json has values for {', '.join(populated)}. This file "
            f"is uploaded and becomes part of the image layer, so those values would be "
            f"readable by anyone with source access — permanently, even after you "
            f"remove them. Set them with `tamarind ct config --env KEY=VALUE` instead, "
            f"and leave the values out of the file."
        )


def _check_max_runtime(data: dict, errors: list[str]) -> None:
    raw = data.get("maxRuntimeSeconds")
    if raw is None:
        return
    if not _is_int(raw):
        errors.append("maxRuntimeSeconds must be an integer number of seconds.")
        return
    value = int(raw)
    if not (MIN_RUNTIME_SECONDS <= value <= MAX_RUNTIME_SECONDS):
        errors.append(
            f"maxRuntimeSeconds must be between {MIN_RUNTIME_SECONDS} and "
            f"{MAX_RUNTIME_SECONDS} (24 hours), got {value}."
        )


def _check_inputs(inputs: list, errors: list[str]) -> None:
    """Only what is decidable locally: an input needs a name, and names are unique.

    The TYPE is not checked against a list. The server accepts types this client has
    never heard of by design, so a hardcoded enum here would reject a valid config
    the day the platform adds one.
    """
    seen: set[str] = set()
    for index, entry in enumerate(inputs):
        if not isinstance(entry, dict):
            errors.append(f"inputs[{index}] must be an object, not {type(entry).__name__}.")
            continue
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            errors.append(f"inputs[{index}] has no name.")
            continue
        if name in seen:
            errors.append(f"Duplicate input name {name!r}; the run form keys inputs by name.")
        seen.add(name)


def _check_msa(inputs: list, errors: list[str], facts: dict) -> None:
    """usesMsa: boolean, at most one, and only on a `sequence` input.

    All three mirror the server. The type rule is the surprising one — the flagged
    value is handed to the aligner as a protein query, so a `text` or `number` input
    would put arbitrary content in front of it.
    """
    flagged = [i for i in inputs if isinstance(i, dict) and i.get("usesMsa") is not None]
    for entry in flagged:
        # `isinstance`, not membership: `1 in (True, False)` is True in Python, so the
        # membership form accepted a JSON `1` — and the `is True` check below then read
        # that same value as DISABLED. A manifest this validator calls a boolean would
        # reach the server and silently not use MSA.
        if not isinstance(entry.get("usesMsa"), bool):
            errors.append(
                f"Input {entry.get('name')!r}: usesMsa must be a boolean "
                f'(got {entry.get("usesMsa")!r}; the string "false" is truthy).'
            )

    enabled = [i for i in flagged if i.get("usesMsa") is True]
    if not enabled:
        facts["usesMsa"] = False
        return
    if len(enabled) > 1:
        names = ", ".join(repr(i.get("name")) for i in enabled)
        errors.append(
            f"Only one input may set usesMsa; found {len(enabled)} ({names}). "
            f"The MSA stage aligns a single field."
        )
        facts["usesMsa"] = True
        return

    target = enabled[0]
    if target.get("type") != "sequence":
        errors.append(
            f"Input {target.get('name')!r}: usesMsa is only supported on an input of "
            f"type 'sequence' (this one is {target.get('type')!r})."
        )
    facts["usesMsa"] = True
    facts["msaInput"] = target.get("name")


def _check_batching(inputs: list, errors: list[str], facts: dict) -> None:
    """designBatching: a real boolean, number inputs only, at most one, count >= 1.

    The bool check is the same one `usesMsa` needed, for the same reason and one field
    over: truthiness reads `"false"` and `1` as ENABLED and `0` as absent. A number
    input with `designBatching: "false"` was reported as batching, while the same
    string without a count was rejected as if it had asked for it.
    """
    flagged = [i for i in inputs if isinstance(i, dict) and i.get("designBatching") is not None]
    for entry in flagged:
        if not isinstance(entry.get("designBatching"), bool):
            errors.append(
                f"Input {entry.get('name')!r}: designBatching must be a boolean "
                f"(got {entry.get('designBatching')!r})."
            )
    batching = [i for i in flagged if i.get("designBatching") is True]
    for entry in batching:
        if entry.get("type") != "number":
            errors.append(
                f"Input {entry.get('name')!r}: designBatching is only valid on a "
                f"number input; on any other type it saves but never fires."
            )
    if len(batching) > 1:
        names = ", ".join(repr(i.get("name")) for i in batching)
        errors.append(f"Only one input may enable design batching; found: {names}.")
    for entry in batching:
        per_batch = entry.get("designsPerBatch")
        if not isinstance(per_batch, (int, float)) or not _is_int(per_batch) or int(per_batch) < 1:
            errors.append(
                f"Input {entry.get('name')!r} enables design batching but has no "
                f"valid designsPerBatch (>= 1)."
            )
    if batching:
        facts["designBatching"] = batching[0].get("name")


def _check_outputs(outputs: list, errors: list[str]) -> None:
    """The primary-CSV rules — one primary, and it needs a path when it is ambiguous."""
    csvs = [o for o in outputs if isinstance(o, dict) and o.get("type") == "csv"]
    primary = [o for o in csvs if o.get("primary")]
    if len(primary) > 1:
        errors.append("Only one CSV output may be marked as the primary results table.")
    if len(csvs) > 1 and len(primary) == 1 and not primary[0].get("path"):
        errors.append(
            "The primary CSV must set a `path` when the tool declares more than one "
            "CSV output; without it the declaration matches every .csv."
        )


def parse_env_assignments(assignments: list[str]) -> dict[str, str]:
    """Turn ``["KEY=value", ...]`` into a mapping, or say precisely what is wrong.

    Splits on the FIRST ``=`` only, so a value containing one survives — which
    matters, because base64 and connection strings routinely do and silently
    truncating a credential produces a failure nobody traces back to here.

    An empty value is allowed: ``KEY=`` is a legitimate way to blank a variable.
    """
    parsed: dict[str, str] = {}
    for raw in assignments:
        key, sep, value = raw.partition("=")
        if not sep:
            raise ValidationError(
                f"--env expects KEY=VALUE, got {raw!r}. "
                f"(Quote the whole pair if your shell is splitting it.)"
            )
        key = key.strip()
        if not key:
            raise ValidationError(f"--env has an empty name in {raw!r}.")
        if not key.replace("_", "").isalnum():
            raise ValidationError(
                f"--env name {key!r} is not a valid environment variable name "
                f"(letters, digits and underscores)."
            )
        parsed[key] = value
    return parsed


def _is_int(value: Any) -> bool:
    """A JSON integer. Floats count when integer-valued (JSON has no int/float
    distinction); bool does not, even though it subclasses int."""
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    return isinstance(value, float) and value.is_integer()
