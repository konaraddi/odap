---
title: Condescending Reveal
---



Framing a correction or disagreement as "bad news" or revelatory knowledge the other person lacks, positioning yourself as the educator.

- "I may have bad news for you on how compilers typically work."
- "You might want to sit down for this..."
- "Hate to break it to you, but..."
- "Someone should probably tell you that..."

## Why It's Unproductive

Treats disagreement as ignorance rather than a difference in perspective or priorities. The "let me educate you" framing is condescending and makes the other person defensive before they've even heard the point. Often happens when someone sees an opportunity to demonstrate expertise, but the superior tone damages the conversation more than the information helps it.

## The Better Move

Skip the buildup and just share what you know. If someone's wrong about something, the correction lands better when you lead with the information itself rather than performing a reveal. You can still disagree or correct, just drop the "brace yourself" framing and engage directly.

### Why It's Better

Puts the focus on the substance instead of on the social dynamic of who knows more. The other person hears the information rather than the condescension.

---

## Examples

**OP**: "IDK how everyone else feels about it, but a non-deterministic 'compiler' is the last thing I need."<br>
**Antipattern**: "I may have bad news for you on how compilers typically work."<br>
**Better**: "Modern compilers already have non-deterministic aspects (optimization heuristics, instruction scheduling). The concern with LLMs is probably more about unpredictable correctness than non-determinism per se."

**OP**: "Your phone is definitely listening to your conversations. I talked about hiking boots with a friend and got ads for them an hour later."<br>
**Antipattern**: "Hate to break it to you, but that's not how any of this works."<br>
**Better**: "It's actually weirder than that. Your friend probably searched for boots, and the ad network inferred you two are connected. No mic needed when the behavioral data is that good."

**OP**: "We should just rewrite our CUDA kernels in HIP so we're not locked into Nvidia."<br>
**Antipattern**: "Someone should probably tell you what HIP actually is before you go down that road."<br>
**Better**: "HIP covers the runtime API side, but the kernels are the hard part since the architectures are genuinely different. Hipify helps but it's not a drop-in swap. Depends on how much custom kernel work you have."
