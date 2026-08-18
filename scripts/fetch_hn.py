#!/usr/bin/env python3
"""
Fetch Hacker News comments and score them as potential discourse antipattern candidates.

Uses heuristics (thread death, flagged status, escalation keywords, etc.) to identify
comments that may represent antipatterns. Outputs a markdown digest of the top candidates.

No external dependencies required -- uses only Python stdlib.
"""

import json
import re
import sys
import os
import html
import time
import threading
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

HN_API = "https://hacker-news.firebaseio.com/v0"
MAX_COMMENTS_OUTPUT = 100
MAX_STORIES = 30
MAX_COMMENTS_PER_STORY = 150
REQUEST_TIMEOUT = 10
# How many levels of ancestor context to include with each comment. One level
# (the immediate parent) is often not enough to judge a reply, because the claim
# being disputed is frequently a level or two further up.
MAX_ANCESTORS = 3
# Per-ancestor character budget in the digest.
ANCESTOR_TRUNCATE = 700

# Patterns that suggest escalation or dismissiveness
ESCALATION_KEYWORDS = [
    r"\bobviously\b",
    r"\bclearly you\b",
    r"\bthat'?s not what i said\b",
    r"\byou clearly\b",
    r"\byou obviously\b",
    r"\byou don'?t understand\b",
    r"\byou'?re missing the point\b",
    r"\bstrawman\b",
    r"\bstraw man\b",
    r"\bmoving the goalposts?\b",
    r"\bgaslighting\b",
    r"\bin bad faith\b",
    r"\bbad faith\b",
    r"\bnice try\b",
    r"\bwell actually\b",
    r"\bwell,? duh\b",
    r"\bimagine thinking\b",
    r"\btell me you\b",
    r"\bdo your (own )?research\b",
    r"\bi can'?t even\b",
    r"\bwhoosh\b",
    r"\br/whoosh\b",
    r"\byou people\b",
    r"\btypical\b",
    r"\bof course you\b",
    r"\bnot surprised\b",
    r"\bwhat a surprise\b",
    r"\bkeep telling yourself\b",
    r"\bwhatever you say\b",
    r"\bsure,? buddy\b",
    r"\bok,? buddy\b",
    r"\bsweet summer child\b",
    r"\bbless your heart\b",
    r"\bthat'?s adorable\b",
    r"\boh honey\b",
]

ESCALATION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in ESCALATION_KEYWORDS]


class RateLimiter:
    """Simple rate limiter that enforces a minimum interval between calls."""

    def __init__(self, max_per_second=2):
        self._min_interval = 1.0 / max_per_second
        self._lock = threading.Lock()
        self._last_call = 0.0

    def wait(self):
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_call = time.monotonic()


_rate_limiter = RateLimiter(max_per_second=2)


def fetch_json(url, retries=3):
    """Fetch JSON from a URL with retries and exponential backoff."""
    for attempt in range(retries):
        try:
            _rate_limiter.wait()
            req = Request(url, headers={"User-Agent": "odap-antipattern-digest/1.0"})
            with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (URLError, HTTPError, TimeoutError) as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                return None


def strip_html(text):
    """Strip HTML tags and decode entities from HN comment text."""
    if not text:
        return ""
    # HN uses <p> for paragraphs
    text = text.replace("<p>", "\n\n")
    # Remove all other HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode HTML entities
    text = html.unescape(text)
    return text.strip()


def count_escalation_matches(text):
    """Count how many escalation keyword patterns match in the text."""
    if not text:
        return 0
    count = 0
    for pattern in ESCALATION_PATTERNS:
        if pattern.search(text):
            count += 1
    return count


def has_quote_then_attack(text):
    """Check if comment quotes someone then responds dismissively.

    strip_html() turns <p> into a blank-line separator, so the reply to a quoted
    line is rarely the very next line -- it is usually separated by one or more
    blank lines. Scan forward past blanks (and past any further quoted lines) to
    find the first line of the actual reply.
    """
    if not text:
        return False
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if not line.strip().startswith(">"):
            continue
        # Walk forward to the first non-blank, non-quote line: the reply itself.
        for candidate in lines[i + 1:]:
            stripped = candidate.strip()
            if not stripped or stripped.startswith(">"):
                continue
            for pattern in ESCALATION_PATTERNS:
                if pattern.search(stripped.lower()):
                    return True
            break
    return False


