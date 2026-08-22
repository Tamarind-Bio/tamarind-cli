# Tamarind Custom Tools OpenAPI profile

The Custom Tools Python SDK is generated through an explicit compiler boundary:

```text
complete backend-generated public OpenAPI
    -> project operations tagged `custom-tools`
    -> validate this profile
    -> normalize to the language-neutral IR
    -> generate the Python transport
    -> format, type-check, and contract-test the generated package
```

The Python emitter must not interpret raw OpenAPI. Selection belongs to the projector;
remaining OpenAPI-specific decisions belong to the profile validator and normalizer.
The emitter consumes only the normalized IR in `tamarind_codegen.custom_tools.ir`.

## Supported profile

The first profile intentionally covers the public Custom Tools control-plane API rather
than the entire OpenAPI specification.

- OpenAPI 3.1 documents using the default OpenAPI dialect or the standard JSON Schema
  2020-12 dialect. Custom dialects are rejected.
- One concrete global HTTPS server and one global `x-api-key` header security scheme.
- HTTP `GET`, `POST`, `PUT`, `PATCH`, and `DELETE` operations with unique `operationId`s.
- Scalar path, query, and header parameters. Path parameters must be required strings;
  required parameters are non-null, while optional query parameters may use FastAPI's
  nullable representation.
- Only default OpenAPI parameter serialization: simple/non-exploded paths and
  form/exploded queries and simple/non-exploded headers, without `allowReserved`.
- Optional or required non-null `application/json` request bodies.
- `application/json` and `application/problem+json` responses, plus responses with no body.
- Exactly one successful response per operation.
- Local references to component schemas, responses, parameters, and request bodies.
- Named component objects, typed maps, arrays, strings, integers, numbers, booleans, and null
  schemas. Structured object schemas must be component definitions; objects cannot combine
  declared properties with typed additional properties.
- String, numeric, and array constraints used by the API: `minLength`, `maxLength`,
  `pattern`, `minimum`, `maximum`, `minItems`, and `maxItems`.
- Scalar enumerations and constants, defaults, and nullable schemas represented as
  `anyOf: [<schema>, {"type": "null"}]`.

Every supported OpenAPI object kind has a closed field allowlist. Documentation-only
`title`, `summary`, `description`, `tags`, `x-doc-group`, and `x-tamarind-group` may
be accepted where applicable without affecting the transport. Any other field is rejected,
even when it is valid in general OpenAPI, unless the IR and emitter explicitly support its
transport behavior.

## Explicit non-goals

The validator rejects these constructs with a location-specific error:

- external references;
- callbacks, webhooks, links, and cookie parameters;
- XML, multipart, form-encoded, or multiple request/response media types;
- general `oneOf`, `allOf`, or `anyOf` unions;
- schema assertions other than the string and numeric constraints listed above;
- discriminators, recursive references, tuples, and conditional JSON Schema;
- arbitrary extension behavior that would require the Python emitter to understand
  OpenAPI.

Adding a feature requires changing this document, the validator, the IR if necessary,
and fixtures demonstrating the generated behavior. Unsupported input is an error rather
than an invitation for the emitter to guess.

## Ownership

| Concern | Owner |
|---|---|
| Whether an OpenAPI construct is supported | Profile validator |
| Reference resolution and nullable/parameter normalization | Normalizer |
| Stable semantic representation | IR |
| Python names, imports, models, and request code | Python emitter |
| Formatting and type correctness | CI |
| Runtime upload, build, and polling behavior | Hand-written SDK layer |

The backend commits one complete public OpenAPI artifact. The CLI vendors it verbatim,
records its source repository, full commit, path, and SHA-256 in
`openapi/public-v1.lock.json`, then deterministically projects operations tagged
`custom-tools` before profile validation and generation.
