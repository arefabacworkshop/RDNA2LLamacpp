# Implementation Plan: RDNA2 Refactoring & Stripping

## Overview
Transform the repository from a generic multi-architecture build matrix into a focused, highly reliable build pipeline dedicated strictly to AMD RDNA2 (`gfx103X`: `gfx1030`, `gfx1031`, `gfx1032`, `gfx1034`) GPUs on Windows and Ubuntu.

## Architecture Decisions
- **Target Consolidation**: Default target is `gfx103X`, which maps to all discrete RDNA2 variants (`gfx1030;gfx1031;gfx1032;gfx1034`). Sub-architectures can also be built individually if specified.
- **Excise Self-Hosted APU Runners**: Remove `test-stx-halo` and `test-stx` so builds and releases never hang waiting for private hardware.
- **Preserve Proven Ingestion & Packaging**: Retain the exact dynamic tarball version detection logic and DLL/kernel library harvesting routines.

## Task List

### Phase 1: Core CI Workflow Streamlining
- [ ] Task 1.1: Refactor inputs, defaults, and matrix setup in `build-llamacpp-rocm.yml` to target `gfx103X`.
- [ ] Task 1.2: Simplify Windows & Ubuntu build jobs (target mapping and tarball download).
- [ ] Task 1.3: Remove `test-stx-halo` and `test-stx` jobs and unblock `create-release`.

### Checkpoint: Workflow Verification
- [ ] Verify YAML syntax and dependency graph of `build-llamacpp-rocm.yml`.

### Phase 2: Secondary Workflows & Docs
- [ ] Task 2.1: Update `test-llamacpp-rocm.yml` default inputs to `gfx103X`.
- [ ] Task 2.2: Rewrite `docs/manual_instructions.md` focusing strictly on RDNA2.
- [ ] Task 2.3: Update `README.md` and issue templates to reflect RDNA2 focus and performance flags.

### Checkpoint: Complete Verification
- [ ] Ensure 0 broken links and complete consistency across all project files.
