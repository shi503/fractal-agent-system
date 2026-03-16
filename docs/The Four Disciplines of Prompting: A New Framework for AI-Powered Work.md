# The Four Disciplines of Prompting: A New Framework for AI-Powered Work

## Introduction: Beyond Chat-Based Prompting

The landscape of AI interaction is rapidly evolving beyond simple chat-based prompting. A new framework, articulated by Nate B. Jones, proposes a shift towards a more disciplined and structured approach to working with AI, especially with the rise of autonomous agents. This new paradigm is built on four key disciplines that move beyond conversational requests to detailed specifications and strategic intent. This document summarizes these four disciplines, drawing from the content of the 'Prompt Kit' and related articles by Nate B. Jones [1][2].

## The Foundational Step: The Human Prompt (Prompt 0)

Before engaging with any of the four disciplines, the framework emphasizes a critical preliminary step: **The Human Prompt**. This is not a prompt given to an AI, but a structured thinking exercise for the user to perform *before* interacting with an AI. The goal is to clarify one's own thoughts and intentions to avoid being led astray by the AI's fluent but potentially misguided outputs. This exercise involves answering seven key questions away from any screen:

1.  **What am I actually trying to accomplish?** (Focus on the outcome, not the task).
2.  **Why does this matter?** (Distinguish between high-stakes and low-stakes tasks).
3.  **What does "done" look like?** (Describe the specific, desired output).
4.  **What does "wrong" look like?** (Identify subtle failure modes).
5.  **What do I already know about this that I haven't written down?** (Capture implicit and institutional knowledge).
6.  **What are the pieces?** (Decompose the task into components).
7.  **What's the hard part?** (Pinpoint areas of uncertainty and judgment).

This initial step ensures that the user, not the AI, is driving the interaction, leading to more accurate and aligned results [1].

## The Four Disciplines of Prompting

The core of the framework is the division of "prompting" into four distinct, compounding disciplines. These move from the tactical level of writing a good prompt to the strategic level of encoding organizational intent into AI-readable formats. The following table summarizes these four disciplines:

| Discipline | Description | Key Artifact | Problem Solved |
| :--- | :--- | :--- | :--- |
| **1. Prompt Craft** | The foundational skill of writing clear, effective prompts. This is the traditional understanding of "prompt engineering" and the starting point for the other disciplines. | Self-Contained Problem Statements | Vague, conversational requests that lead to ambiguous or incomplete AI responses. |
| **2. Context Engineering** | The practice of providing the AI with all necessary information, including personal preferences, institutional knowledge, and project-specific details, to ensure it has the context to produce relevant and accurate work. | Personal Context Document (`CLAUDE.md`) | AI-generated content that is technically correct but lacks the specific nuance, tone, or knowledge of the user or organization. |
| **3. Intent Engineering** | The discipline of defining and encoding the *purpose* behind a task, including goals, values, tradeoffs, and decision boundaries. This ensures that autonomous agents optimize for the desired outcomes, not just measurable outputs. | Intent & Delegation Framework | AI actions that are efficient but counterproductive, such as Klarna's AI saving money but damaging customer satisfaction [2]. |
| **4. Specification Engineering** | The most advanced discipline, involving the creation of detailed, structured documents that an autonomous agent can execute against for extended periods without human intervention. | Specification Document (`SPEC.md`) | The inability to delegate complex, multi-day tasks to AI agents with confidence that the final output will meet all quality and constraint requirements. |

## Conclusion: The Future of AI-Powered Work

The four disciplines of prompting represent a significant evolution in how we interact with AI. As AI models become more powerful and autonomous, the ability to provide clear, structured, and context-rich instructions will be paramount. This framework provides a roadmap for moving beyond simple prompting to a more strategic and effective way of leveraging AI to achieve complex goals. By mastering these disciplines, individuals and organizations can unlock the full potential of AI-powered work.

## References

[1] "State of Prompt Engineering Prompt Kit." Nate Jones. [https://promptkit.natebjones.com/20260225_hfy_promptkit_1](https://promptkit.natebjones.com/20260225_hfy_promptkit_1)

[2] "Klarna saved $60 million and broke its company. The missing layer is what I'm calling intent engineering + 2 prompts to find yours." Nate Jones. [https://natesnewsletter.substack.com/p/klarna-saved-60-million-and-broke](https://natesnewsletter.substack.com/p/klarna-saved-60-million-and-broke)
