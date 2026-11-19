from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.assay_order_check_request_column_mapping_type_0 import (
        AssayOrderCheckRequestColumnMappingType0,
    )
    from ..models.assay_order_check_request_settings_type_0 import (
        AssayOrderCheckRequestSettingsType0,
    )


T = TypeVar("T", bound="AssayOrderCheckRequest")


@_attrs_define
class AssayOrderCheckRequest:
    """The body `validateAssay` takes: the fields of `AssayOrderRequest`, typed, without the rules between them (exactly
    one of `sequences` or `csvFile`, a `columnMapping` with `csvFile`, the shape of each sequence), which are part of
    its verdict.

        Attributes:
            assay_type (str):
            column_mapping (AssayOrderCheckRequestColumnMappingType0 | None | Unset):
            confirm_duplicate (bool | None | Unset):
            csv_file (None | str | Unset):
            modality (None | str | Unset):
            name (None | str | Unset):
            notes (None | str | Unset):
            sequences (list[Any] | None | Unset):
            settings (AssayOrderCheckRequestSettingsType0 | None | Unset):
    """

    assay_type: str
    column_mapping: AssayOrderCheckRequestColumnMappingType0 | None | Unset = UNSET
    confirm_duplicate: bool | None | Unset = UNSET
    csv_file: None | str | Unset = UNSET
    modality: None | str | Unset = UNSET
    name: None | str | Unset = UNSET
    notes: None | str | Unset = UNSET
    sequences: list[Any] | None | Unset = UNSET
    settings: AssayOrderCheckRequestSettingsType0 | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.assay_order_check_request_column_mapping_type_0 import (
            AssayOrderCheckRequestColumnMappingType0,
        )
        from ..models.assay_order_check_request_settings_type_0 import (
            AssayOrderCheckRequestSettingsType0,
        )

        assay_type = self.assay_type

        column_mapping: dict[str, Any] | None | Unset
        if isinstance(self.column_mapping, Unset):
            column_mapping = UNSET
        elif isinstance(self.column_mapping, AssayOrderCheckRequestColumnMappingType0):
            column_mapping = self.column_mapping.to_dict()
        else:
            column_mapping = self.column_mapping

        confirm_duplicate: bool | None | Unset
        if isinstance(self.confirm_duplicate, Unset):
            confirm_duplicate = UNSET
        else:
            confirm_duplicate = self.confirm_duplicate

        csv_file: None | str | Unset
        if isinstance(self.csv_file, Unset):
            csv_file = UNSET
        else:
            csv_file = self.csv_file

        modality: None | str | Unset
        if isinstance(self.modality, Unset):
            modality = UNSET
        else:
            modality = self.modality

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        notes: None | str | Unset
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        sequences: list[Any] | None | Unset
        if isinstance(self.sequences, Unset):
            sequences = UNSET
        elif isinstance(self.sequences, list):
            sequences = self.sequences

        else:
            sequences = self.sequences

        settings: dict[str, Any] | None | Unset
        if isinstance(self.settings, Unset):
            settings = UNSET
        elif isinstance(self.settings, AssayOrderCheckRequestSettingsType0):
            settings = self.settings.to_dict()
        else:
            settings = self.settings

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "assayType": assay_type,
            }
        )
        if column_mapping is not UNSET:
            field_dict["columnMapping"] = column_mapping
        if confirm_duplicate is not UNSET:
            field_dict["confirmDuplicate"] = confirm_duplicate
        if csv_file is not UNSET:
            field_dict["csvFile"] = csv_file
        if modality is not UNSET:
            field_dict["modality"] = modality
        if name is not UNSET:
            field_dict["name"] = name
        if notes is not UNSET:
            field_dict["notes"] = notes
        if sequences is not UNSET:
            field_dict["sequences"] = sequences
        if settings is not UNSET:
            field_dict["settings"] = settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.assay_order_check_request_column_mapping_type_0 import (
            AssayOrderCheckRequestColumnMappingType0,
        )
        from ..models.assay_order_check_request_settings_type_0 import (
            AssayOrderCheckRequestSettingsType0,
        )

        d = dict(src_dict)
        assay_type = d.pop("assayType")

        def _parse_column_mapping(
            data: object,
        ) -> AssayOrderCheckRequestColumnMappingType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                column_mapping_type_0 = AssayOrderCheckRequestColumnMappingType0.from_dict(data)

                return column_mapping_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AssayOrderCheckRequestColumnMappingType0 | None | Unset, data)

        column_mapping = _parse_column_mapping(d.pop("columnMapping", UNSET))

        def _parse_confirm_duplicate(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        confirm_duplicate = _parse_confirm_duplicate(d.pop("confirmDuplicate", UNSET))

        def _parse_csv_file(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        csv_file = _parse_csv_file(d.pop("csvFile", UNSET))

        def _parse_modality(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        modality = _parse_modality(d.pop("modality", UNSET))

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_notes(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        notes = _parse_notes(d.pop("notes", UNSET))

        def _parse_sequences(data: object) -> list[Any] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                sequences_type_0 = cast(list[Any], data)

                return sequences_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[Any] | None | Unset, data)

        sequences = _parse_sequences(d.pop("sequences", UNSET))

        def _parse_settings(data: object) -> AssayOrderCheckRequestSettingsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                settings_type_0 = AssayOrderCheckRequestSettingsType0.from_dict(data)

                return settings_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AssayOrderCheckRequestSettingsType0 | None | Unset, data)

        settings = _parse_settings(d.pop("settings", UNSET))

        assay_order_check_request = cls(
            assay_type=assay_type,
            column_mapping=column_mapping,
            confirm_duplicate=confirm_duplicate,
            csv_file=csv_file,
            modality=modality,
            name=name,
            notes=notes,
            sequences=sequences,
            settings=settings,
        )

        return assay_order_check_request
