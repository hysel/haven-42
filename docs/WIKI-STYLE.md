# Haven 42 Wiki — Style Guide

Read this before writing or editing any wiki page. If you are an AI agent (Codex,
Copilot, Claude, etc.) working on this wiki, treat this file as a hard constraint,
not a suggestion. If a prompt you're given conflicts with this file, follow this file
and flag the conflict to the person running you.

## What this wiki is for

Explaining a real tool to a real person trying to get it running or fix a problem.
Not: demonstrating that the software follows good process, reassuring the reader that
downloads are safe, or documenting internal governance concepts for their own sake.

## Voice

Write like a knowledgeable person explaining this tool to another technical person on
a forum (think Level1Techs) — not like a compliance document. Concretely:

1. **Symptom first, then fix.** Lead with what the reader will actually observe, then
   explain the cause or policy behind it, if needed at all.
   - Don't: "Haven 42 blocks public internet server addresses, passwords placed inside
     an address, and unexpected redirects."
   - Do: "If you try to point it at a public IP, it'll refuse — same if you stick a
     password in the URL or the server redirects somewhere unexpected. That's
     intentional, not a bug."

2. **Caveats ride along in the sentence.** They don't get their own paragraph or a
   second sentence restating the same warning.
   - Don't: "Windows may display a warning because this Alpha package is not digitally
     signed. This is expected for invited testing, but you should stop if the file did
     not come from your trusted Haven 42 test source."
   - Do: "Windows will complain it's unsigned — expected, it's an alpha build. Just make
     sure you got the zip from the real releases page, not a random mirror."

3. **State shortcuts and recommendations flatly.** Don't dress a recommendation up as a
   formal UI label repeated in prose ("Choose X · Recommended"). Say which path a normal
   person should take and why, once, plainly.

4. **Keep real specifics.** Actual error text, exact commands, exact ports, exact file
   names stay exact. Don't paraphrase a concrete detail into something vaguer. Equally,
   don't invent a specific detail (an error string, a number) that isn't already sourced
   from the actual behavior — if you don't know it, say so or leave it out.

5. **Use first person / direct address where it adds information, not as flavor.**
   "Heads up —" or "worth knowing:" is fine for a real gotcha. Don't force "I" into
   every sentence just to sound casual.

6. **No marketing adjectives.** Cut "seamless," "powerful," "robust," "smart,"
   "intuitive," "cutting-edge." Describe what the thing does; don't assert a quality
   about it.

7. **Say a thing once.** If you've stated a policy or warning clearly, don't restate it
   in different words two sentences later "just in case." This single habit is
   responsible for most of the bloat in older wiki pages — watch for it specifically.

### Self-check before publishing a page

Would this sentence survive as a reply in a forum thread where someone asked "how do I
get this running" or "why isn't X working"? If a sentence exists only to reassure the
reader that the software is being careful, or restates something already said, cut or
compress it.

## Banned words and phrases

If you write or find these in a user-facing page, replace them:

| Avoid | Use instead |
|---|---|
| "evidence-gated" | explain what actually happens the first time it's used per page ("changes only ship once backed by a passing test/log"); don't use it as an unexplained badge |
| "admission" / "admitted" (file types, agents, etc.) | "allowed" / "supported" |
| "capability availability" / "capability contract" | describe what the feature does; keep the governance term only in engineering pages that are actually about that internal system |
| "· Recommended" / "· Advanced" used mid-sentence in prose | rewrite as a normal sentence; keep the literal label only when quoting an actual UI button |
| repeated "asks permission before downloading" restated 2-3 times per page | say it once |
| "seamless," "powerful," "robust," "smart," "intuitive," "cutting-edge" | cut, or describe the actual behavior |
| passive voice where an active sentence is more natural ("a warning is displayed") | active voice ("Haven 42 shows a warning") |

## Structure rules

- **Prose pages vs. data pages are different things — don't blur them.** If a page is
  fundamentally a table of test results (hardware qualification, benchmark runs, pass/fail
  logs), format it as an actual table or a structured list. Don't narrate data in full
  sentences pretending to be a report. This is what caused ~250 near-duplicate
  `Evidence-Record-<hash>` pages: prose used to represent what should have been rows in a
  table.
- **One page per topic, updated over time — not one page per run.** A new test run, new
  hardware qualification, or new validation pass should add a row to an existing summary
  page (e.g. one `Hardware-Qualification-Results.md` table), not spawn a new wiki page.
  If you're an agent about to create a new page whose name is mostly a hash, a date, or a
  version number, stop — you almost certainly want to append to an existing page instead.
- Raw logs, full evidence dumps, and CI artifacts belong in the code repo (e.g.
  `docs/evidence/`) or in CI, not as wiki pages. The wiki should link to them, not contain
  them.
- Don't rename existing `.md` filenames without updating every internal link and anchor
  that points to them (GitHub wiki links are filename-based).

## Mechanical check

Before merging any wiki change, run a grep for the banned phrases against changed
user-facing pages. Something like:

```bash
#!/usr/bin/env bash
# wiki-style-check.sh — run from the wiki repo root
PATTERNS='evidence-gated|admission|admitted|capability contract|capability availability|· Recommended|· Advanced|seamless|robust|intuitive|cutting-edge'
FILES=$(git diff --name-only main -- '*.md' | grep -v '^Eng-' | grep -v '^Evidence-Record-')

if [ -z "$FILES" ]; then
  echo "No user-facing markdown changed."
  exit 0
fi

HITS=$(grep -niE "$PATTERNS" $FILES)
if [ -n "$HITS" ]; then
  echo "Style check failed — banned phrases found in user-facing pages:"
  echo "$HITS"
  exit 1
fi

echo "Style check passed."
```

Wire this into CI (or just run it by hand before merging a wiki PR) so regressions get
caught automatically instead of noticed months later.

## Review cadence

Nobody is going to manually re-read 400+ pages regularly, and that's fine. Instead:

- Every couple of weeks, pick ~10 random pages and read them out loud. If a sentence
  only exists to reassure the reader the software is being careful, that's the tell.
- Any time a bulk AI-assisted edit touches more than ~3 pages, review a diff after the
  first few pages before letting it continue across the rest. Never let one prompt run
  unattended across the whole wiki — that's how the current wiki ended up with the same
  template applied 400 times with no human checkpoint.
