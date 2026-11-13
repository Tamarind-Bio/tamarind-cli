"""SDK resources (client.jobs / client.tools / client.files) mirror the CLI and route
through the same rest/catalog/uploads layer. Library use → jobSource "sdk"."""

import json
from pathlib import Path

import httpx
import pytest
import respx

from tamarind import Tamarind, attribution

BASE = "https://api.test/"


@pytest.fixture(autouse=True)
def _sdk_channel():
    attribution.set_channel(attribution.CHANNEL_SDK)
    yield
    attribution.set_channel(attribution.CHANNEL_SDK)


def _client():
    return Tamarind(api_key="test-key", api_base=BASE)


@respx.mock
def test_jobs_submit_hits_submit_job_with_sdk_source():
    route = respx.post(f"{BASE}submit-job").mock(return_value=httpx.Response(200, json={"ok": True}))
    with _client() as c:
        c.jobs.submit("boltz", {"sequence": "ABC"}, name="run1")
    body = json.loads(route.calls.last.request.content)
    assert body == {"jobName": "run1", "type": "boltz", "settings": {"sequence": "ABC"}, "jobSource": "sdk"}


@respx.mock
def test_jobs_submit_batch_and_validate():
    sb = respx.post(f"{BASE}submit-batch").mock(return_value=httpx.Response(200, json={"ok": True}))
    vj = respx.post(f"{BASE}validate-job").mock(return_value=httpx.Response(200, json={"valid": True}))
    with _client() as c:
        c.jobs.submit_batch("boltz", [{"sequence": "A"}], name="b1", job_names=["b1-1"])
        c.jobs.validate("boltz", {"sequence": "A"})
    assert json.loads(sb.calls.last.request.content)["jobSource"] == "sdk"
    assert "jobSource" not in json.loads(vj.calls.last.request.content)  # validation creates no job


@respx.mock
def test_tools_list_and_schema():
    tools = respx.get(f"{BASE}catalog/tools").mock(return_value=httpx.Response(200, json={"tools": []}))
    schema = respx.get(f"{BASE}catalog/tools/boltz/schema").mock(return_value=httpx.Response(200, json={"schema": {}}))
    with _client() as c:
        c.tools.list(search="boltz")
        c.tools.schema("boltz")
    assert tools.called and schema.called
    assert "search=boltz" in str(tools.calls.last.request.url)


@respx.mock
def test_files_list_folders_delete():
    files = respx.get(f"{BASE}files").mock(return_value=httpx.Response(200, json={"files": []}))
    folders = respx.get(f"{BASE}getFolders").mock(return_value=httpx.Response(200, json={"folders": []}))
    delete = respx.request("DELETE", f"{BASE}delete-file").mock(return_value=httpx.Response(200, json={"ok": True}))
    with _client() as c:
        c.files.list()
        c.files.folders()
        c.files.delete(file_path="x.pdb")
    assert files.called and folders.called and delete.called


@respx.mock
def test_files_upload_presign_then_put(tmp_path: Path):
    p = tmp_path / "in.pdb"
    p.write_text("ATOM")
    presign = respx.post(f"{BASE}getPresignedUploadUrl").mock(
        return_value=httpx.Response(200, json={"uploadUrl": "https://s3.test/put", "key": "k", "bucket": "b"})
    )
    put = respx.put("https://s3.test/put").mock(return_value=httpx.Response(200))
    with _client() as c:
        result = c.files.upload(p, remote="in.pdb")
    assert presign.called and put.called
    assert result == {"ok": True, "filename": "in.pdb", "bytes": 4}
