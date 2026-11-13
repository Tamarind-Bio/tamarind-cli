"""`tamarind batch --prevalidate` sends ONE validate request per chunk, not per job.

The per-job loop this replaced is the traffic shape that got a customer blocked at
the network edge: 10,000 jobs meant 10,000 POSTs from one address. Every row is
still validated — these tests pin that, and that a row's index survives chunking,
because an index that shifts sends the user to fix the wrong payload.
"""

import json

import httpx
import respx
from typer.testing import CliRunner

from tamarind import rest
from tamarind.cli.main import app
from tamarind.cli.commands import jobs as jobs_commands
from tamarind.errors import ValidationError

API = "https://app.tamarind.bio/api/"
ENV = {"TAMARIND_API_KEY": "k", "NO_COLOR": "1"}
runner = CliRunner()


def _batch_file(tmp_path, n):
    path = tmp_path / "batch.yaml"
    path.write_text("".join(f"- {{sequence: MK{i}}}\n" for i in range(n)))
    return path


def _run(tmp_path, n):
    return runner.invoke(
        app,
        ["--json", "batch", "boltz", "--name", "b", "--input",
         str(_batch_file(tmp_path, n)), "--prevalidate"],
        env=ENV,
    )


def _all_valid(offset, count):
    return {
        "valid": True, "count": count, "valid_count": count,
        "results": [{"index": i, "valid": True} for i in range(count)],
    }


# --- the chunker, on its own -------------------------------------------------

def test_chunks_respect_the_row_cap(monkeypatch):
    monkeypatch.setattr(rest, "VALIDATE_BATCH_MAX_ROWS", 3)
    chunks = jobs_commands._chunk_for_validate([{"s": i} for i in range(7)])
    assert [(off, len(rows)) for off, rows in chunks] == [(0, 3), (3, 3), (6, 1)]
    # Offsets must reconstruct the original list exactly, in order.
    assert [r for _, rows in chunks for r in rows] == [{"s": i} for i in range(7)]


def test_chunks_shrink_on_BYTES_even_under_the_row_cap(monkeypatch):
    """The row cap is not the only bound — over ~4.5 MB the platform answers a bare
    413 ahead of the endpoint, so there is no JSON body to report."""
    monkeypatch.setattr(rest, "VALIDATE_BATCH_MAX_ROWS", 1000)
    monkeypatch.setattr(rest, "VALIDATE_BATCH_MAX_BYTES", 500)
    rows = [{"sequence": "A" * 200} for _ in range(8)]
    chunks = jobs_commands._chunk_for_validate(rows)
    assert len(chunks) > 1, "a large payload must split below the row cap"
    assert sum(len(r) for _, r in chunks) == 8
    assert [off for off, _ in chunks] == sorted(off for off, _ in chunks)


def test_a_single_oversized_row_is_still_emitted(monkeypatch):
    """Never drop a row we cannot shrink — send it and let the server answer."""
    monkeypatch.setattr(rest, "VALIDATE_BATCH_MAX_BYTES", 10)
    chunks = jobs_commands._chunk_for_validate([{"sequence": "A" * 5000}])
    assert len(chunks) == 1 and len(chunks[0][1]) == 1


# --- end to end --------------------------------------------------------------

@respx.mock
def test_many_jobs_cost_few_requests(tmp_path, monkeypatch):
    monkeypatch.setattr(rest, "VALIDATE_BATCH_MAX_ROWS", 2)
    validation = respx.post(f"{API}validate-job").mock(
        side_effect=[
            httpx.Response(200, json=_all_valid(0, 2)),
            httpx.Response(200, json=_all_valid(2, 2)),
            httpx.Response(200, json=_all_valid(4, 1)),
        ]
    )
    submit = respx.post(f"{API}submit-batch").mock(
        return_value=httpx.Response(200, json={"message": "queued"})
    )

    result = _run(tmp_path, 5)
    assert result.exit_code == 0, result.stdout
    assert validation.call_count == 3, "5 jobs at 2 rows/call is 3 requests, not 5"
    assert submit.call_count == 1
    # Every row went up exactly once, in order.
    sent = [r for c in validation.calls for r in json.loads(c.request.content)["settings"]]
    assert sent == [{"sequence": f"MK{i}"} for i in range(5)]


