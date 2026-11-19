from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.batch_source_format import BatchSourceFormat
from ..models.batch_source_rank_order import BatchSourceRankOrder
from ..types import UNSET, Unset

T = TypeVar("T", bound="BatchSource")


@_attrs_define
class BatchSource:
    """Read the batch's rows from one of your files, at submit. Replaces the MCP-only `fromFile` handling. A problem with
    the file itself is 422 at the member at fault, such as `/source/file` or `/source/sequenceColumn`; the rows'
    settings are checked after the 202, like an inline batch's.

        Attributes:
            file (str): A workspace `path`, a path in one of your job folders, or a `tamarind://jobs/job_<id>/<path>`
                reference to a job's file. At most 64 MiB of UTF-8 text and 30,000 rows (after `topN`); a file that is missing,
                too large, empty or malformed is 422 at `/source/file`. A file batch's row pointers (`/settings/<n>`) count the
                file's rows from 0.
            format_ (BatchSourceFormat | Unset): `auto` picks by the file's extension (`.fasta`, `.fa`, `.faa`, `.fna`,
                `.csv`, `.jsonl`, `.ndjson`), and any other is 422 `required` at `/source/format`. FASTA is one row per record.
                CSV is one row per line under a header row; a line with more cells than the header is 422 `invalid_format` at
                `/source/file`. JSONL is one JSON object of settings per line. Default: BatchSourceFormat.AUTO.
            name_column (str | Unset): CSV only: the column holding each job's name. A value that isn't a job name, or a
                name repeated or equal to the batch's `name`, is 422 at `/source/nameColumn`, naming the row.
            rank_by (str | Unset): CSV only: a numeric column to order the rows by before `topN`. Rows with no number in it
                go last, in file order.
            rank_order (BatchSourceRankOrder | Unset): With `rankBy` only. Without it, `rankBy` ranks highest first.
            sequence_column (str | Unset): CSV only: the column holding the sequence. Each row then carries only that value.
                Without it, every column but `nameColumn` is a setting of the same name. CSV values are text; send typed values
                as JSONL.
            sequence_field (str | Unset): The setting each row's sequence goes into, for FASTA, and for CSV with
                `sequenceColumn`. Defaults to `sequence`.
            top_n (int | Unset): Keep only the first N rows, after ranking.
    """

    file: str
    format_: BatchSourceFormat | Unset = BatchSourceFormat.AUTO
    name_column: str | Unset = UNSET
    rank_by: str | Unset = UNSET
    rank_order: BatchSourceRankOrder | Unset = UNSET
    sequence_column: str | Unset = UNSET
    sequence_field: str | Unset = UNSET
    top_n: int | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        file = self.file

        format_: str | Unset = UNSET
        if not isinstance(self.format_, Unset):
            format_ = self.format_.value

        name_column = self.name_column

        rank_by = self.rank_by

        rank_order: str | Unset = UNSET
        if not isinstance(self.rank_order, Unset):
            rank_order = self.rank_order.value

        sequence_column = self.sequence_column

        sequence_field = self.sequence_field

        top_n = self.top_n

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "file": file,
            }
        )
        if format_ is not UNSET:
            field_dict["format"] = format_
        if name_column is not UNSET:
            field_dict["nameColumn"] = name_column
        if rank_by is not UNSET:
            field_dict["rankBy"] = rank_by
        if rank_order is not UNSET:
            field_dict["rankOrder"] = rank_order
        if sequence_column is not UNSET:
            field_dict["sequenceColumn"] = sequence_column
        if sequence_field is not UNSET:
            field_dict["sequenceField"] = sequence_field
        if top_n is not UNSET:
            field_dict["topN"] = top_n

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file = d.pop("file")

        _format_ = d.pop("format", UNSET)
        format_: BatchSourceFormat | Unset
        if isinstance(_format_, Unset):
            format_ = UNSET
        else:
            format_ = BatchSourceFormat(_format_)

        name_column = d.pop("nameColumn", UNSET)

        rank_by = d.pop("rankBy", UNSET)

        _rank_order = d.pop("rankOrder", UNSET)
        rank_order: BatchSourceRankOrder | Unset
        if isinstance(_rank_order, Unset):
            rank_order = UNSET
        else:
            rank_order = BatchSourceRankOrder(_rank_order)

        sequence_column = d.pop("sequenceColumn", UNSET)

        sequence_field = d.pop("sequenceField", UNSET)

        top_n = d.pop("topN", UNSET)

        batch_source = cls(
            file=file,
            format_=format_,
            name_column=name_column,
            rank_by=rank_by,
            rank_order=rank_order,
            sequence_column=sequence_column,
            sequence_field=sequence_field,
            top_n=top_n,
        )

        return batch_source
