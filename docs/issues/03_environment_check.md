# Verify portability outside the initial local environment

Run the pinned package on the hosted Python matrix and on a Windows environment.
Compare short-horizon arrays against the accepted numerical tolerance and record
the operating system and installed versions.

Acceptance criteria:

- Store actual run links and outcomes.
- Verify the built wheel can run without the source directory.
- Report numerical differences instead of assuming bitwise identity.