def fetch_item(item_id):
    """Fetch a single HN item."""
    return fetch_json(f"{HN_API}/item/{item_id}.json")


def fetch_comment_tree(story_item):
    """Fetch comments for a story, returning a flat list of comment items."""
    kid_ids = story_item.get("kids", [])
    if not kid_ids:
        return []

    comments = []
    queue = list(kid_ids)
    # Track depth for each comment
    depth = {kid_id: 1 for kid_id in kid_ids}
    # Cache fetched items to avoid refetching parents. Seed it with the story so
    # that walking up from a top-level comment (whose parent IS the story) is a
    # cache hit rather than a wasted network fetch that only proves it is not a
    # comment.
    item_cache = {story_item["id"]: story_item}

    while queue and len(comments) < MAX_COMMENTS_PER_STORY:
        cid = queue.pop(0)
        item = fetch_item(cid)
        if item and item.get("type") == "comment" and not item.get("deleted"):
            item["_depth"] = depth.get(item["id"], 1)
            item["_story_id"] = story_item["id"]
            item["_story_title"] = story_item.get("title", "")

            # Walk the ancestor chain for context, nearest parent first.
            # BFS guarantees every ancestor was processed (and cached) before this
            # node was dequeued, so this is almost always cache hits and no network.
            ancestors = []
            ancestor_id = item.get("parent")
            # Bound hops, not just collected texts: an ancestor with no text
            # (deleted) does not grow `ancestors`, so without this the walk could
            # keep climbing to the root fetching items it will never use.
            hops = 0
            while ancestor_id and len(ancestors) < MAX_ANCESTORS and hops < MAX_ANCESTORS * 2:
                hops += 1
                try:
                    if ancestor_id in item_cache:
                        ancestor = item_cache[ancestor_id]
                    else:
                        ancestor = fetch_item(ancestor_id)
                        if ancestor:
                            item_cache[ancestor_id] = ancestor

                    # Stop at the story root; only comments carry useful context.
                    if not ancestor or ancestor.get("type") != "comment":
                        break
                    ancestor_text = strip_html(ancestor.get("text", ""))
                    if ancestor_text:
                        ancestors.append(ancestor_text)
                    ancestor_id = ancestor.get("parent")
                except Exception as e:
                    print(f"  Warning: Could not fetch ancestor {ancestor_id}: {e}", file=sys.stderr)
                    break

            if ancestors:
                # Nearest parent first; format_digest reverses for reading order.
                item["_ancestor_texts"] = ancestors
                # Kept for backward compatibility with the previous digest format.
                item["_parent_text"] = ancestors[0]

            # Cache this item too
            item_cache[item["id"]] = item
            comments.append(item)

            # Queue children if we haven't hit the limit
            child_ids = item.get("kids", [])
            for child_id in child_ids:
                depth[child_id] = item["_depth"] + 1
            if len(comments) + len(queue) < MAX_COMMENTS_PER_STORY:
                queue.extend(child_ids)

    return comments


def score_comment(comment):
    """
    Score a comment for antipattern potential. Higher = more likely to be interesting.

    Returns (score, reasons) tuple.
    """
    score = 0
    reasons = []
    text = strip_html(comment.get("text", ""))

    # Skip empty or very short comments
    if len(text) < 20:
        return 0, []

    # NOTE: comments containing links used to score 0 and be dropped entirely.
    # That silently discarded whole classes of documented antipatterns
    # (source-dismissal, refused-source, research-dismissal), which all tend to
    # cite or link something. Links are no longer disqualifying.

    # Dead/flagged comments (strong signal)
    if comment.get("dead"):
        score += 5
        reasons.append("flagged/dead")

    # --- Content signals: what the comment actually says. Weighted highest,
    # because these are the only signals that speak to discourse quality. ---

    keyword_count = count_escalation_matches(text)
    if keyword_count > 0:
        score += keyword_count * 3
        reasons.append(f"{keyword_count} escalation keyword(s)")

    # Quote-then-attack pattern
    if has_quote_then_attack(text):
        score += 4
        reasons.append("quote-then-attack")

    # --- Context signals: thread shape. Deliberately weak. A short comment deep
    # in a thread is a conversational dead end, which is not the same thing as an
    # antipattern; on their own these should not carry a comment into the digest. ---

    kids = comment.get("kids", [])
    depth = comment.get("_depth", 1)
    if not kids and depth >= 3:
        score += 1
        reasons.append(f"thread death at depth {depth}")

    # High reply count relative to depth (contentious)
    if len(kids) >= 5:
        score += 1
        reasons.append(f"{len(kids)} direct replies")

    # Length heuristic: very short replies in deep threads are often dismissive
    if len(text) < 80 and depth >= 2:
        score += 1
        reasons.append("short reply in thread")

    return score, reasons


