# The FRACTAL Evaluation Framework

This directory contains the evaluation framework for the FRACTAL multi-agent system. The framework is designed to provide a robust and trustworthy assessment of the work performed by the agent hierarchy, based on the principle of "tool trace as truth."

## Core Principles

1.  **Deterministic Checks First:** The primary method of evaluation is through deterministic, rule-based checks that are objective and repeatable. This includes running tests, linters, and static analysis tools.
2.  **LLM as a Judge of Intent, Not Correctness:** LLM-based evaluations are used sparingly and only to assess alignment with the high-level intent of the project. They are never used as the sole measure of correctness.
3.  **Tool Trace as Truth:** The evaluation is based on the actual output of the tools and the state changes in the environment, not on the agent's self-reported narrative.
4.  **Approval Gates:** The Architect's evaluation of a Feature Lead's work serves as an explicit approval gate before the work is integrated.

## Directory Structure

-   `/EVAL_TEMPLATES`: Contains the templates for different types of evaluations.
-   `/EVAL_RESULTS`: Contains the results of completed evaluations, organized by feature.

## Workflow

1.  When a Feature Lead marks a workstream as `COMPLETE`, the Architect initiates the evaluation process.
2.  The Architect uses the appropriate template from `/EVAL_TEMPLATES` to create an evaluation plan.
3.  The Architect executes the evaluation plan, running all deterministic checks and, if necessary, performing an LLM-based judgment.
4.  The Architect records the results of the evaluation in a new file in `/EVAL_RESULTS`.
5.  Based on the evaluation results, the Architect either approves the work and merges it, or rejects it and provides feedback to the Feature Lead for revision.
