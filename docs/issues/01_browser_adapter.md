# Add a browser adapter for the validated numerical core

Add a small interface that accepts the same configuration schema and displays
the saved trajectories. Keep the solver independent of HTTP and UI components.

Acceptance criteria:

- Reject the same invalid configurations as the CLI.
- Display parameter settings and solver completion status.
- Preserve raw CSV export and the distinction between plotted and raw samples.
- Add contract tests before linking or embedding the interface in a course.
