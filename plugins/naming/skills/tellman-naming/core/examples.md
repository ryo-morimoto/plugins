# Worked pairs

**Named after the implementation.**
Bad: `get-sol-jupiter` only looks under `[:sol :jupiter]`; inlining loses little.
Good: `jovian-moons`, named for purpose; where the data lives becomes a hidden detail.

**Intermediate names.**
Bad: `(let [trimmed (trim s) lowered (lower trimmed) parts (split lowered)] parts)`
Good: `(-> s trim lower split)`

**Short name, complex right-hand side.**
Bad: `g` bound to a long chain; the reader must study both sides.
Good: name the chain's result `surface-gravities`; keep `g` for the loop variable.

**Pure function.**
Bad: `calculate-md5`, `get-timestamp`. Good: `md5`, `timestamp`.

**Reads from outside.**
Bad: `payload` for a function that hits the network. Good: `fetch-payload`.

**Map.**
Bad: `graph`, `student-map`. Good: `handle->downstreams`, `class->students` (in TypeScript `studentsByClass`).

**One everyday word, several meanings.**
`student` means an applicant to admissions, an enrolled person to the bursar, someone registered for classes to faculty. One type for all three is only as narrow as the loosest meaning.

**Implementation fact treated as meaning.**
One engineer stores ids in 128 bits; another matches them with a 36-character pattern in logs. Both made today's UUID part of what `id` means. Neither notices until it changes.

**Interface for one caller.**
Bad: a versioned `PricingServiceV1` interface with one implementation and one caller. Good: call the function.

If a case looks like one of these but the readers or the expected change differ, reason from the rule, not from the example.