@respx.mock
def test_a_bad_row_in_a_LATER_chunk_keeps_its_original_index(tmp_path, monkeypatch):
    """The row is 4th overall but 2nd in its chunk. Reporting the chunk-local index
    would send the user to fix a payload that is fine."""
    monkeypatch.setattr(rest, "VALIDATE_BATCH_MAX_ROWS", 2)
    respx.post(f"{API}validate-job").mock(
        side_effect=[
            httpx.Response(200, json=_all_valid(0, 2)),
            httpx.Response(200, json={
                "valid": False, "count": 2, "valid_count": 1,
                "results": [
                    {"index": 0, "valid": True},
                    {"index": 1, "valid": False, "error": "bad sequence"},
                ],
            }),
        ]
    )
    submit = respx.post(f"{API}submit-batch").mock(
        return_value=httpx.Response(200, json={"message": "should not happen"})
    )

    result = runner.invoke(
        app,
        ["batch", "boltz", "--name", "b", "--input",
         str(_batch_file(tmp_path, 5)), "--prevalidate"],
        env=ENV,
    )
    assert result.exit_code != 0
    assert isinstance(result.exception, ValidationError)
    assert result.exception.detail["index"] == 3
    assert result.exception.detail["jobName"] == "b-4"
    assert "Batch item 4" in str(result.exception)
    assert not submit.called


@respx.mock
def test_the_FIRST_bad_row_is_reported_when_several_fail(tmp_path):
    respx.post(f"{API}validate-job").mock(
        return_value=httpx.Response(200, json={
            "valid": False, "count": 3, "valid_count": 1,
            "results": [
                {"index": 0, "valid": True},
                {"index": 1, "valid": False, "error": "first problem"},
                {"index": 2, "valid": False, "error": "second problem"},
            ],
        })
    )
    respx.post(f"{API}submit-batch").mock(return_value=httpx.Response(200, json={}))

    result = runner.invoke(
        app,
        ["batch", "boltz", "--name", "b", "--input",
         str(_batch_file(tmp_path, 3)), "--prevalidate"],
        env=ENV,
    )
    assert result.exception.detail["index"] == 1
    assert "first problem" in str(result.exception)


@respx.mock
def test_a_batch_WIDE_refusal_is_not_blamed_on_row_one(tmp_path):
    """Out of quota / over a cap answers valid:false with NO `results`. Branching on
    `valid` instead of on `results` would report it as 'Batch item 1 invalid'."""
    respx.post(f"{API}validate-job").mock(
        return_value=httpx.Response(200, json={
            "valid": False,
            "error": "You have reached your monthly job limit.",
        })
    )
    submit = respx.post(f"{API}submit-batch").mock(
        return_value=httpx.Response(200, json={"message": "should not happen"})
    )

    result = runner.invoke(
        app,
        ["batch", "boltz", "--name", "b", "--input",
         str(_batch_file(tmp_path, 2)), "--prevalidate"],
        env=ENV,
    )
    assert result.exit_code != 0
    assert isinstance(result.exception, ValidationError)
    message = str(result.exception)
    assert "monthly job limit" in message
    assert "Batch item" not in message
    assert "index" not in result.exception.detail
    assert not submit.called


