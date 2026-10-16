# Task List: RDNA2 Refactoring

- [x] **Task 1: Refactor `build-llamacpp-rocm.yml`**
  - Scope: Remove non-RDNA2 targets, clean up target mapping, remove `test-stx-halo`/`test-stx` jobs, and update `create-release` dependencies.
  - Acceptance Criteria: Workflow defaults to `gfx103X`, clean YAML syntax, zero APU runner dependencies.
- [x] **Task 2: Update `test-llamacpp-rocm.yml`**
  - Scope: Default target set to `gfx103X`.
  - Acceptance Criteria: Works seamlessly with release artifacts from Task 1.
- [x] **Task 3: Refactor `docs/manual_instructions.md`**
  - Scope: Strip out non-RDNA2 tables and instructions, retain only `gfx103X-all` and `gfx1030;gfx1031;gfx1032;gfx1034`.
  - Acceptance Criteria: Clear, copy-pasteable build guide for RDNA2 users on Windows and Ubuntu.
- [x] **Task 4: Update `README.md` & Issue Templates**
  - Scope: Update titles, badges, supported card tables (RX 6500XT to RX 6950XT), and RDNA2 performance flags.
  - Acceptance Criteria: Accurate, clean documentation with no dead links or extraneous GPU references.
