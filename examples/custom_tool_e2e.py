#!/usr/bin/env python3
"""End-to-end custom-tool deploy, driven from Python.

    check -> build -> smoke-test at the pinned version -> publish

Exits non-zero on failure, so CI or an agent can tell pass from fail without
parsing output. This is the same sequence `tamarind deploy && tamarind publish`
runs; the library is here for when you want to make a decision in between — as
this script does, refusing to publish a version whose smoke test did not pass.

Run it with:

    TAMARIND_API_KEY=... python examples/custom_tool_e2e.py ./my-esmfold

Three things in here are load-bearing and easy to get wrong by hand:

* **`outcome.confirmed_version()`, never `outcome.version_name`.** `deployed` says
  the server acted; it does NOT say the server acted on YOUR source. When extraction
  outruns the deploy, `build()` deliberately returns `deployed=True` with
  `confirmed=False` — publishing that promotes a version built from the previous
  tree. `confirmed_version()` returns None in exactly the cases where publishing
  would be wrong, and `publish_confirmed()` is the only thing that accepts its
  result. Checking `deployed` alone is the bug this script used to contain.

* **Pin the smoke test to the version's REF, not its name.** `v1` is a display
  name; the pinned submit endpoint pins by commit ref, so `toolRef` must carry
  `version.ref`. Sending the name either fails or silently exercises the wrong tree.

* **Publish last.** Publishing is what makes a version live for the whole org.
"""

from __future__ import annotations

import sys
from pathlib import Path

from tamarind import customtools as ct
from tamarind import jobs
from tamarind.config import load_config
from tamarind.errors import NotFoundError, TamarindError
from tamarind.http import HTTPClient

SMOKE_TEST_SETTINGS = {"sequence": "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQ"}
SMOKE_TEST_TIMEOUT = 900.0


def deploy(folder: Path) -> int:
    cfg = load_config()
    if not cfg.api_key:
        print("Set TAMARIND_API_KEY, or run `tamarind auth login`.", file=sys.stderr)
        return 1

    # The folder records which tool it belongs to (.tamarind), so a renamed or
    # freshly-cloned directory still deploys to the right place.
    name = ct.project.resolve_name(folder)

    # 1. Local checks. Instant, and they cost nothing compared to a failed build.
    findings = ct.inspect_manifest(folder)
    for warning in findings.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if findings.errors:
        for error in findings.errors:
            print(f"config.json: {error}", file=sys.stderr)
        return 1

    with HTTPClient(cfg.api_base, cfg.api_key) as client:
        try:
            ct.get_tool(client, name=name)
        except NotFoundError:
            print(f"creating {name}")
            ct.create_tool(client, name=name)

        # 2. Package, upload, deploy, and stream the build.
        outcome = ct.build(
            client,
            name=name,
            folder=folder,
            on_event=lambda e: print(f"[{e.phase}] {e.message}"),
        )
        print(f"{outcome.version_name or '(no version)'}: {outcome.explanation}")

        if not outcome.deployed:
            # Not a failure. The common case is an unchanged re-deploy in CI, where
            # the live version is already correct and there is nothing to test.
            return 0

        # 3. The evidence, not the name. None here means publishing would be unsafe —
        #    nothing deployed, the server named no version, or the extraction was never
        #    confirmed so this build may have used the PREVIOUS source.
        confirmed = outcome.confirmed_version()
        if confirmed is None:
            print(f"not publishable: {outcome.explanation}", file=sys.stderr)
            return 1

        # 4. Smoke-test THAT version. The endpoint pins by commit ref, so resolve the
        #    named version to its ref — sending the display name pins nothing.
        version = ct.plan.find_version(ct.get_versions(client, name=name), confirmed.name)
        if version is None or not version.ref:
            print(f"{confirmed.name} records no source ref to pin to.", file=sys.stderr)
            return 1
        job_name = f"{name}-smoke-{confirmed.name}"
        print(f"submitting {job_name} against {name}@{version.ref[:10]}")
        jobs.submit_job_pinned(
            client,
            job_name=job_name,
            job_type=name,
            settings=SMOKE_TEST_SETTINGS,
            tool_ref=version.ref,
        )
        final = jobs.wait_for_job(client, job_name, timeout=SMOKE_TEST_TIMEOUT)
        status = jobs.job_status(final)
        if not jobs.is_success(status):
            print(f"smoke test finished {status} — not publishing.", file=sys.stderr)
            return 1

        # 5. Only now make it live for everyone. `publish_confirmed` takes the
        #    evidence rather than a name, so this line cannot promote a stale build.
        _, published = ct.publish_confirmed(client, name=name, version=confirmed)
        print(f"published {name} version {published}")
        return 0


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    try:
        raise SystemExit(deploy(target))
    except TamarindError as exc:
        # Every library error carries a stable exit code, so a caller can branch on
        # the KIND of failure without matching on the message text.
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(exc.exit_code) from exc
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        raise SystemExit(130) from None