def test_chunks_take_the_LARGEST_prefix_that_fits(monkeypatch):
    """Halving overshoots: with 10 uniform rows where 6 fit, it settles for 5 and buys an
    extra request. `_prevalidate_batch` promises as few requests as possible."""
    monkeypatch.setattr(rest, "VALIDATE_BATCH_MAX_ROWS", 1000)
    rows = [{"s": "A" * 100} for _ in range(10)]
    six = len(json.dumps({"type": "t", "settings": rows[:6]}).encode())
    seven = len(json.dumps({"type": "t", "settings": rows[:7]}).encode())
    monkeypatch.setattr(rest, "VALIDATE_BATCH_MAX_BYTES", (six + seven) // 2)
    chunks = jobs_commands._chunk_for_validate(rows, job_type="t")
    assert [len(r) for _, r in chunks] == [6, 4]


def test_the_byte_budget_counts_jobNames_and_type(monkeypatch):
    """`validate_jobs` sends an envelope, not bare rows. A budget measuring only the rows
    is not the budget the edge applies, and the gap grows with one name per row."""
    monkeypatch.setattr(rest, "VALIDATE_BATCH_MAX_ROWS", 1000)
    rows = [{"s": "A" * 50} for _ in range(6)]
    names = ["N" * 200 for _ in range(6)]
    monkeypatch.setattr(
        rest, "VALIDATE_BATCH_MAX_BYTES",
        len(json.dumps({"type": "t", "settings": rows}).encode()) + 20,
    )
    assert len(jobs_commands._chunk_for_validate(rows, job_type="t")) == 1
    assert len(jobs_commands._chunk_for_validate(rows, job_type="t", names=names)) > 1


@respx.mock
def test_a_SHORT_results_list_refuses_instead_of_submitting(tmp_path):
    """A verdict per row is the contract. Two rows answered for three means one was never
    judged, and "no invalid rows" would be a false pass on it."""
    respx.post(f"{API}validate-job").mock(
        return_value=httpx.Response(200, json={
            "valid": True, "count": 3, "valid_count": 2,
            "results": [{"index": 0, "valid": True}, {"index": 1, "valid": True}],
        })
    )
    submit = respx.post(f"{API}submit-batch").mock(
        return_value=httpx.Response(200, json={"message": "should not happen"})
    )
    result = runner.invoke(
        app,
        ["batch", "boltz", "--name", "b", "--input",
         str(_batch_file(tmp_path, 3)), "--prevalidate"],
        env=ENV,
    )
    assert result.exit_code != 0
    assert isinstance(result.exception, ValidationError)
    assert "2 of 3 rows" in str(result.exception)
    assert not submit.called


@respx.mock
def test_verdicts_with_no_usable_index_do_not_count_as_judged(tmp_path):
    """A malformed entry is not a verdict. Counting it would let a row through unchecked."""
    respx.post(f"{API}validate-job").mock(
        return_value=httpx.Response(200, json={
            "valid": True, "count": 2, "valid_count": 2,
            "results": [{"index": 0, "valid": True}, {"valid": True}],
        })
    )
    submit = respx.post(f"{API}submit-batch").mock(
        return_value=httpx.Response(200, json={"message": "should not happen"})
    )
    result = runner.invoke(
        app,
        ["batch", "boltz", "--name", "b", "--input",
         str(_batch_file(tmp_path, 2)), "--prevalidate"],
        env=ENV,
    )
    assert result.exit_code != 0 and not submit.called


def test_the_prevalidate_help_does_not_claim_a_request_per_item():
    """It used to say "one API request per item" — the behaviour this PR removed.

    Read off the DECLARED option, not rendered `--help` output. Rendering goes through Rich,
    which wraps at the terminal width and injects ANSI codes, so on an 80-column CI runner
    `--prevalidate` is not even a contiguous string — this passed locally and failed on every
    runner in the matrix. The declared text is what the help is built from, and does not
    depend on the terminal it is shown in.
    """
    import typer.main

    batch = typer.main.get_command(app).commands["batch"]
    option = next(p for p in batch.params if "--prevalidate" in getattr(p, "opts", []))
    assert option.help, "--prevalidate should document itself"
    assert "per item" not in option.help
