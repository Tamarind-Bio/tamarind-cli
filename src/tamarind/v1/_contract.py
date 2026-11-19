"""Generated from openapi/api-v1.yaml by scripts/sync_api_v1_contract.py. Do not edit."""

# Query parameters the contract declares `style: form, explode: false`, by generated
# module: a list goes on the wire as one comma-joined value (`status=Running,Complete`).
# The generated request builders send repeated keys instead, which the API reads as
# only the last value.
COMMA_JOINED_QUERY: dict[str, frozenset[str]] = {
    "get_usage": frozenset({"groupBy"}),
    "list_files": frozenset({"extension"}),
    "list_jobs": frozenset({"status"}),
}
