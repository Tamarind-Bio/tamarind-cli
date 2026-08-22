# Tamarind Custom Tools OpenAPI profile

The Custom Tools Python SDK is generated through an explicit compiler boundary:

```text
public OpenAPI document
    -> validate this profile
    -> normalize to the language-neutral IR
    -> generate the Python transport
    -> format, type-check, and contract-test the generated package
```

The generator must not interpret raw OpenAPI. All OpenAPI-specific decisions belong to
the profile validator and normalizer. The generator consumes only the normalized IR in
`tamarind_codegen.custom_tools.ir`.

## Supported profile

The first profile intentionally covers the public Custom Tools control-plane API rather
than the entire OpenAPI specification.

- OpenAPI 3.1 documents.
- HTTP `GET`, `POST`, `PUT`, `PATCH`, and `DELETE` operations with unique `operationId`s.
- Path and query parameters. Path parameters must be required.
- Optional or required `application/json` request bodies.
- `application/json` and `application/problem+json` responses, plus responses with no body.
- Local references to component schemas, responses, parameters, and request bodies.
- Object, array, string, integer, number, boolean, and null schemas.
- String and numeric constraints used by the API: `minLength`, `maxLength`, `pattern`,
  `minimum`, and `maximum`.
- Enumerations, constants, defaults, typed maps, and nullable schemas represented as
  `anyOf: [<schema>, {"type": "null"}]`.

## Explicit non-goals

The validator rejects these constructs with a location-specific error:

- external references;
- callbacks, webhooks, links, and cookie or header parameters;
- XML, multipart, form-encoded, or multiple request/response media types;
- general `oneOf`, `allOf`, or `anyOf` unions;
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
| Runtime upload, deploy, and polling behavior | Hand-written SDK layer |

The immutable source revision used by upload and deploy is a separate runtime invariant.
It is not encoded in the generator; the generated transport only exposes the server
contract needed by the hand-written SDK workflow.
