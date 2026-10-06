# CostGuard — ROADMAP

v0.1.0 makes no model or provider calls. Its default inference cost is zero because no cloud inference is implemented. It does not implement a billing guard or infer subscription rights.

Planned: provider price metadata with timestamps, atomic reservations before a call, reconciliation against actual usage, persistent daily/project limits, bounded retries, human approval when a price is unknown, concurrency-safe accounting and EconomyMode. The SmartTeam and fast/standard/deep router design has not been implemented in this distribution. A local keyword match is not cost-aware inference routing.

Adapters must be disabled by default until these controls and failure tests exist. External providers may charge when a future user deliberately enables them; no free allowance is assumed.
