# Architecture

The public package extracts three small components from the actual local MATRIX application rather than publishing its private deployment.

CLI / optional Tkinter UI → Store → SQLite authoritative registry → derived Markdown/JSON files.

`team_store.py`: explicit state machine, transactions and project lock, SHA-256 attachment evidence, approved mission freeze and handoff depth limit of 16.
`mission_chain.py`: sequential brief, assignments, received responses and status. It has no model/tool execution loop. Assignment markers are untrusted text; a response is not evidence of a file change.
`model_router.py`: deterministic keyword recommendation limited to a supplied list of aliases. No network calls.

The original machine-specific paths and game release-policy imports were removed. A new portable entry point and minimal desktop UI replace the private Pro interface. Private provider modules were excluded rather than stubbed as working integrations. Public data starts empty. No migration/import of personal conversations is performed.

Exports contain user-entered local paths and content; they are private runtime data. Do not commit them. CostGuard and provider abstraction remain roadmap items.
