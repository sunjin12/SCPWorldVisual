---
name: grill-me
description: "Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions 'grill me'."
---

# Grill Me

## Purpose

Relentlessly interview the user about every aspect of their plan or design until a shared understanding is reached. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one.

## When to Use

- User says "grill me" or "interview me about this plan"
- User wants to stress-test a design or architecture
- User needs help finding gaps in their thinking
- User wants to reach clarity on ambiguous decisions

## Process

### 1. Understand the Plan

First, ask the user to briefly describe their plan or design. If the plan is already in context (e.g., a spec file, a design document), read it thoroughly first. Ask clarifying questions if the scope is unclear.

### 2. Map the Decision Tree

Identify the key decisions embedded in the plan. For each decision, determine:
- What choices exist?
- What are the tradeoffs?
- What downstream decisions depend on this one?

### 3. Interview — One Question at a Time

Ask questions **one at a time**. For each question:

1. **State the question clearly.**
2. **Provide your recommended answer** with reasoning (tradeoffs, risks, alternatives considered).
3. **Wait for the user's response** before moving to the next question.
4. If the user disagrees with your recommendation, explore their preferred direction before continuing.

### 4. Resolve Dependencies

Walk the decision tree in dependency order. Resolve foundational decisions (architecture, data model, technology choices) before surface-level ones (UI details, naming). When a decision is resolved, note it and move to the next dependent question.

### 5. Explore the Codebase When Relevant

If a question can be answered by looking at existing code, **explore the codebase first** before asking the user. For example:
- "Your existing auth service already uses JWT — does this plan need to change that, or build on top of it?"
- "I see you already have a `memory_service.py` — should this new feature reuse it, or does it need a separate store?"

### 6. Summarize and Conclude

When all branches are resolved, provide a concise summary of:
- Decisions made
- Rationale for each
- Any remaining open questions
- Concrete next steps

## Rules

- **One question at a time.** Never batch multiple questions together.
- **Always provide a recommendation.** Don't just ask — give your best answer and explain why.
- **Codebase-first.** If the workspace has relevant code, read it before asking.
- **Be relentless but respectful.** Push back on vague answers. Ask "why" until the reasoning is clear.
- **Stop when done.** Don't invent edge cases just to keep going. When the plan is solid, say so.
- **Keep context.** Remember previous answers and build on them. Don't re-ask resolved questions.
