# PROJECT PLAN REFERENCE — MANDATORY

A complete engineering plan for this project is provided in the project repository as a dedicated plan file.

## Mandatory Rule

Treat the project plan file as the **primary source of truth for the entire implementation**.

Before starting ANY stage, task, feature, refactor, bug fix, or architectural change:

1. Locate and read the current project plan file.
2. Review the sections relevant to the task you are about to perform.
3. Check the current implementation against the plan.
4. Identify the applicable:

   * architecture rules
   * interfaces
   * data models
   * configuration requirements
   * simulation rules
   * routing rules
   * metrics definitions
   * testing requirements
   * acceptance criteria
   * prohibited actions

5. Implement the requested work according to the plan.

## Refer to the Plan Regularly

Do NOT read the plan only once at the beginning of the project.

Re-read the relevant parts of the plan:

* before starting every stage
* before modifying an existing architectural component
* before changing an interface or function signature
* before changing configuration
* before modifying simulation behavior
* before changing routing logic
* before adding a new metric
* before changing experiment behavior
* before performing significant refactoring
* whenever an implementation decision is ambiguous

The plan must remain a **continuously referenced specification**, not merely an initial document.

## Plan vs. Existing Code

When the existing code and the plan disagree:

1. Determine whether the code or the plan is intended to be authoritative for the current stage.
2. Do NOT silently choose a new design.
3. Prefer the plan unless there is a demonstrated implementation error, contradiction, or missing requirement.
4. If the plan contains an inconsistency, document it clearly.
5. Make the smallest correction necessary.
6. Update the relevant documentation if the implementation intentionally deviates from the plan.

Never silently invent architectural rules that are not in the plan.

## Before Coding

For every task, explicitly perform this mental checklist:

**PLAN**
→ What does the project plan require?

**CURRENT CODE**
→ What has already been implemented?

**INTERFACES**
→ What existing contracts must remain compatible?

**DEPENDENCIES**
→ What modules may this component depend on?

**TESTS**
→ What tests are required or affected?

**ACCEPTANCE**
→ What does the plan define as "done" for this task?

Only then implement the change.

## Stage Discipline

Implement **one project stage at a time**.

For the current stage:

1. Read the stage requirements from the plan.
2. Inspect the relevant repository files.
3. Implement only the required scope.
4. Run focused tests after logical units.
5. Run the full test suite after completing the stage.
6. Verify every acceptance criterion from the plan.
7. Review the git diff.
8. Update documentation if required.
9. Only then consider the stage complete.

Do NOT automatically begin the next stage unless explicitly instructed.

## Do Not Override the Plan for Convenience

Do not:

* simplify away required functionality
* add unplanned dependencies
* restructure modules unnecessarily
* change interfaces merely because another design looks cleaner
* remove tests because they are inconvenient
* change simulation assumptions without documenting it
* change metric definitions
* change experimental conditions
* fabricate missing behavior
* invent expected results

The goal is to implement the project described by the plan, not a different project that happens to solve a similar problem.

## Research Integrity

This project is a research simulation.

Therefore:

* Never fabricate numerical results.
* Never hard-code experimental outcomes.
* Never claim an algorithm performed better without running the simulation.
* Preserve reproducibility.
* Preserve identical conditions for fair algorithm comparisons.
* Distinguish assumptions from measured results.
* Use the exact metric definitions in the plan.
* Use the exact simulation rules in the plan unless a documented correction is required.

## Important Project-Specific Rules

Always preserve the plan's core architectural principles:

* routing strategies remain interchangeable
* the energy model remains replaceable
* topology remains structurally static
* dead nodes are represented by state rather than removed from the topology
* packet paths remain immutable
* simulation parameters use the plan's configuration naming
* visualization remains separate from simulation
* metrics are explicitly passed from the simulator
* experiments do not modify core simulation behavior
* deterministic seeds are used for reproducibility

## End-of-Task Verification

Before reporting completion, re-check the relevant plan section and verify:

* implementation matches the specification
* required files exist
* required interfaces exist
* acceptance criteria are satisfied
* tests were actually executed
* no unrelated changes were introduced
* git diff contains only intended changes

Then report:

* what was implemented
* files changed
* tests run
* test results
* plan requirements satisfied
* any deviations from the plan
* any remaining issues

## Critical Instruction

The plan file should be treated as a **living engineering contract**.

Refer to it repeatedly throughout development.

Do not rely on memory of the plan from an earlier prompt or earlier context. Always consult the actual file when making implementation decisions.
