# Stop and Ask

Six decision classes where Claude MUST stop and put the question to the user before
acting — regardless of any autonomous/proactive output style, plan-approval breadth, or
deadline. A broad instruction ("fix all", "handle it") does not cover these. Each
trigger comes from a real incident in a production research project (2026-08); the
pattern to prevent is *decide → disclose → proceed*, which is honest but still
unilateral.

## The six triggers

1. **Mutating a released or deposited data file in place.** Anything named in a paper's
   Data Records or shipped to collaborators. Requires: explicit user yes, a timestamped
   `.bak` created FIRST, and a dry-run shown before `--apply`. *(Origin: a repair
   script with a semantic bug rewrote 50k rows; recovery depended on a backup that
   existed only by accident.)*

2. **Choosing a semantic rule for real data.** Merge/collapse/tie-break rules
   ("latest wins", "True wins"), field redefinitions, imputation choices. Present the
   options with affected row counts; do not pick a default.

3. **Changing any number that has appeared in a supervisor- or public-facing
   artifact.** Includes sentences about set membership ("district X exits the sample"),
   not just digits. Show before/after, get a yes, and disclose the change in the
   artifact itself — never silently swap.

4. **Irreversible or hard-to-reverse operations without a verified backup.** Deletion,
   overwrite, force-push, history rewrite, remote/published actions. "There's probably
   a copy somewhere" is not a backup; verify it exists and matches first.

5. **Materially divergent interpretations of an instruction.** If two readings change
   different files or publish different numbers, ask — one question costs less than one
   wrong branch.

6. **Setting any verification status by means other than recomputation.** Passport
   statuses, test expectations, "verified" labels. Text substitution never changes a
   status; only a recompute (or a named verifier agent) does, and `last_verified_by`
   must say which. *(Origin: a batch-substituted passport left 5 wrong claims marked
   PASS; the independent verifier caught them.)*

## How to ask

One AskUserQuestion (or a short in-chat question) with: the action, the affected scope
in numbers, the options with one-line consequences, and a recommendation. Then wait. Do
not pre-execute "reversible parts" of a triggered action.

## Mechanical backstops

Rules that depend on in-the-moment judgment fail exactly when judgment does, so pair
this rule with the hooks: `git-guardrails.py`'s protected-outputs guard (blocks
in-place writes to files listed in `.claude/protected-outputs.txt`) and the passport
provenance gate in `.githooks/pre-commit` (fails commits whose changed claims lack
fresh recompute provenance). Hooks are the floor, not the ceiling — absence of a hook
block never implies permission. Mutation scripts default to `--dry-run`; `--apply` is
explicit and creates its own `.bak`.
