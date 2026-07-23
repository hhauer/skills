---
name: deep-review
description: Use when asked for a thorough senior-level review of a codebase, especially for production readiness, feature completeness, architecture risk, subtle bugs, or spec conformance against design documents.
---

# Deep Review

Performs a senior-level production-readiness review grounded in the codebase's governing specifications.

## Overview

This skill is for reviews that go beyond surface code quality. It checks whether the implementation appears actually deployable, whether core behaviors are wired together at runtime, whether the system matches its specs, and whether there are subtle security, correctness, or operational risks.

The review should answer questions like:

- Is it feature complete or only component-complete?
- Does the runtime wiring match the architecture?
- Are there security or boundary failures?
- Are there spec deviations?
- What would block production deployment?

## When To Use

Use this when the user asks for any of the following:

- a thorough review of the codebase
- a production-readiness or deployment-readiness review
- a senior engineer assessment of architecture and subtle bugs
- a feature-completeness check against specs, proposals, or design docs
- a conformance review against OpenSpec, scaffold docs, or similar source-of-truth artifacts

Do not use this for a normal narrow PR review or for a simple “find one bug” debugging task.

## Review Standard

Default to a code-review mindset with findings first.

- Prioritize bugs, security issues, behavioral regressions, missing implementation, and mismatches with the governing spec.
- Categorize findings by severity.
- Code quality observations that do not affect behavior or deployability should be clearly marked as non-blocking.
- If no findings are discovered, say so explicitly and note residual risks or testing gaps.

## Authority Order

When multiple design sources exist, apply them in this order:

1. The live OpenSpec in `openspec/specs/`
2. The originating scaffold or reference design material
3. README or implementation commentary

If the OpenSpec is explicit, it wins. If the OpenSpec is ambiguous, use the scaffold/reference material. Do not let the current implementation redefine intended behavior.

## Workflow

### 1. Read The Governing Docs First

Before judging the code, inspect the authoritative design artifacts.

At minimum:

- the relevant OpenSpec capability specs
- the proposal/design docs if they describe intended divergences or scope
- any upstream scaffold/reference docs the user identified

Extract:

- required runtime behaviors
- explicit non-goals and intentional divergences
- security and boundary expectations
- lifecycle and deployment expectations

### 2. Map The Runtime Surface

Identify the real runtime entrypoints before reading everything else.

Look for:

- daemon startup and shutdown
- transport inbound and outbound handling
- orchestrator/message loop
- model/provider registration
- handler registration
- background execution paths (scheduled jobs, workers, queues, subagents)
- persistence and logging surfaces

Do not assume a subsystem is operational just because the primitives exist.

### 3. Split The Review Into Parallel Tracks

Review at least these areas:

- spec conformance
- runtime composition and completeness
- security and permission boundaries
- execution-model correctness
- test coverage realism

Use parallel tool calls where possible.

### 4. Run Targeted Deep Passes

For a true deep review, dispatch focused subagents (Agent tool) with targeted questions instead of one vague request.

Recommended passes:

1. Runtime completeness and orchestrator/entrypoint wiring
2. Security posture and boundary enforcement
3. Execution-model correctness — retries, cancellation, concurrency, delegation
4. Test-suite realism if the repository has an unusually strong or unusually weak test story

Give each subagent the specific files to read and a sharply scoped question. Run independent passes in parallel.

### 5. Verify Operational Claims

If the repo claims readiness, run the stated quality gates and report the actual outcomes.

Typical checks:

- full test suite
- lint
- format check
- build or typecheck if relevant

Passing tests do not override architectural or runtime-integration findings.

### 6. Look For These Common Failure Modes

Pay special attention to:

- component-complete but runtime-incomplete systems
- tests that hand-wire behavior absent from production code
- security boundaries enforced only by convention
- spec compliance in helper functions but not in real execution paths
- provider/API compatibility mismatches hidden by mocks
- fail-open behavior when config is missing or ambiguous
- missing or partial operational logging/snapshots/audit trails
- shutdown/retry/cancellation paths that exist on paper but not in runtime wiring

### 7. Produce Findings-First Output

Structure the final review like this:

1. Critical findings
2. High findings
3. Medium findings
4. Low or non-blocking observations
5. Overall deployment assessment

For each finding include:

- what is wrong
- why it matters
- where it is in the code
- whether it blocks production

Keep lists flat. Avoid burying the important issues under commentary.

## Review Heuristics

- Missing runtime wiring is often more serious than messy code.
- A passing suite can still hide a non-runnable system.
- If the system depends on a provider, compare request formatting against official docs when risk is meaningful.
- If a capability exists only in tests and not in production wiring, treat that as incomplete.
- If a security mechanism is enforced in some call paths but bypassable in others, treat it as a security finding.

## Minimum Output Bar

Do not stop at “looks good overall” unless you have actually checked:

- governing specs
- runtime entrypoints
- security boundaries
- quality gates
- at least several likely production paths

If time is limited, say what was not reviewed instead of implying full coverage.
