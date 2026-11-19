from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.assay_type_modalities_item import AssayTypeModalitiesItem

if TYPE_CHECKING:
    from ..models.assay_setting import AssaySetting
    from ..models.assay_type_includes_assays_item import AssayTypeIncludesAssaysItem


T = TypeVar("T", bound="AssayType")


@_attrs_define
class AssayType:
    """One wet-lab assay you can order.

    Attributes:
        assay_type (str): The value to send as `assayType`.
        category (str):
        description (str):
        details (None | str):
        doc_url (None | str):
        includes_assays (list[AssayTypeIncludesAssaysItem]): The assays an order of this type runs.
        max_sequences (int):
        method (None | str):
        min_sequences (int):
        modalities (list[AssayTypeModalitiesItem]): The `modality` values this assay accepts.
        multi_chain_protein (bool): False when a protein sequence must be a single chain.
        name (str):
        provider (str): The lab running it. More labs may be added, so handle one you do not know.
        provider_name (str):
        settings (list[AssaySetting]): What `settings` takes on an order of this type.
        targets_provider (None | str): Send this as `provider` to `listAssayTargets` to find target ids. Null when the
            assay takes no target.
        turnaround (None | str):
    """

    assay_type: str
    category: str
    description: str
    details: None | str
    doc_url: None | str
    includes_assays: list[AssayTypeIncludesAssaysItem]
    max_sequences: int
    method: None | str
    min_sequences: int
    modalities: list[AssayTypeModalitiesItem]
    multi_chain_protein: bool
    name: str
    provider: str
    provider_name: str
    settings: list[AssaySetting]
    targets_provider: None | str
    turnaround: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        assay_type = self.assay_type

        category = self.category

        description = self.description

        details: None | str
        details = self.details

        doc_url: None | str
        doc_url = self.doc_url

        includes_assays = []
        for includes_assays_item_data in self.includes_assays:
            includes_assays_item = includes_assays_item_data.to_dict()
            includes_assays.append(includes_assays_item)

        max_sequences = self.max_sequences

        method: None | str
        method = self.method

        min_sequences = self.min_sequences

        modalities = []
        for modalities_item_data in self.modalities:
            modalities_item = modalities_item_data.value
            modalities.append(modalities_item)

        multi_chain_protein = self.multi_chain_protein

        name = self.name

        provider = self.provider

        provider_name = self.provider_name

        settings = []
        for settings_item_data in self.settings:
            settings_item = settings_item_data.to_dict()
            settings.append(settings_item)

        targets_provider: None | str
        targets_provider = self.targets_provider

        turnaround: None | str
        turnaround = self.turnaround

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "assayType": assay_type,
                "category": category,
                "description": description,
                "details": details,
                "docUrl": doc_url,
                "includesAssays": includes_assays,
                "maxSequences": max_sequences,
                "method": method,
                "minSequences": min_sequences,
                "modalities": modalities,
                "multiChainProtein": multi_chain_protein,
                "name": name,
                "provider": provider,
                "providerName": provider_name,
                "settings": settings,
                "targetsProvider": targets_provider,
                "turnaround": turnaround,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.assay_setting import AssaySetting
        from ..models.assay_type_includes_assays_item import AssayTypeIncludesAssaysItem

        d = dict(src_dict)
        assay_type = d.pop("assayType")

        category = d.pop("category")

        description = d.pop("description")

        def _parse_details(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        details = _parse_details(d.pop("details"))

        def _parse_doc_url(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        doc_url = _parse_doc_url(d.pop("docUrl"))

        includes_assays = []
        _includes_assays = d.pop("includesAssays")
        for includes_assays_item_data in _includes_assays:
            includes_assays_item = AssayTypeIncludesAssaysItem.from_dict(includes_assays_item_data)

            includes_assays.append(includes_assays_item)

        max_sequences = d.pop("maxSequences")

        def _parse_method(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        method = _parse_method(d.pop("method"))

        min_sequences = d.pop("minSequences")

        modalities = []
        _modalities = d.pop("modalities")
        for modalities_item_data in _modalities:
            modalities_item = AssayTypeModalitiesItem(modalities_item_data)

            modalities.append(modalities_item)

        multi_chain_protein = d.pop("multiChainProtein")

        name = d.pop("name")

        provider = d.pop("provider")

        provider_name = d.pop("providerName")

        settings = []
        _settings = d.pop("settings")
        for settings_item_data in _settings:
            settings_item = AssaySetting.from_dict(settings_item_data)

            settings.append(settings_item)

        def _parse_targets_provider(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        targets_provider = _parse_targets_provider(d.pop("targetsProvider"))

        def _parse_turnaround(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        turnaround = _parse_turnaround(d.pop("turnaround"))

        assay_type = cls(
            assay_type=assay_type,
            category=category,
            description=description,
            details=details,
            doc_url=doc_url,
            includes_assays=includes_assays,
            max_sequences=max_sequences,
            method=method,
            min_sequences=min_sequences,
            modalities=modalities,
            multi_chain_protein=multi_chain_protein,
            name=name,
            provider=provider,
            provider_name=provider_name,
            settings=settings,
            targets_provider=targets_provider,
            turnaround=turnaround,
        )

        assay_type.additional_properties = d
        return assay_type

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
