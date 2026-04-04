# odap Repository Guidelines

## Mission

This repository helps improve online discourse by identifying antipatterns in conversation and providing constructive alternatives. The goal is to foster more productive, friendly, and cooperative dialogue on platforms like Reddit, Twitter, TikTok, and elsewhere.

## How People Use This

1. **Self-improvement**: Reading patterns to recognize and improve their own discourse habits
2. **Constructive response**: Politely linking to patterns when they see antipatterns in discussions
3. **Observer learning**: Understanding what makes conversations go sideways

### What Success Looks Like

When someone gets linked to a pattern, ideally:
- They understand the issue without feeling attacked
- The conversation gets back on track
- Other participants learn from the example

## What Qualifies as an Antipattern

An antipattern is a common conversational move that:
- **Sounds reasonable** on the surface but derails productive discussion
- **Happens frequently** in online discourse
- **Has clear alternatives** that keep conversations constructive
- **Isn't just annoying** - it actively damages dialogue quality

Not every bad behavior is an antipattern. Focus on subtle, widespread patterns that people often don't realize they're doing.

## Pattern Structure

Each pattern document should follow this structure:

### 1. Frontmatter
```yaml
---
slug: pattern-name
title: Pattern Name
---
```

### 2. The Pattern
Brief description of what the antipattern looks like, followed by 3-4 generic examples.

**Guidelines:**
- Keep examples short and recognizable
- Use quotes for clarity
- Focus on the structure/form, not specific topics
- Show variety in how the pattern manifests

### 3. Why It's Unproductive
Explain what this pattern does to the conversation and why people fall into it.

**Guidelines:**
- Assume good intent - these are usually unconscious habits
- Acknowledge the human element (ego, defensiveness, social positioning)
- Keep psychology light - no pseudo-science
- Be empathetic but clear about impact
- Weave in why people do this (the ego/identity aspect)
- Avoid using "you" - it feels accusatory (use "it signals" or "this communicates" instead)
- Length: 2-3 sentences max

### 4. The Better Move
1-2 sentences of prose explaining the **principle** - the shift in thinking or approach someone should make. This is not sample dialogue. It's the transferable idea that applies in any context.

**Guidelines:**
- State the move plainly and directly
- No hedging or filler
- Should be memorable enough that someone could apply it without examples

### 5. Why It's Better
Brief explanation of why the alternative approach is more effective.

**Guidelines:**
- Connect to the conversation's goals
- Be concise - 1-2 sentences
- Focus on practical benefits

### 6. Examples
2-3 full exchanges at the bottom of each pattern, each showing OP / Antipattern / Better.

**Guidelines:**
- Exchanges should feel like real internet comments, not scripted dialogue
- The "Better" response can be blunt, casual, or skeptical - it just engages with substance
- No therapist-speak ("I appreciate your perspective", "That's a valid point")
- Keep each line to 1-2 sentences - real comments are brief
- Topics should be varied and neutral (tech, science, everyday things)
- Can draw from real comments in `digests/` (anonymized and condensed)

**Example format:**
```markdown
---

## Examples

**OP**: "New study shows that getting 7-8 hours of sleep improves cognitive performance."
**Antipattern**: "Well duh, anyone could have told you that."
**Better**: "Makes sense. Were there any surprising findings about sleep quality vs. quantity?"

**OP**: "Research confirms that exercise reduces anxiety."
**Antipattern**: "We didn't need a study to know this."
**Better**: "Good to have data backing up the intuition. Was there a threshold where it stopped helping?"
```

## Tone & Voice Guidelines

### Always
- **Assume good intent** - people usually don't realize they're doing these things
- **Stay respectful** - readers may have just been linked here for doing this pattern
- **Be empathetic** - acknowledge why these patterns are tempting
- **Stay constructive** - focus on solutions, not shame
- **Keep it concise** - people won't read walls of text

### Never
- Don't be preachy or condescending
- Don't use academic jargon
- Don't overexplain the psychology
- Don't make people feel stupid
- Don't use aggressive language
- Don't use em dashes (—) in prose - they're associated with AI writing

### Voice
- Direct and clear
- Slightly informal (this is for everyday internet discourse)
- Helpful, not lecturing
- Like a thoughtful friend pointing something out

## Length Guidelines

