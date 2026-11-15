# ResearchGPT V2 implementation instructions

- Read `docs/PROGRESS.md` first and at the beginning of every phase.
- Work only on `feature/evidence-pipeline-integration`; stop if another branch is active.
- Treat `../researchgpt-pipeline` and `../ResearchGPT`, their branches, tracked files and history as read-only.
- Never claim a passing test that was not executed. Distinguish fixtures, mocks, live models and real documents.
- Preserve research baselines, stable paper/chunk identity, source provenance, attribution and evaluation history.
- Do not push, merge, create pull requests, or run the full 60-paper experiment without explicit approval.
- Make focused local commits at tested checkpoints. Do not commit secrets, corpora, PDFs, indexes or weights.
- Update progress after each phase with commands, outcomes, blockers, last completed commit and next action.
- Work as the sole implementation agent.
