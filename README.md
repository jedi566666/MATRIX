# MATRIX Open Source

MATRIX is an open-source AI orchestration and workspace system for coordinating agents, projects, tools and cost-aware model routing.

**v0.1.0 is the standalone local coordination core extracted from the author's working MATRIX application.** It is not a release of the complete private MATRIX Pro desktop deployment. It records and routes work; it does not call AI models or execute tools. No paid service, credentials or private project is required.

## Capability status

| Status | Capabilities |
|---|---|
| IMPLEMENTED | SQLite mission registry, persistent event history, state transitions, one active mission per project, evidence and deliverable SHA-256 verification, explicit human approval, risk authorization invalidated when inputs change, bounded/idempotent handoffs, Markdown/JSON exports, role-based available-agent recommendations, sequential mission briefs, CLI, offline desktop mission creation/listing |
| EXPERIMENTAL | The generic sequential MissionChain assignment protocol and standalone minimal desktop UI; model outputs are untrusted, do not prove execution |
| ROADMAP | SmartTeam selection, price-aware routing, persistent atomic CostGuard reservation ledger, EconomyMode, provider adapters, streaming chat, sandboxed tools, richer desktop conversations |

The existing role matcher scores local keywords against available aliases. It does not query a provider catalogue, prices, entitlements or model capabilities. Historical alias names are routing labels, not a promise that a cloud model exists or is available. Cost-aware routing in the project description is a goal; no monetary budget enforcement is implemented in this release.

## Install and run

Python 3.10+; no runtime dependencies. Tkinter is optional for the desktop UI.

```sh
git clone https://github.com/jedi566666/MATRIX.git
cd MATRIX
python -m matrix --help
python -m matrix --data-dir ./local-data create --project demo --agent reviewer --objective "Review the example" --deliverables "review.md"
python -m matrix --data-dir ./local-data list
python -m matrix --data-dir ./local-data gui
```

These source commands run offline without installation. For an installed command:

```sh
python -m venv .venv
# Activate .venv using your platform's standard command.
python -m pip install .
matrix-workspace --help
```

Linux GUI installations may require their distribution's `python3-tk` package. Headless users can use the CLI. Default data is stored under `~/.matrix-workspace`; override it with `--data-dir` or the `MATRIX_DATA_DIR` environment variable. `.env.example` is documentation; MATRIX does not automatically load `.env` files.

## Workflow and tools

READY → WORKING → REVIEW → APPROVED → DONE. BLOCKED can return to READY. Approval requires a producer flag and existing evidence plus deliverables with matching hashes. This is a single-user trust boundary, not authentication or an operating-system sandbox. Attachments are copied only when explicitly selected; review them before sharing exports.

The public release uses an offline CLI/GUI rather than the private Pro provider integrations. Projects are supplied by the user, not imported from a personal registry. Providers and automated tool execution are disabled; third-party adapters must be reviewed before enabling them.

## Develop

```sh
python -m unittest discover -s tests -v
python -m compileall -q matrix tests
python scripts/release_gate.py
python -m pip wheel --no-deps . -w dist
```

CI runs on Linux and Windows. No model requests are made by tests. See [architecture](docs/ARCHITECTURE.md), [security](SECURITY.md), [CostGuard status](docs/COST_GUARD.md), [roadmap](docs/ROADMAP.md), [contributing](CONTRIBUTING.md) and [third-party notices](THIRD_PARTY_NOTICES.md).

## License and project boundaries

Apache-2.0: see LICENSE and NOTICE. Only this repository's software and documentation are licensed. MTP ECU, tokens, wallets, creative publications, manuscripts, commercial assets, private infrastructure and unrelated works are excluded. No trademark license or affiliation with an AI provider is implied.

Maintainer: Mehdi (@jedi566666). Report normal issues on GitHub; follow SECURITY.md for sensitive reports. Created with assistance from Codex, with release tests and scope reviewed locally. No community adoption or provider certification is claimed.
