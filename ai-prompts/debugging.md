# Prompt record — debugging

**Origin:** Implementation follow-up under user request U2. No human debugging
prompt or separate debugging-agent delegation was supplied.

**Assistant task/action summary, not a reconstructed prompt:** Diagnose failures
encountered while installing the package, starting Spark, and running core tests;
make focused corrections and rerun relevant checks.

**Observed feedback and response:**

1. Editable install failed because package directories did not yet exist →
   create them, then retry sync.
2. Slim Java 21 lacked `jdk.incubator.vector` → replace `jdk4py` with an isolated
   full JDK via `install-jdk`.
3. macOS JDK bundle root needed `Contents/Home` → normalize Java home.
4. Spark workers used Python 3.9 with a Python 3.12 driver → set both PySpark
   interpreter variables to `sys.executable`.
5. Timestamp test compared local-time collection to UTC-naive expected value →
   compare Unix epoch; do not change the correct stored instant.

**Actual evidence:** Spark 4.0.4 smoke passed. First core run: 15 passed, 6 failed.
Coordinator-reported rerun: 21 passed in 14.67s. See
[debugging notes](../debugging-notes.md) for commands and limitations.
The assistant changed its own earlier implementation/assertion choices; this
does **not** mean the participant accepted or rejected them.

**Additional inspection feedback:** Source-segment and trend-grain interface
mismatches were raised during documentation work. The generator's source tiers
were corrected with a 14-passing regression and regenerated snapshot; Gold was
aligned to `period_type`. Coordinator acceptance review also requested exact
Gold output aliases/customer fields and required histogram/pie charts.
The corrected focused Gold/dashboard suite reported 21 passed in 15.53s.
The later unified suite passed 63 tests in 26.60s, including independent
acceptance and persisted fixture/rerun checks. Full-default/browser evidence is
tracked separately. These findings are not invented failed-run traces or
participant decisions.

**Later actual specialist review:** Two verified bugs were found after the
63-test/full-run validation: default Spark CSV escaping disagreed with
`csv.writer` doubled quotes; default trimming/email whitespace checks missed
Unicode whitespace. The coordinator corrected escaping/quoted multiline support
and Unicode edge/email handling, preserving `_raw`, and added regressions.
The interim expectation was 66 tests; valid quoted-newline coverage brought the
final result to **67 passed in 28.97s**. The final CLI/wheel succeeded. The
coordinator requested a targeted recheck of the four corrected source/test files;
the specialist confirmed both findings resolved and no significant issues in
those fixes. The earlier actual screenshot is retained with its original run ID.
No clean initial review is claimed.

## Actual Databricks follow-up: 2026-09-10

The participant reported a placeholder mismatch during dashboard SQL generation
after the pipeline succeeded. The assistant reproduced the exact call against
source and the built wheel successfully, improved mismatch diagnostics and added
regressions, documented notebook installation/restart checks and produced
rendered SQL as a workaround. The actual mismatched cloud file was not inspected.
The participant subsequently confirmed end-to-end execution and dashboard
creation, without stating which remediation resolved their environment.
See [the dashboard prompt record](dashboard.md) for the detailed account.

| Participant review field | Value |
|---|---|
| Accepted / changed / rejected | I supplied the exact dashboard-helper call and exception for AI-assisted investigation, then confirmed the project and dashboard worked; the record does not specify which remediation I used |
| Rationale and any participant modifications | I needed usable dashboard SQL after the pipeline succeeded; I do not claim a confirmed stale-wheel root cause or that I independently found the earlier implementation bugs |
| Independent participant validation | I confirmed cloud completion and supplied published-dashboard screenshots; the assistant's package/test checks remain separately attributed |
