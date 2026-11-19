from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.assay_order_inline_request_modality_type_1 import AssayOrderInlineRequestModalityType1
from ..models.assay_order_inline_request_modality_type_2_type_1 import (
    AssayOrderInlineRequestModalityType2Type1,
)
from ..models.assay_order_inline_request_modality_type_3_type_1 import (
    AssayOrderInlineRequestModalityType3Type1,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.antibody_sequence import AntibodySequence
    from ..models.assay_order_inline_request_settings_type_0 import (
        AssayOrderInlineRequestSettingsType0,
    )
    from ..models.protein_sequence import ProteinSequence


T = TypeVar("T", bound="AssayOrderInlineRequest")


@_attrs_define
class AssayOrderInlineRequest:
    """
    Attributes:
        assay_type (str): Which assay to run. The options come from GET /assay-types. Example: adaptyv_affinity.
        sequences (list[AntibodySequence | ProteinSequence | str]): The sequences to test. At most 5,000, enforced by
            the order checks. For antibodies, send "HEAVY:LIGHT" strings (or just "HEAVY"), or objects with `name`, `heavy`
            and `light`. For proteins, send the sequence as a string (join chains with ":"), or objects with `name` and
            `sequence`. A sequence you don't name is called seq_1, seq_2 and so on. Every name and every sequence has to be
            different.
        confirm_duplicate (bool | None | Unset): Set to true to place an order that looks like one you placed recently.
            Use it after a `duplicate_order` response, when you do want a second, separately billed order. Only
            `submitAssay` reads it. Default: False.
        modality (AssayOrderInlineRequestModalityType1 | AssayOrderInlineRequestModalityType2Type1 |
            AssayOrderInlineRequestModalityType3Type1 | None | Unset): Whether your sequences are antibodies or proteins.
            You can leave it out when the assay type only supports one.
        name (None | str | Unset): A name for the order so you can find it later. At most 200 characters once trimmed;
            the order checks enforce it, so a longer one is a validation problem, not a schema refusal.
        notes (None | str | Unset): Anything the Tamarind team should know when reviewing the order. At most 2,000
            characters, enforced by the order checks.
        settings (AssayOrderInlineRequestSettingsType0 | None | Unset): Options for this assay, such as the target. The
            assay type's `settings` list says what is needed. Example: {'antigenConcentrations': [1, 10, 100], 'method':
            'BLI', 'targetId': '<id from /assay-targets>'}.
    """

    assay_type: str
    sequences: list[AntibodySequence | ProteinSequence | str]
    confirm_duplicate: bool | None | Unset = False
    modality: (
        AssayOrderInlineRequestModalityType1
        | AssayOrderInlineRequestModalityType2Type1
        | AssayOrderInlineRequestModalityType3Type1
        | None
        | Unset
    ) = UNSET
    name: None | str | Unset = UNSET
    notes: None | str | Unset = UNSET
    settings: AssayOrderInlineRequestSettingsType0 | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.antibody_sequence import AntibodySequence
        from ..models.assay_order_inline_request_settings_type_0 import (
            AssayOrderInlineRequestSettingsType0,
        )
        from ..models.protein_sequence import ProteinSequence

        assay_type = self.assay_type

        sequences = []
        for sequences_item_data in self.sequences:
            sequences_item: dict[str, Any] | str
            if isinstance(sequences_item_data, AntibodySequence):
                sequences_item = sequences_item_data.to_dict()
            elif isinstance(sequences_item_data, ProteinSequence):
                sequences_item = sequences_item_data.to_dict()
            else:
                sequences_item = sequences_item_data
            sequences.append(sequences_item)

        confirm_duplicate: bool | None | Unset
        if isinstance(self.confirm_duplicate, Unset):
            confirm_duplicate = UNSET
        else:
            confirm_duplicate = self.confirm_duplicate

        modality: None | str | Unset
        if isinstance(self.modality, Unset):
            modality = UNSET
        elif isinstance(self.modality, AssayOrderInlineRequestModalityType1):
            modality = self.modality.value
        elif isinstance(self.modality, AssayOrderInlineRequestModalityType2Type1):
            modality = self.modality.value
        elif isinstance(self.modality, AssayOrderInlineRequestModalityType3Type1):
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
        elif isinstance(self.settings, AssayOrderInlineRequestSettingsType0):
            settings = self.settings.to_dict()
        else:
            settings = self.settings

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "assayType": assay_type,
                "sequences": sequences,
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
        from ..models.antibody_sequence import AntibodySequence
        from ..models.assay_order_inline_request_settings_type_0 import (
            AssayOrderInlineRequestSettingsType0,
        )
        from ..models.protein_sequence import ProteinSequence

        d = dict(src_dict)
        assay_type = d.pop("assayType")

        sequences = []
        _sequences = d.pop("sequences")
        for sequences_item_data in _sequences:

            def _parse_sequences_item(data: object) -> AntibodySequence | ProteinSequence | str:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    sequences_item_type_1 = AntibodySequence.from_dict(data)

                    return sequences_item_type_1
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    sequences_item_type_2 = ProteinSequence.from_dict(data)

                    return sequences_item_type_2
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                return cast(AntibodySequence | ProteinSequence | str, data)

            sequences_item = _parse_sequences_item(sequences_item_data)

            sequences.append(sequences_item)

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
            AssayOrderInlineRequestModalityType1
            | AssayOrderInlineRequestModalityType2Type1
            | AssayOrderInlineRequestModalityType3Type1
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
                modality_type_1 = AssayOrderInlineRequestModalityType1(data)

                return modality_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, str):
                    raise TypeError()
                modality_type_2_type_1 = AssayOrderInlineRequestModalityType2Type1(data)

                return modality_type_2_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, str):
                    raise TypeError()
                modality_type_3_type_1 = AssayOrderInlineRequestModalityType3Type1(data)

                return modality_type_3_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                AssayOrderInlineRequestModalityType1
                | AssayOrderInlineRequestModalityType2Type1
                | AssayOrderInlineRequestModalityType3Type1
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

        def _parse_settings(data: object) -> AssayOrderInlineRequestSettingsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                settings_type_0 = AssayOrderInlineRequestSettingsType0.from_dict(data)

                return settings_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AssayOrderInlineRequestSettingsType0 | None | Unset, data)

        settings = _parse_settings(d.pop("settings", UNSET))

        assay_order_inline_request = cls(
            assay_type=assay_type,
            sequences=sequences,
            confirm_duplicate=confirm_duplicate,
            modality=modality,
            name=name,
            notes=notes,
            settings=settings,
        )

        return assay_order_inline_request
