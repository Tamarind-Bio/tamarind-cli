from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.molecule_fasta_mode import MoleculeFastaMode
from ..models.molecule_file_format import MoleculeFileFormat
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.molecule_import_request_chain_mapping_type_0 import (
        MoleculeImportRequestChainMappingType0,
    )
    from ..models.molecule_import_request_column_mapping_type_0 import (
        MoleculeImportRequestColumnMappingType0,
    )


T = TypeVar("T", bound="MoleculeImportRequest")


@_attrs_define
class MoleculeImportRequest:
    """The spec's `FileImportRequest`.

    Attributes:
        file_name (str):
        group_id (str):
        chain_mapping (MoleculeImportRequestChainMappingType0 | None | Unset):
        column_mapping (MoleculeImportRequestColumnMappingType0 | None | Unset):
        fasta_mode (MoleculeFastaMode | None | Unset):
        file_format (MoleculeFileFormat | Unset): The spec's `FileFormat` — a STRICT SUBSET of the internal
            `MoleculeFileFormat`, which also carries `cif`/`mmcif`. The public API does not
            document those, so they aren't accepted here; `auto` still detects anything the
            worker can read.
        size_bytes (int | None | Unset): CSV imports (including `fileFormat: auto` with a `.csv` filename) may be up to
            2 GiB. All other formats, including files left for content-based auto-detection, are limited to 16 MiB.
    """

    file_name: str
    group_id: str
    chain_mapping: MoleculeImportRequestChainMappingType0 | None | Unset = UNSET
    column_mapping: MoleculeImportRequestColumnMappingType0 | None | Unset = UNSET
    fasta_mode: MoleculeFastaMode | None | Unset = UNSET
    file_format: MoleculeFileFormat | Unset = UNSET
    size_bytes: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.molecule_import_request_chain_mapping_type_0 import (
            MoleculeImportRequestChainMappingType0,
        )
        from ..models.molecule_import_request_column_mapping_type_0 import (
            MoleculeImportRequestColumnMappingType0,
        )

        file_name = self.file_name

        group_id = self.group_id

        chain_mapping: dict[str, Any] | None | Unset
        if isinstance(self.chain_mapping, Unset):
            chain_mapping = UNSET
        elif isinstance(self.chain_mapping, MoleculeImportRequestChainMappingType0):
            chain_mapping = self.chain_mapping.to_dict()
        else:
            chain_mapping = self.chain_mapping

        column_mapping: dict[str, Any] | None | Unset
        if isinstance(self.column_mapping, Unset):
            column_mapping = UNSET
        elif isinstance(self.column_mapping, MoleculeImportRequestColumnMappingType0):
            column_mapping = self.column_mapping.to_dict()
        else:
            column_mapping = self.column_mapping

        fasta_mode: None | str | Unset
        if isinstance(self.fasta_mode, Unset):
            fasta_mode = UNSET
        elif isinstance(self.fasta_mode, MoleculeFastaMode):
            fasta_mode = self.fasta_mode.value
        else:
            fasta_mode = self.fasta_mode

        file_format: str | Unset = UNSET
        if not isinstance(self.file_format, Unset):
            file_format = self.file_format.value

        size_bytes: int | None | Unset
        if isinstance(self.size_bytes, Unset):
            size_bytes = UNSET
        else:
            size_bytes = self.size_bytes

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "fileName": file_name,
                "groupId": group_id,
            }
        )
        if chain_mapping is not UNSET:
            field_dict["chainMapping"] = chain_mapping
        if column_mapping is not UNSET:
            field_dict["columnMapping"] = column_mapping
        if fasta_mode is not UNSET:
            field_dict["fastaMode"] = fasta_mode
        if file_format is not UNSET:
            field_dict["fileFormat"] = file_format
        if size_bytes is not UNSET:
            field_dict["sizeBytes"] = size_bytes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.molecule_import_request_chain_mapping_type_0 import (
            MoleculeImportRequestChainMappingType0,
        )
        from ..models.molecule_import_request_column_mapping_type_0 import (
            MoleculeImportRequestColumnMappingType0,
        )

        d = dict(src_dict)
        file_name = d.pop("fileName")

        group_id = d.pop("groupId")

        def _parse_chain_mapping(
            data: object,
        ) -> MoleculeImportRequestChainMappingType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                chain_mapping_type_0 = MoleculeImportRequestChainMappingType0.from_dict(data)

                return chain_mapping_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MoleculeImportRequestChainMappingType0 | None | Unset, data)

        chain_mapping = _parse_chain_mapping(d.pop("chainMapping", UNSET))

        def _parse_column_mapping(
            data: object,
        ) -> MoleculeImportRequestColumnMappingType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                column_mapping_type_0 = MoleculeImportRequestColumnMappingType0.from_dict(data)

                return column_mapping_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MoleculeImportRequestColumnMappingType0 | None | Unset, data)

        column_mapping = _parse_column_mapping(d.pop("columnMapping", UNSET))

        def _parse_fasta_mode(data: object) -> MoleculeFastaMode | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                fasta_mode_type_0 = MoleculeFastaMode(data)

                return fasta_mode_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MoleculeFastaMode | None | Unset, data)

        fasta_mode = _parse_fasta_mode(d.pop("fastaMode", UNSET))

        _file_format = d.pop("fileFormat", UNSET)
        file_format: MoleculeFileFormat | Unset
        if isinstance(_file_format, Unset):
            file_format = UNSET
        else:
            file_format = MoleculeFileFormat(_file_format)

        def _parse_size_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        size_bytes = _parse_size_bytes(d.pop("sizeBytes", UNSET))

        molecule_import_request = cls(
            file_name=file_name,
            group_id=group_id,
            chain_mapping=chain_mapping,
            column_mapping=column_mapping,
            fasta_mode=fasta_mode,
            file_format=file_format,
            size_bytes=size_bytes,
        )

        return molecule_import_request
