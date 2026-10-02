# Enforce a wall-clock timeout in a separate worker

The current module limits output size and derivative evaluations. A slow solver
call still runs inside the caller's process. Add a worker that can be terminated
after a documented wall-clock budget without publishing partial outputs.

Acceptance criteria:

- Simulate a timed-out job and report a distinct failed status.
- Confirm no success manifest or result directory is published.
- Test cancellation and cleanup of staged artifacts.
