# Prompt record — Bronze

**Origin:** The user requested the overall standalone solution, U2 in
[session history](session-history.md). There was no separate human Bronze prompt.

**Assistant implementation-task summary (not a verbatim prompt):** Build CSV
landing for the three shared source contracts. Preserve all raw lexical values,
represent empty CSV cells as null, reject header/record mismatches, and attach
source file, run ID, and ingestion time. Use the existing execution session and
explicit local Parquet/cloud managed-Delta persistence.

**AI output / decisions:** `src/bronze/ingest_all.py` reads without schema inference
or trimming, uses fail-fast CSV handling, checks exact ordered headers, and adds
metadata. Bronze is not a cleanup or deduplication step.

**Validation:** Core tests cover raw values, metadata, header rejection, and
malformed records. First core run failed partly because a timestamp assertion
expected a UTC-naive Python object. The assistant changed the assertion to the
Unix instant rather than modifying correct stored data. The 21-passing core rerun
includes Bronze tests; final full-size persistence remains a separate gate.
The later **63-test unified suite** also passed Bronze and persisted Spark
fixture/rerun checks.
The successful full-default run subsequently persisted all **10,000 customer,
100,000 order, and 500 product** Bronze rows; see [test evidence](../test-strategy.md).

**Later specialist feedback / assistant correction:** Default backslash CSV
escaping corrupted standard doubled quotes such as `John "JJ" Doe`. The coordinator
set double-quote escaping and enabled quoted multiline fields, then added a
regression, including valid quoted newlines. This actual finding was subsequently
covered by the final **67-passing suite** and successful full-default rerun.
Earlier passing evidence alone was not treated as proof of the fix.

| Participant review field | Value |
|---|---|
| Accepted / changed / rejected | I used the delivered ingestion and configured the setup SQL for the `workspace` catalog |
| Rationale and any participant modifications | The catalog change aligned the setup with my Databricks target; raw preservation and CSV parsing corrections were assistant implementation choices |
| Independent participant validation | I ran the project successfully on Databricks; quote/newline/header edge-case coverage comes from the preserved assistant-run tests |
