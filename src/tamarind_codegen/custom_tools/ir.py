"""Small, immutable representation consumed by language-specific emitters.

There are deliberately no OpenAPI dictionaries or Python identifiers in this module.
The normalizer resolves OpenAPI structure; emitters make language-specific decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Scalar = str | int | float | bool | None
SchemaKind = Literal[
    "array",
    "boolean",
    "integer",
    "map",
    "null",
    "number",
    "object",
    "reference",
    "string",
]


@dataclass(frozen=True)
class Constraint:
    name: Literal["maxLength", "maximum", "minLength", "minimum", "pattern"]
    value: str | int | float


@dataclass(frozen=True)
class JsonArray:
    values: tuple[JsonValue, ...]


@dataclass(frozen=True)
class JsonObject:
    items: tuple[tuple[str, JsonValue], ...]


JsonValue = Scalar | JsonArray | JsonObject


@dataclass(frozen=True)
class Field:
    wire_name: str
    schema: Schema
    required: bool
    description: str | None = None


@dataclass(frozen=True)
class Schema:
    kind: SchemaKind
    nullable: bool = False
    description: str | None = None
    reference: str | None = None
    items: Schema | None = None
    fields: tuple[Field, ...] = ()
    additional_properties: bool | Schema | None = None
    enum: tuple[Scalar, ...] = ()
    has_const: bool = False
    const: Scalar = None
    has_default: bool = False
    default: JsonValue = None
    constraints: tuple[Constraint, ...] = ()


@dataclass(frozen=True)
class SchemaDefinition:
    name: str
    schema: Schema


@dataclass(frozen=True)
class Parameter:
    wire_name: str
    location: Literal["path", "query"]
    required: bool
    schema: Schema
    description: str | None = None


@dataclass(frozen=True)
class RequestBody:
    required: bool
    schema: Schema


@dataclass(frozen=True)
class Response:
    status: str
    description: str
    schema: Schema | None


@dataclass(frozen=True)
class Operation:
    operation_id: str
    method: Literal["DELETE", "GET", "PATCH", "POST", "PUT"]
    path: str
    parameters: tuple[Parameter, ...]
    request_body: RequestBody | None
    responses: tuple[Response, ...]
    summary: str | None = None


@dataclass(frozen=True)
class Api:
    title: str
    version: str
    server_url: str
    source_sha256: str
    schemas: tuple[SchemaDefinition, ...]
    operations: tuple[Operation, ...]
