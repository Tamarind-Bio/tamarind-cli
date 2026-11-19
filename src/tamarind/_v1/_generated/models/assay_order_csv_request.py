from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.assay_order_csv_request_modality_type_1 import AssayOrderCsvRequestModalityType1
from ..models.assay_order_csv_request_modality_type_2_type_1 import (
    AssayOrderCsvRequestModalityType2Type1,
)
from ..models.assay_order_csv_request_modality_type_3_type_1 import (
    AssayOrderCsvRequestModalityType3Type1,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.assay_order_csv_request_settings_type_0 import AssayOrderCsvRequestSettingsType0


T = TypeVar("T", bound="AssayOrderCsvRequest")


@_attrs_define
class AssayOrderCsvRequest:
    """
    Attributes:
        assay_type (str): Which assay to run. The options come from GET /assay-types. Example: adaptyv_affinity.
        column_mapping (Any): Which CSV columns hold what. Needed with `csvFile`. For antibodies, map `heavy`, and
            optionally `name` and `light`. For proteins, map `sequence`, and optionally `name`.
        csv_file (str): A CSV file of sequences, to use instead of `sequences`. Upload it first with `POST /files`, then
            give its path within your files. It is a relative `.csv` path of at most 512 characters, with no `..`, and the
            file can be up to 10 MB. The order checks enforce these. Example: designs/round2.csv.
        confirm_duplicate (bool | None | Unset): Set to true to place an order that looks like one you placed recently.
            Use it after a `duplicate_order` response, when you do want a second, separately billed order. Only
            `submitAssay` reads it. Default: False.
        modality (AssayOrderCsvRequestModalityType1 | AssayOrderCsvRequestModalityType2Type1 |
            AssayOrderCsvRequestModalityType3Type1 | None | Unset): Whether your sequences are antibodies or proteins. You
            can leave it out when the assay type only supports one.
        name (None | str | Unset): A name for the order so you can find it later. At most 200 characters once trimmed;
            the order checks enforce it, so a longer one is a validation problem, not a schema refusal.
        notes (None | str | Unset): Anything the Tamarind team should know when reviewing the order. At most 2,000
            characters, enforced by the order checks.
        settings (AssayOrderCsvRequestSettingsType0 | None | Unset): Options for this assay, such as the target. The
            assay type's `settings` list says what is needed. Example: {'antigenConcentrations': [1, 10, 100], 'method':
            'BLI', 'targetId': '<id from /assay-targets>'}.
    """

    assay_type: str
    column_mapping: Any
    csv_file: str
    confirm_duplicate: bool | None | Unset = False
    modality: (
        AssayOrderCsvRequestModalityType1
        | AssayOrderCsvRequestModalityType2Type1
        | AssayOrderCsvRequestModalityType3Type1
        | None
        | Unset
    ) = UNSET
    name: None | str | Unset = UNSET
    notes: None | str | Unset = UNSET
    settings: AssayOrderCsvRequestSettingsType0 | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.assay_order_csv_request_settings_type_0 import (
            AssayOrderCsvRequestSettingsType0,
        )

        assay_type = self.assay_type

        column_mapping: Any
        column_mapping = self.column_mapping

        csv_file = self.csv_file

        confirm_duplicate: bool | None | Unset
        if isinstance(self.confirm_duplicate, Unset):
            confirm_duplicate = UNSET
        else:
            confirm_duplicate = self.confirm_duplicate

        modality: None | str | Unset
        if isinstance(self.modality, Unset):
            modality = UNSET
        elif isinstance(self.modality, AssayOrderCsvRequestModalityType1):
            modality = self.modality.value
        elif isinstance(self.modality, AssayOrderCsvRequestModalityType2Type1):
            modality = self.modality.value
        elif isinstance(self.modality, AssayOrderCsvRequestModalityType3Type1):
            modality = self.modality.value
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

        settings: dict[str, Any] | None | Unset
        if isinstance(self.settings, Unset):
            settings = UNSET
        elif isinstance(self.settings, AssayOrderCsvRequestSettingsType0):
            settings = self.settings.to_dict()
        else:
            settings = self.settings

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "assayType": assay_type,
                "columnMapping": column_mapping,
                "csvFile": csv_file,
            }
        )
        if confirm_duplicate is not UNSET:
            field_dict["confirmDuplicate"] = confirm_duplicate
        if modality is not UNSET:
            field_dict["modality"] = modality
        if name is not UNSET:
            field_dict["name"] = name
        if notes is not UNSET:
            field_dict["notes"] = notes
        if settings is not UNSET:
            field_dict["settings"] = settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.assay_order_csv_request_settings_type_0 import (
            AssayOrderCsvRequestSettingsType0,
        )

        d = dict(src_dict)
        assay_type = d.pop("assayType")

        def _parse_column_mapping(data: object) -> Any:
            return cast(Any, data)

        column_mapping = _parse_column_mapping(d.pop("columnMapping"))

        csv_file = d.pop("csvFile")

        def _parse_confirm_duplicate(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        confirm_duplicate = _parse_confirm_duplicate(d.pop("confirmDuplicate", UNSET))

        def _parse_modality(
            data: object,
        ) -> (
            AssayOrderCsvRequestModalityType1
            | AssayOrderCsvRequestModalityType2Type1
            | AssayOrderCsvRequestModalityType3Type1
            | None
            | Unset
        ):
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                modality_type_1 = AssayOrderCsvRequestModalityType1(data)

                return modality_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, str):
                    raise TypeError()
                modality_type_2_type_1 = AssayOrderCsvRequestModalityType2Type1(data)

                return modality_type_2_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, str):
                    raise TypeError()
                modality_type_3_type_1 = AssayOrderCsvRequestModalityType3Type1(data)

                return modality_type_3_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                AssayOrderCsvRequestModalityType1
                | AssayOrderCsvRequestModalityType2Type1
                | AssayOrderCsvRequestModalityType3Type1
                | None
                | Unset,
                data,
            )

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

        def _parse_settings(data: object) -> AssayOrderCsvRequestSettingsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                settings_type_0 = AssayOrderCsvRequestSettingsType0.from_dict(data)

                return settings_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AssayOrderCsvRequestSettingsType0 | None | Unset, data)

        settings = _parse_settings(d.pop("settings", UNSET))

        assay_order_csv_request = cls(
            assay_type=assay_type,
            column_mapping=column_mapping,
            csv_file=csv_file,
            confirm_duplicate=confirm_duplicate,
            modality=modality,
            name=name,
            notes=notes,
            settings=settings,
        )

        return assay_order_csv_request
