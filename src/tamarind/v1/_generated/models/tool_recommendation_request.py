from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.recommendation_ccd_input import RecommendationCcdInput
    from ..models.recommendation_sequence_input import RecommendationSequenceInput
    from ..models.recommendation_smiles_input import RecommendationSmilesInput


T = TypeVar("T", bound="ToolRecommendationRequest")


@_attrs_define
class ToolRecommendationRequest:
    """Ask which tool to run for a stated task.

    Attributes:
        prompt (str): What you want to do, in your own words — e.g. 'predict the structure of this antibody-antigen
            complex'.
        inputs (list[RecommendationCcdInput | RecommendationSequenceInput | RecommendationSmilesInput] | Unset): Your
            input sequence components, to tailor the recommendation to your specific inputs. Optional, but they are what let
            the recommendation rest on a measurement of your own target rather than an overall ranking.
    """

    prompt: str
    inputs: (
        list[RecommendationCcdInput | RecommendationSequenceInput | RecommendationSmilesInput]
        | Unset
    ) = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.recommendation_sequence_input import RecommendationSequenceInput
        from ..models.recommendation_smiles_input import RecommendationSmilesInput

        prompt = self.prompt

        inputs: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.inputs, Unset):
            inputs = []
            for inputs_item_data in self.inputs:
                inputs_item: dict[str, Any]
                if isinstance(inputs_item_data, RecommendationSequenceInput):
                    inputs_item = inputs_item_data.to_dict()
                elif isinstance(inputs_item_data, RecommendationSmilesInput):
                    inputs_item = inputs_item_data.to_dict()
                else:
                    inputs_item = inputs_item_data.to_dict()

                inputs.append(inputs_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "prompt": prompt,
            }
        )
        if inputs is not UNSET:
            field_dict["inputs"] = inputs

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.recommendation_ccd_input import RecommendationCcdInput
        from ..models.recommendation_sequence_input import RecommendationSequenceInput
        from ..models.recommendation_smiles_input import RecommendationSmilesInput

        d = dict(src_dict)
        prompt = d.pop("prompt")

        _inputs = d.pop("inputs", UNSET)
        inputs: (
            list[RecommendationCcdInput | RecommendationSequenceInput | RecommendationSmilesInput]
            | Unset
        ) = UNSET
        if _inputs is not UNSET:
            inputs = []
            for inputs_item_data in _inputs:

                def _parse_inputs_item(
                    data: object,
                ) -> (
                    RecommendationCcdInput | RecommendationSequenceInput | RecommendationSmilesInput
                ):
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        componentsschemas_recommendation_input_type_0 = (
                            RecommendationSequenceInput.from_dict(data)
                        )

                        return componentsschemas_recommendation_input_type_0
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        componentsschemas_recommendation_input_type_1 = (
                            RecommendationSmilesInput.from_dict(data)
                        )

                        return componentsschemas_recommendation_input_type_1
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_recommendation_input_type_2 = (
                        RecommendationCcdInput.from_dict(data)
                    )

                    return componentsschemas_recommendation_input_type_2

                inputs_item = _parse_inputs_item(inputs_item_data)

                inputs.append(inputs_item)

        tool_recommendation_request = cls(
            prompt=prompt,
            inputs=inputs,
        )

        return tool_recommendation_request
