---
title: Purity Gatekeeping
---



Dismissing technical choices or tools as inadequate because they use higher-level abstractions rather than lower-level fundamentals.

"Real developers don't need frameworks for that."

"If people actually understood JavaScript, they wouldn't need React."

"Using Tailwind just means someone never learned proper CSS."

"Electron apps are bloated. Native or nothing."

### Why It's Unproductive

Treats modern abstractions as shortcuts for the incompetent rather than legitimate trade-offs. It's tempting because advocating for fundamentals feels like defending craft and expertise, but it conflates yesterday's abstractions with timeless principles while ignoring business context and evolving needs. Shuts down discussion of actual trade-offs like development speed, team skills, or maintenance costs.

## The Better Move

Ask about the constraints that shaped the decision instead of judging the decision itself. Every tool choice involves trade-offs, and the interesting conversation is about which trade-offs matter for a given situation, not whether someone passed your personal purity test.

### Why It's Better

Treats the other person as someone who made a considered decision rather than someone who took a shortcut out of ignorance. That's where you actually learn something.

---

## Examples

**OP**: "We shipped the desktop app using Electron to reuse our web codebase and move faster."<br>
**Antipattern**: "Electron apps are bloated garbage. Real developers build native apps that don't eat 500MB of RAM."<br>
**Better**: "How's the performance been in practice? Electron gets a bad rap but it depends a lot on what the app actually does."

**OP**: "We went with Tailwind for the redesign and it's been great for velocity."<br>
**Antipattern**: "Using Tailwind just means your team never learned proper CSS."<br>
**Better**: "What sold you over plain CSS or something like CSS modules? Curious if the speed gain holds up as the project grows."

**OP**: "New gopher here. What library are people using for HTTP routing in Go?"<br>
**Antipattern**: "You should just use the standard library. It's always worked fine. People who reach for libraries don't understand the language."<br>
**Better**: "The standard library covers a lot, but chi and gorilla/mux are solid if you want middleware chaining out of the box. Depends on how much routing logic you need."
