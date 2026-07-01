"""Unit tests for the client-side workspace-file filtering that `files list`
applies (the /files endpoint ignores query filters, so the CLI mirrors the MCP
getFiles tool locally)."""

from tamarind.cli.commands.files import _apply_file_filters, _file_name, _file_type_counts


def test_file_name_variants():
    assert _file_name("x.pdb") == "x.pdb"
    assert _file_name({"name": "y.pdb"}) == "y.pdb"
    assert _file_name({"key": "z.pdb"}) == "z.pdb"
    assert _file_name(123) == "123"


def test_no_filters_returns_everything():
    files = ["a.pdb", "b.cif", "c.txt"]
    r = _apply_file_filters(files)
    assert r["files"] == files
    assert r["total"] == 3 and r["totalUnfiltered"] == 3 and r["hasMore"] is False


def test_types_is_case_insensitive_and_tolerates_leading_dot():
    files = ["a.pdb", "b.PDB", "c.cif", "d.txt", "seqs.fasta"]
    r = _apply_file_filters(files, types=".pdb,cif")
    assert set(r["files"]) == {"a.pdb", "b.PDB", "c.cif"}
    assert r["total"] == 3 and r["totalUnfiltered"] == 5


def test_types_does_not_substring_match():
    # "pdb" must match the EXTENSION, not appear anywhere in the name.
    files = ["pdb_notes.txt", "model.pdb"]
    r = _apply_file_filters(files, types="pdb")
    assert r["files"] == ["model.pdb"]


def test_search_is_substring_case_insensitive():
    files = ["seqs.fasta", "SEQUENCES.txt", "model.pdb"]
    r = _apply_file_filters(files, search="seq")
    assert set(r["files"]) == {"seqs.fasta", "SEQUENCES.txt"}


def test_pagination_offset_limit_and_hasmore():
    files = [f"f{i}.pdb" for i in range(10)]
    r = _apply_file_filters(files, limit=3, offset=0)
    assert r["files"] == ["f0.pdb", "f1.pdb", "f2.pdb"]
    assert r["count"] == 3 and r["total"] == 10 and r["hasMore"] is True
    last = _apply_file_filters(files, limit=3, offset=9)
    assert last["files"] == ["f9.pdb"] and last["hasMore"] is False


def test_filters_then_paginates():
    files = ["a.pdb", "x.txt", "b.pdb", "y.txt", "c.pdb"]
    r = _apply_file_filters(files, types="pdb", limit=2, offset=0)
    assert r["files"] == ["a.pdb", "b.pdb"]
    assert r["total"] == 3 and r["hasMore"] is True  # 3 pdbs, showing 2


def test_file_type_counts():
    counts = _file_type_counts(["a.PDB", "b.pdb", "c.cif", "no_ext_file"])
    assert counts == {"pdb": 2, "cif": 1, "no_extension": 1}  # case-insensitive; ext-less bucketed


def test_file_type_counts_empty():
    assert _file_type_counts([]) == {}
