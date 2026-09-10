# Prompt record — data generation

**Origin:** U1/U2/U3 in [session history](session-history.md).
No separate human generation prompt was supplied.

**Assistant-generated delegated prompt summary (A3):** Implement the deterministic
generator, tests, and generation notes in the standalone project. Match shared
CSV contracts; produce 10,000 customers, 100,000 orders, 500 products with seed 42
and as-of 2026-01-31. Inject the explicitly enumerated faults without changing row
counts; retain duplicate donor evidence, avoid incidental orphans, write a
reproducible manifest, and persist full source files safely.

**AI output / implementation decisions:** Standard-library generator, isolated
random state, integer-cent money, synthetic `example.com` email addresses, fault
line/donor mappings, hashes, internal sales personas, clean/custom-sized generation, and
protected refresh. Duplicated IDs replace existing values; 460 events correspond
to 490 direct failed rows when all duplicate members are flagged.

**Validation actually reported:** Initially 13 generator tests passed in 1.17s;
after source-tier correction, **14 passed in 1.11s**, including source-enum and
clean snapshot lifetime-value reconciliation checks. Corrected full default
CSVs and manifest persisted; counts and SHA-256 independently checked.
See [generation notes](../src/data_generation/DATA_GENERATION_NOTES.md).
Those checks do not constitute a Spark/Databricks pipeline run.

**Follow-up assistant task:** Correct the initial leakage of internal personas
into the source `customer_segment`. The generator now emits the required
Premium/Standard/Basic tiers while preserving internal sales personas. The
corrected default counts are Basic 5,003, Standard 2,499, Premium 2,498.
The agent verified that orders/products bytes and every non-segment customer
field were unchanged. Generator regression and persisted Spark fixture
integration subsequently passed within the **63-test unified suite**. Full-default
execution evidence is recorded separately in [test strategy](../test-strategy.md).

**Rejected AI suggestion — not a participant decision:** In sibling discussion,
an agent initially proposed relaxing Silver to accept the derived persona labels.
The coordinating assistant rejected that suggestion because the source contract
explicitly requires Premium/Standard/Basic. The generator was corrected instead;
Silver validation was not weakened.

| Participant review field | Value |
|---|---|
| Accepted / changed / rejected | I used the AI-generated synthetic sources in the delivered project; no separate generator rejection or modification is recorded |
| Rationale and any participant modifications | The sources provide known quality faults for the exercise without real customer data; the persona/source-tier correction was made by AI, not independently by me |
| Independent participant validation | I confirmed end-to-end Databricks execution; generator fault counts and hashes are attributed to the assistant's tests, not a separate manual audit by me |