def format_digest(scored_comments, date_str):
    """Format scored comments into a markdown digest."""
    lines = [
        f"# HN Antipattern Digest - {date_str}",
        "",
        f"Top {len(scored_comments)} candidate comments scored by heuristics.",
        "Review these for potential new antipatterns or examples of existing ones.",
        "",
        "---",
        "",
    ]

    for i, (score, reasons, comment) in enumerate(scored_comments, 1):
        text = strip_html(comment.get("text", ""))
        author = comment.get("by", "[deleted]")
        story_title = comment.get("_story_title", "Unknown")
        depth = comment.get("_depth", 0)
        hn_url = f"https://news.ycombinator.com/item?id={comment['id']}"
        reason_str = ", ".join(reasons)
        # Nearest parent first in storage; reverse so the digest reads top-down
        # (oldest ancestor -> immediate parent -> the comment itself).
        ancestors = list(reversed(comment.get("_ancestor_texts", [])))
        if not ancestors and comment.get("_parent_text"):
            ancestors = [comment["_parent_text"]]

        lines.append(f"### #{i} (score: {score})")
        lines.append("")
        lines.append(f"**Story**: {story_title}")
        lines.append(f"**Author**: {author} | **Depth**: {depth} | **Signals**: {reason_str}")
        lines.append(f"**Link**: {hn_url}")
        lines.append("")

        # Include the ancestor chain so the comment can be judged in context.
        for offset, ancestor_text in enumerate(ancestors):
            if len(ancestor_text) > ANCESTOR_TRUNCATE:
                ancestor_text = ancestor_text[: ANCESTOR_TRUNCATE - 3] + "..."
            levels_up = len(ancestors) - offset
            label = "Parent comment" if levels_up == 1 else f"Ancestor ({levels_up} levels up)"
            lines.append(f"**{label}**:")
            lines.append("> " + ancestor_text.replace("\n", "\n> "))
            lines.append("")

        if ancestors:
            lines.append("**This comment**:")

        lines.append("> " + text.replace("\n", "\n> "))
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    print("Fetching top stories from HN...", file=sys.stderr)
    story_ids = fetch_json(f"{HN_API}/topstories.json")
    if not story_ids:
        print("Failed to fetch top stories.", file=sys.stderr)
        sys.exit(1)

    story_ids = story_ids[:MAX_STORIES]

    # Fetch story items
    print(f"Fetching {len(story_ids)} stories...", file=sys.stderr)
    stories = []
    for sid in story_ids:
        item = fetch_item(sid)
        if item and item.get("kids"):
            stories.append(item)

    print(f"Found {len(stories)} stories with comments.", file=sys.stderr)

    # Fetch and score comments from each story
    all_scored = []
    for i, story in enumerate(stories):
        print(
            f"  [{i+1}/{len(stories)}] Fetching comments for: {story.get('title', '?')[:60]}",
            file=sys.stderr,
        )
        comments = fetch_comment_tree(story)

        for comment in comments:
            score, reasons = score_comment(comment)
            if score > 0:
                all_scored.append((score, reasons, comment))

    # Sort by score descending, take top N
    all_scored.sort(key=lambda x: x[0], reverse=True)
    top = all_scored[:MAX_COMMENTS_OUTPUT]

    print(f"\nScored {len(all_scored)} candidates, outputting top {len(top)}.", file=sys.stderr)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    digest = format_digest(top, date_str)

    # Write to digests directory
    digest_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "digests")
    os.makedirs(digest_dir, exist_ok=True)
    digest_path = os.path.join(digest_dir, f"{date_str}.md")

    with open(digest_path, "w") as f:
        f.write(digest)

    print(f"Digest written to {digest_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
