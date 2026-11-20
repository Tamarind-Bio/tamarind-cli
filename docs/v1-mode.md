# v1 mode

The CLI and the Python SDK (`tamarind.Tamarind`, `tamarind.rest`) call the v1 API for a
key when the server says to. Nothing changes on the client side: today's commands and
methods keep their names, flags, signatures, output layout and exit codes, and the
requests behind them go to v1. This page lists what runs on v1, what still runs on
classic, and where the output differs from classic.

## How v1 is chosen

The server decides, per user: the LaunchDarkly flag `cli-sdk-v1-api`, answered on v1
`GET /me` as `clients.useV1`. The client asks on the first request v1 can answer (never
for `--help`, `--version` or other offline commands) and keeps the answer for 5 minutes,
per key and environment. The CLI keeps it in `~/.tamarind/v1-flag.json` (or under
`TAMARIND_CONFIG_DIR`), mode 0600, which holds a hash of the key, never the key itself.
Anything but an explicit `true` means classic: no answer, a 401, a 404 (a caller outside
v1), the field false or missing. Once a client (or a CLI command) has its answer it keeps
it, so a long `wait` never changes API halfway; a flag change reaches the next command
within 5 minutes. `--help` lists the v1-only commands from the last answer kept, so a
flagged user's very first `--help`, before any command has asked, doesn't list them yet.

The v1 API is the one in the classic base's environment: `app.tamarind.bio` →
`api.tamarind.bio`, `staging.tamarind.bio` → `api-staging.tamarind.bio`. Any other
`--api-base` (a local server) has no v1 and stays classic. `TAMARIND_V1_API_BASE`
overrides the v1 base for tests; `TAMARIND_API=classic` turns v1 off.

Operations only v1 has (`tamarind projects`, `client.projects`, `client.jobs.get`...)
run only when v1 is on for the key; otherwise they say "uses the v1 API, which isn't
enabled for this account yet" (exit 2) and send nothing.

## What runs on v1