- **The Pattern**: 1 sentence description + 3-4 example quotes
- **Why It's Unproductive**: 2-3 sentences
- **The Better Move**: 1-2 sentences of prose (the principle, not sample quotes)
- **Why It's Better**: 1-2 sentences
- **Examples**: 2-3 full exchanges (OP / Antipattern / Better)

Total page length: Aim for something readable in under 60 seconds.

## Examples: Good vs Bad Pattern Descriptions

### ❌ Bad: Too Aggressive
"This obnoxious pattern makes you look like an arrogant jerk who values being right over actual discussion."

### ✅ Good: Constructive
"Treats confirmation as worthlessness. Makes the person sharing feel foolish for thinking evidence matters. Signals that you value being right over learning what's true."

---

### ❌ Bad: Too Academic
"This pattern exhibits status-seeking behavior rooted in epistemic superiority complexes and defensive attribution biases."

### ✅ Good: Accessible
"Frames correction as humiliation. Makes the other person defensive before they've even heard the point."

---

### ❌ Bad: Too Vague
"Don't do this because it's not nice."

### ✅ Good: Specific
"Turns agreement into validation theater. Suggests the conversation is about being right rather than exploring ideas."

## Creating New Patterns

### Process
1. Identify a pattern you see repeatedly in online discourse
2. Check if it's truly an antipattern (see criteria above)
3. Draft the pattern using the structure template
4. Test the tone - would you feel okay being linked to this page?
5. Ensure alternatives are concrete and genuinely helpful

### Common Mistakes When Writing Patterns

**Example quotes must be self-contained.** Each quote at the top of a pattern page is often the first thing a reader sees. It must make sense on its own without any surrounding context. If a quote only works when you already know what conversation it's responding to, it's not ready.

- Bad: `"People said the same thing about calculators."` (Said what? About what?)
- Good: `"Worried about AI-generated code? Should I credit my linter as a co-author too?"` (The concern and the dismissal are both in the quote.)

**"Why It's Unproductive" should use concrete examples, not abstract ones.** Ground explanations in the same scenarios the quotes set up. Don't introduce new abstract comparisons the reader hasn't seen yet.

**Keep language plain in "The Better Move."** Avoid corporate or technical phrasing. "Where the analogy breaks down" beats "the delta from what came before." Write it how you'd say it to a friend.

**Read the whole page as a first-time visitor.** Someone may land on this page after being linked to it mid-argument. They're possibly defensive. Every sentence should hold up for that reader, not just for someone browsing the catalog.

**Check existing patterns before writing.** There are 30+ patterns already. Read through the `docs/patterns/` directory to make sure the new pattern isn't already covered or a minor variation of something that exists.

### Naming Patterns
- Use descriptive, memorable names
- Keep them neutral, not judgmental
- Examples: "hindsight-dismissal" not "being-a-know-it-all"

## Mining Digests for Antipatterns

### What Digests Are

The `digests/` directory contains raw, anonymized comment snippets collected from online discourse (Reddit, Twitter, etc.), organized by date. They're source material for identifying new patterns.

### How to Mine Them

Read through digests looking for recurring conversational moves that:
- Appear across multiple digests/threads (not one-off bad behavior)
- Are distinct from the 30+ existing patterns in `docs/patterns/`
- Meet the antipattern criteria already in this document (sounds reasonable, frequent, has alternatives, damages dialogue)

### What to Report When Proposing Candidates

For each candidate pattern:
- A proposed name (neutral, descriptive)
- A 1-2 sentence description of the move
- 2-3 supporting quotes from digests (with dates)
- Why it's distinct from existing patterns
- A quick gut-check: is this subtle enough? (Blatant rudeness isn't an antipattern)

### Common Pitfalls When Mining

- Don't propose patterns that are just topic-specific versions of existing ones (e.g., a tech-specific credential-gatekeeping is still credential-gatekeeping)
- Don't confuse a bad opinion with a bad conversational move
- A single spicy comment isn't a pattern; look for the structural move that repeats

## Repository Philosophy

The internet doesn't have to be hostile. Most people want to have good conversations - they just fall into patterns that work against that goal. By naming these patterns and offering alternatives, we help people recognize and adjust these habits.

This isn't about winning arguments or proving you're smarter. It's about making online spaces a bit more pleasant and productive for everyone.
