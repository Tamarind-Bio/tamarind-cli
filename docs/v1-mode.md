# v1 mode

With v1 selected, today's commands keep their names, flags, output layout and exit codes,
and the requests behind them go to the v1 API. This page lists what runs on v1, what still
runs on classic, and where the output differs from classic mode.

## Selecting v1

| Setting | Values | Default |
|---|---|---|
| `TAMARIND_API` / profile `"api"` | `classic`, `v1` | `classic` |
| `TAMARIND_V1_API_BASE` / profile `"v1_api_base"` | URL | `https://api.tamarind.bio` |

`TAMARIND_API_BASE` / `--api-base` stay the classic base. A few requests still go to
classic with v1 selected (below), so both bases must name the same environment. The
defaults do; on staging set both:

```bash
export TAMARIND_API=v1
export TAMARIND_V1_API_BASE=https://api-staging.tamarind.bio
export TAMARIND_API_BASE=https://staging.tamarind.bio/api/
```

## What runs on v1

| Command | v1 operation |
|---|---|
| `auth status`, `auth login` (the key check) | getMe |
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
| `custom-tools …` | the same operations at the v1 base; `custom-tools test` is submitJob pinned to the version |

There is no fallback to classic. When v1 refuses a request, the CLI shows v1's error with
today's exit codes (401 → 3, 404 → 4, 400/422 → 5, 429 → 6, budget or quota → 8, anything
else → 1). A 5xx or no answer is "outcome unclear", as in classic mode, so `submit` and
`batch` print their recovery command instead of retrying.

## What still runs on classic

These have no v1 form yet, so they stay on classic even with v1 selected:

- the catalog: `tools`, `schema`, `modalities`, `functions` (until the catalog server PRs land);
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

**custom-tools test:** v1 has no test marker, so the run doesn't appear in the website's
Test history.

**files delete of a missing file:** v1 answers 404 (exit 4); classic answers "File deleted
successfully".
