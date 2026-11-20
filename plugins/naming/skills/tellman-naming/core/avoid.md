# First question: should this name exist?

A name is indirection: it tells the reader they may stop here and not look inside. Good names are hard to find, so avoid needing one where you can.

Do not create a name when:

| Situation | Do instead |
|---|---|
| An intermediate result in a chain of transformations | Compose the steps; leave the middle unnamed |
| The implementation is clearer than any name you can think of | Keep it inline or anonymous |
| A function has grown large but its pieces have no good names | Leave it large. Names may come later |
| A conventional short name already fits (see the pack) | Use it; do not coin a word |
| You deliberated and still have no good name | Stop. Leave the code as it is |

Test: replace the name with its implementation. If little brevity is lost, the name is not earning its place.

When a name must exist:

- Do not make the name carry everything. Surrounding code, documentation and conversation carry the rest. Prefer `id` to `unique-arbitrary-string-id`.
- A value used many times may take a short name even if a longer one would explain more.
- Ignore "smaller functions are better". A large function claims that splitting it would not make it easier to understand. That claim is often right.

These run against common advice (extract and name; small functions; descriptive names). Follow this file anyway.
