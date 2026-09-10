# Copilot workflow — working instructions

These project guidance notes were authored during the implementation. They are
not a claim that Copilot automatically read this directory, and they are not
retrospective participant-authored instructions.

- Work within the approved standalone project and each delegated file scope.
  Coordinate interface changes rather than silently modifying another agent's files.
- Read shared contracts before implementing a layer. Keep table/column names,
  accepted source values, decimal semantics, and as-of configuration aligned.
- Preserve bad rows and raw evidence; do not repair tests by hiding defects or
  weakening checks. Explain all-member duplicate behavior explicitly.
- Use existing pytest validation, narrow selectors during diagnosis, then
  integrated/full-size gates. Separate observed command output from expected results.
- Use `uv sync --extra local --extra dev`, then `.venv/bin/medallion setup-java`,
  `.venv/bin/medallion generate`, and `.venv/bin/medallion run` locally. This avoids
  a plain `uv run` resync removing extras; if using `uv run`, specify
  `--extra local --extra dev` again. Do not install local Spark/Java extras into
  Databricks.
- Keep Spark Connect-compatible DataFrame/SQL paths for cloud execution. Use the
  notebook-provided session and authorized volume/catalog names.
- Never expose credentials or real customer data. Treat generated dashboards as
  data exports even when only aggregates are embedded.
- Distinguish pipeline SUCCESS from later local rendering/export and cloud
  dashboard publishing. No fallback or empty “success” should conceal failure.
- Record prompt/task summaries with their true author. Do not invent historical
  user messages, human approvals, personal reflections, commit history, or cloud runs.
- Do not stage or commit without a subsequent request. Leave participant review,
  identity, and submission fields pending when not provided.

These principles explain the implementation workflow; they do not override the
actual user's instructions or tool/runtime restrictions.