| Command | v1 operation |
|---|---|
| `auth status`, `auth login` (the key check) | listJobs (classic's check, one job) |
| `jobs`, `jobs --batch`, `status`, `wait`, `submit --wait` | listJobs, getJob |
| `validate`, the check `submit` makes first, `batch --prevalidate` | validateJob |
| `submit`, `batch` | submitJob |
| `cancel`, `cancel --batch` | cancelJob |
| `results` (download, `--show-url`, `--file`) | archiveJob (archivePipelineRun for a run), getJobFile |
| `delete` | deleteJob |
| `logs` | getJobLogs |
| `files list`, `files stats`, `files folders` | listFiles |
| `files upload` | uploadFile |
| `files delete` | deleteFile |
| `custom-tools …` | the same operations at the v1 base; `custom-tools test` is submitJob pinned to the version; a build's upload session (v1 `id`) is read as classic's `uploadId` |

In the SDK, `Tamarind().jobs`, `.files`, `.custom_tools`, `.pipelines.get_run` and the
`tamarind.rest` functions follow the same table: the SDK and the CLI share one mapping
(`tamarind._v1.classic`).

There is no fallback to classic. When v1 refuses a request, the CLI shows v1's error with
today's exit codes (401 → 3, 404 → 4, 400/422 → 5, 429 → 6, budget or quota → 8, anything
else → 1). The error is a `ProblemError` (with v1's problem document) that is also the
classic class for its status (`AuthError`, `NotFoundError`, `ValidationError`,
`RateLimitError`, `BudgetError`, `APIError` with `status_code`), so existing `except`
clauses still match. On the requests v1 serves at the same path (custom tools, pipeline
runs) the error is the class classic gives the same answer (`CustomToolExistsError`...),
also a `ProblemError`; a refusal v1 codes as about the key or budget is the auth or
budget error. A 5xx or no answer is "outcome unclear", as in classic mode, so
`submit` and `batch` print their recovery command instead of retrying.

## What still runs on classic

These have no v1 form yet, so they stay on classic even with v1 on:

- the tool list: `tools` (`Tamarind().tools.list`, `tamarind.catalog.list_tools`), held
  on the catalog until the tool set is decided (see "The catalog" below), and
  `tools --custom` in any case (v1's listTools holds built-in tools only). `schema`,
  `modalities` and `functions` are v1's;
- another member's jobs: `--organization`, `--email` (until website#7795);
- `jobs --include-subjobs`;
- `results --pdbs-only` (until v1 serves `bestStructures`);
- `logs` of a batch or a pipeline run (v1 reads one job's log);
- `results RUN --file PATH`, one file of a pipeline run (v1's file read takes a job or a batch);
- `delete NAME` when only a pipeline run has that name (v1 deletes jobs and batches);
- `files delete PATH --folder F` (a path and a folder together).

## Differences from classic mode

Found by running each command on staging in both modes and diffing the output.

**Job rows** (`jobs`, `status`, `wait`, `submit --wait`):
- No `StorageFolder` or `TamarindSchemaVersion`. List rows also have no `Settings`; v1
  lists don't carry settings, and `status` of one job does.
- A batch's `status` has no `redactedFields`.
- Lists leave out the internal `batch-aggregate` jobs. A page of `--limit N` therefore
  holds other jobs, and a `--status` filter (applied to that page) can count differently.
- `jobs --batch` lists the batch's jobs in v1's order, which can differ from classic's.
- `status` of an unknown job gives the same message and exit code, without classic's
  problem detail.

**validate:**
- An invalid report has no `missing_fields`. Classic lists the schema of each missing
  required setting there; v1 names the field in `errors`.
- v1 refuses the 99 old setting names that classic still accepts. Its 422 names the
  current setting to use.

**cancel --batch:** the counts come from v1's batch counts just before the cancel. Right
after `batch`, v1 may not have created the batch's jobs yet. It then says "Cancelled 1
job" (the batch itself) where classic says "Cancelled 3 jobs".

**results --show-url:** the URL is v1's presigned URL: a different S3 host form and
different query parameters, for the same file.

**logs:** no `s3Path`. For a log longer than 256 KB, `totalLines` and the byte offsets are
null, because v1 pages back with a cursor rather than byte offsets.

**files list:** the same files. After the five newest, the rest are sorted by name ignoring
case, by code point, where classic uses JavaScript's `localeCompare`. Names that differ
only in punctuation can swap places (`1IEP.pdb` and `1iep_imatinib_pose.pdb`).

**files folders:** no `labels` (classic's map of folder to job name) and no `nextCursor`.

**results --wait of a batch:** v1 can call a batch Complete before its archive is built.
Under `--wait` the CLI asks again after v1's `retryAfterSeconds` until the archive is ready
or `--timeout` passes (exit 7). Without `--wait` it says the archive is still being
prepared.

**custom-tools test** (and the SDK's `CustomTool.test`): v1 has no test marker, so the
run doesn't appear in the website's Test history.

**files delete of a missing file:** v1 answers 404 (exit 4); classic answers "File deleted
successfully".

**SDK pipeline runs:** `pipelines.get_run` takes classic's bare run id (sent to v1 as
`run_<id>`) and answers with it; the run, its node runs and a node run's `molecules()`
are read in classic's shape (v1's molecule `id` is classic's `complex_id`, the same
value). Checked live on staging: the typed objects are equal. v1's added
`failureReason` isn't on the typed objects.

**SDK `files.list`:** like classic, it reads only `folder` and `include_folders` (classic's
`pages/api/files.js` ignores `include_all`, `include_metadata` and the paging options).
With `include_folders`, folders are listed as `path/` ahead of the newest files, as
classic dates them "now".

**SDK `jobs.list` filters:** `kind`, `status`, `tool` and `search` are v1's. With v1 off,
passing one raises "isn't enabled for this account yet"; they can't be combined with
`organization`, `job_email`, `include_subjobs` or `job_name`.

**The catalog** (`tamarind._v1.catalog`). `modalities`, `functions` and `schema` (and in
the SDK `Tamarind().tools.modalities/functions/schema/example` and `tamarind.catalog`)
are answered from v1 and rebuilt in the catalog's layout: getToolFacets for the facets,
getToolSchema with getTool for a schema. The tool list (`catalog/tools`) has the same
mapping (every page of listTools, with the catalog's own filters, sort, facet lists,
unrecognized-filter note and hints applied), but it stays on the catalog while
`LIST_ON_V1` is off, as it is today. Diffed on staging for one account, every tool,
against the staging MCP's catalog:
- `modalities` and `functions`: the same values, labels and descriptions. `toolCount`
  counts v1's tool list.
- The tool list on v1 (held): v1's list is the app's (website#7796), 429 tools where the
  catalog lists 456. Only the catalog lists `abgpt`, the `rosetta-*` tools, the
  `*-inference` model tools, `bbmerge`, `pilot-sbdd` and `t2pmhc`; only v1 lists
  `odesign-antibody`, `protein-scoring` and `virtual-screening`. For the tools both list:
  the same envelope, filters, order, hints and fields, except `outputTypes`, which follows
  the app's ligand rule (`boltz`: `pdb`, where the catalog says `pdb`, `sdf`). v1 answers
  the schema of every listed tool but `abgpt`, which this account can't run.
- `schema`: the same envelope, display name, description, categories, tags, hint and
  output types. `outputs` is v1's output contract (with the catalog's `byTaskNote`), the
  catalog's for 446 of 455 tools; the other 9 differ in `produces` by the app's rules
  (website#7807). `exampleJobNote` is the catalog's text for the example.
- `schema` parameters are v1's JSON Schema rebuilt as the catalog's list: `name`, `type`,
  `displayName`, `descr`, `default`, `required`, `options`, `lowerBound`/`upperBound` and
  `example`. Left out, with no v1 form: `constraints`, `constraintsText`, `conditionals`,
  `tasks` and the catalog's other UI keys (`showWithRequired`, `extension`, `list`,
  `optionsDescr`, `requiredWhen`...). `descr` is v1's description, which also states the
  constraints (the catalog's text for 42% of settings). `required` is v1's, with what a
  branch requires; a required setting with a default isn't required on v1, which fills it
  in (87% the same). The names are v1's: about 150 settings are named differently from the
  catalog's, and with v1 on, submits take v1's names.
- `schema --example` (`Tamarind().tools.example`) is v1's `example`, built for one task
  branch: the same settings as before for 389 of 426 tools.
- A tool hidden from the assistant (`Hide: agent`: `odesign-antibody`, `protein-scoring`,
  `virtual-screening`) has a schema on v1, where the catalog refuses it.

**Job rows, three more** (from review, not yet changed): a v1 `Failed` job shows `Failed`
where classic says `Stopped`; `stopReason` is kept only for a low-priority job; a pipeline
step's job has no `Batch`.
