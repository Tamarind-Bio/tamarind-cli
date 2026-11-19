from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_metadata_request_metadata import UpdateMetadataRequestMetadata
    from ..models.update_metadata_request_properties import UpdateMetadataRequestProperties


T = TypeVar("T", bound="UpdateMetadataRequest")


@_attrs_define
class UpdateMetadataRequest:
    """The spec's `UpdateMoleculeRequest` — a PARTIAL patch across the MOLECULE and
    MEMBERSHIP tenancy grains, applied ATOMICALLY (all-or-nothing, one transaction: if any
    field's write fails, none of them persist).

    Every field is OPTIONAL and independent: an ABSENT field is left untouched, which
    is DISTINCT from a field sent as `null` (which CLEARS it, where the grain allows).
    The fields and the grain each writes:

      * `properties` (MOLECULE grain) — merge scalar annotations into the molecule's
        metadata. Only the keys you send change; a key set to `null` REMOVES that key
        (an absent key and a null key mean different things, so the raw dict carries
        intent). Tool score-run entries are written by tools and are not editable here;
        when the molecule's group is schema-bound the MERGED result must still satisfy
        it. This is the properties-only PATCH's behaviour, unchanged.
      * `source` (MOLECULE grain) — the id of the PARENT molecule this one was derived
        from; `null` clears it. The parent must be visible in YOUR scope, or the write
        is refused (404) — you cannot point a molecule at a parent you cannot see.
      * `fileId` (MOLECULE + MEMBERSHIP grain) — a structure file to associate as this
        membership's primary; `null` clears it. The file must already be attached to
        this molecule in your tenant.
      * `name` (MEMBERSHIP grain) — rename this molecule's per-group display name. A
        name already used by another molecule in the same group is a 409 conflict (the
        `UNIQUE (group_id, name)` constraint), never a 500.

    The membership-grained writes (`name`, `fileId`) target the molecule's MOST RECENT
    in-scope group membership, matching how the group-less by-id read resolves labels.

        Attributes:
            file_id (None | str | Unset):
            metadata (UpdateMetadataRequestMetadata | Unset): DEPRECATED alias for `properties`, kept for callers written
                against the original v1 shape. Send `properties` instead; if both are sent, `properties` wins.
            name (str | Unset):
            properties (UpdateMetadataRequestProperties | Unset):
            source (None | str | Unset):
    """

    file_id: None | str | Unset = UNSET
    metadata: UpdateMetadataRequestMetadata | Unset = UNSET
    name: str | Unset = UNSET
    properties: UpdateMetadataRequestProperties | Unset = UNSET
    source: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        file_id: None | str | Unset
        if isinstance(self.file_id, Unset):
            file_id = UNSET
        else:
            file_id = self.file_id

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        name = self.name

        properties: dict[str, Any] | Unset = UNSET
        if not isinstance(self.properties, Unset):
            properties = self.properties.to_dict()

        source: None | str | Unset
        if isinstance(self.source, Unset):
            source = UNSET
        else:
            source = self.source

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if file_id is not UNSET:
            field_dict["fileId"] = file_id
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if name is not UNSET:
            field_dict["name"] = name
        if properties is not UNSET:
            field_dict["properties"] = properties
        if source is not UNSET:
            field_dict["source"] = source

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_metadata_request_metadata import UpdateMetadataRequestMetadata
        from ..models.update_metadata_request_properties import UpdateMetadataRequestProperties

        d = dict(src_dict)

        def _parse_file_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        file_id = _parse_file_id(d.pop("fileId", UNSET))

        _metadata = d.pop("metadata", UNSET)
        metadata: UpdateMetadataRequestMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = UpdateMetadataRequestMetadata.from_dict(_metadata)

        name = d.pop("name", UNSET)

        _properties = d.pop("properties", UNSET)
        properties: UpdateMetadataRequestProperties | Unset
        if isinstance(_properties, Unset):
            properties = UNSET
        else:
            properties = UpdateMetadataRequestProperties.from_dict(_properties)

        def _parse_source(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        source = _parse_source(d.pop("source", UNSET))

        update_metadata_request = cls(
            file_id=file_id,
            metadata=metadata,
            name=name,
            properties=properties,
            source=source,
        )

        return update_metadata_request
