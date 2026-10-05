# Repo rules for agents

- **Committing.** When the user says to commit (e.g. "commit this run", "let's
  commit"), commit immediately. Do not ask for confirmation, do not re-run
  verification, and do not gate on scope — unless the user explicitly asks for
  verification first.

- **Scratch space.** When creating temporary scripts prefer nesting under `.tmp/` —
  create a sub-folder `.tmp/{task}` rather than creating a new top level directory
  `.tmp-{task}`.

- **Plans.** Keep plan documents in the repo-root `plans/` folder, one file per plan
  named for its subject (e.g. `plans/templates-reorg.md`). Don't put plans in the
  directory they describe; once a plan is executed, delete it or fold what still
  matters into the relevant `README.md`/`AGENTS.md`.
  