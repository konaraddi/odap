#!/usr/bin/env python3
"""
Unit tests for scripts/fetch_hn.py.

Standard library only -- no third-party packages, no network access. Every test
that would otherwise hit the HN API mocks fetch_item instead.

Run from the repo root:

    python -m unittest discover -s tests -v
"""

import importlib.util
import os
import sys
import unittest
from unittest.mock import patch

# The script lives in scripts/ and is not an importable package, so load it by
# path. Importing it is side-effect free: module level is only constants and
# compiled regexes, and main() is behind an __main__ guard.
_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts",
    "fetch_hn.py",
)
_spec = importlib.util.spec_from_file_location("fetch_hn", _SCRIPT)
fetch_hn = importlib.util.module_from_spec(_spec)
sys.modules["fetch_hn"] = fetch_hn
_spec.loader.exec_module(fetch_hn)


class TestStripHtml(unittest.TestCase):
    def test_paragraph_becomes_blank_line(self):
        self.assertEqual(fetch_hn.strip_html("a<p>b"), "a\n\nb")

    def test_tags_removed_and_entities_decoded(self):
        self.assertEqual(fetch_hn.strip_html("<i>x</i> &amp; y"), "x & y")

    def test_hn_quote_marker_is_decoded(self):
        # HN returns user-typed ">" as "&gt;", which the quote detector relies on.
        self.assertTrue(fetch_hn.strip_html("&gt; quoted").startswith(">"))

    def test_empty_and_none(self):
        self.assertEqual(fetch_hn.strip_html(""), "")
        self.assertEqual(fetch_hn.strip_html(None), "")


class TestQuoteThenAttack(unittest.TestCase):
    """Regression tests for the detector that fired twice in 108 days.

    The old implementation looked at the line immediately after a quote line.
    strip_html turns <p> into "\\n\\n", so that position is a blank line and the
    check almost never matched.
    """

    def test_blank_line_between_quote_and_reply(self):
        text = fetch_hn.strip_html("&gt; some claim<p>You clearly don't understand")
        self.assertIn("\n\n", text)  # the exact shape that used to defeat it
        self.assertTrue(fetch_hn.has_quote_then_attack(text))

    def test_reply_on_immediately_following_line(self):
        self.assertTrue(
            fetch_hn.has_quote_then_attack("> some claim\nYou clearly don't understand")
        )

    def test_multiple_blank_lines(self):
        self.assertTrue(
            fetch_hn.has_quote_then_attack("> claim\n\n\n\nwell actually that's wrong")
        )

    def test_consecutive_quote_lines_then_reply(self):
        text = "> line one\n> line two\n\nyou clearly missed it"
        self.assertTrue(fetch_hn.has_quote_then_attack(text))

    def test_quote_with_civil_reply_does_not_match(self):
        text = "> some claim\n\nThat is a fair point, here is the data."
        self.assertFalse(fetch_hn.has_quote_then_attack(text))

    def test_escalation_without_any_quote_does_not_match(self):
        self.assertFalse(fetch_hn.has_quote_then_attack("You clearly don't understand"))

    def test_quote_with_nothing_after_it(self):
        self.assertFalse(fetch_hn.has_quote_then_attack("> a dangling quote\n\n"))

    def test_only_first_reply_paragraph_is_considered(self):
        # An escalation phrase far below an unrelated reply should not count.
        text = "> claim\n\nA neutral first response.\n\nyou clearly are wrong"
        self.assertFalse(fetch_hn.has_quote_then_attack(text))

    def test_empty_input(self):
        self.assertFalse(fetch_hn.has_quote_then_attack(""))
        self.assertFalse(fetch_hn.has_quote_then_attack(None))


class TestCountEscalationMatches(unittest.TestCase):
    def test_counts_distinct_patterns_not_occurrences(self):
        # "strawman" twice is still one distinct pattern.
        self.assertEqual(fetch_hn.count_escalation_matches("strawman strawman"), 1)

    def test_counts_two_distinct_patterns(self):
        self.assertEqual(
            fetch_hn.count_escalation_matches("nice try, that is a strawman"), 2
        )

    def test_case_insensitive(self):
        self.assertEqual(fetch_hn.count_escalation_matches("STRAWMAN"), 1)

    def test_no_match(self):
        self.assertEqual(fetch_hn.count_escalation_matches("a calm reply"), 0)


class TestScoreComment(unittest.TestCase):
    def _comment(self, text, **kw):
        c = {"text": text}
        c.update(kw)
        return c

    def test_very_short_comment_is_rejected(self):
        score, reasons = fetch_hn.score_comment(self._comment("too short"))
        self.assertEqual(score, 0)
        self.assertEqual(reasons, [])

    def test_comment_with_link_is_no_longer_zeroed(self):
        """Links used to force a 0, discarding source-dismissal style comments."""
        text = "you clearly did not read https://example.com/proof before replying"
        score, reasons = fetch_hn.score_comment(self._comment(text))
        self.assertGreater(score, 0)
        self.assertTrue(any("escalation" in r for r in reasons))

    def test_escalation_keyword_weight(self):
        text = "You clearly do not know how any of this works, at all, truly."
        score, _ = fetch_hn.score_comment(self._comment(text, _depth=1))
        self.assertEqual(score, 3)  # one distinct keyword * 3

    def test_content_outweighs_thread_shape(self):
        """A comment with real content signal must outrank a shape-only one."""
        shape_only = self._comment(
            "I think that is probably right, more or less.", _depth=3, kids=[]
        )
        with_content = self._comment(
            "You clearly don't understand what the paper actually measured here.",
            _depth=1,
            kids=[],
        )
        shape_score, _ = fetch_hn.score_comment(shape_only)
        content_score, _ = fetch_hn.score_comment(with_content)
        self.assertGreater(content_score, shape_score)

    def test_shape_only_signals_are_capped_low(self):
        # thread death (1) + short reply (1) = 2, below any single keyword hit (3).
        c = self._comment("Sure, that seems fine to me.", _depth=3, kids=[])
        score, reasons = fetch_hn.score_comment(c)
        self.assertEqual(score, 2)
        self.assertIn("thread death at depth 3", reasons)
        self.assertIn("short reply in thread", reasons)

    def test_direct_replies_signal(self):
        c = self._comment(
            "A perfectly reasonable and sufficiently long comment about things.",
            _depth=1,
            kids=[1, 2, 3, 4, 5],
        )
        score, reasons = fetch_hn.score_comment(c)
        self.assertIn("5 direct replies", reasons)
        self.assertEqual(score, 1)

    def test_quote_then_attack_weight(self):
        text = fetch_hn.strip_html("&gt; your claim<p>nice try, that is a strawman")
        score, reasons = fetch_hn.score_comment({"text": text, "_depth": 1})
        self.assertIn("quote-then-attack", reasons)
        # quote-then-attack (4) + "nice try" + "strawman" (2 * 3) = 10
        self.assertEqual(score, 10)


class TestAncestorChain(unittest.TestCase):
    """fetch_comment_tree should attach ancestor context without extra fetches."""

    STORY = {"id": 1, "type": "story", "title": "A story", "kids": [2]}
    TREE = {
        2: {"id": 2, "type": "comment", "text": "top level", "parent": 1, "kids": [3]},
        3: {"id": 3, "type": "comment", "text": "second level", "parent": 2, "kids": [4]},
        4: {"id": 4, "type": "comment", "text": "third level", "parent": 3, "kids": [5]},
        5: {"id": 5, "type": "comment", "text": "fourth level", "parent": 4},
    }

    def _run(self):
        calls = []

        def fake_fetch_item(item_id):
            calls.append(item_id)
            return dict(self.TREE[item_id]) if item_id in self.TREE else None

        with patch.object(fetch_hn, "fetch_item", side_effect=fake_fetch_item):
            comments = fetch_hn.fetch_comment_tree(dict(self.STORY))
        return comments, calls

    def test_all_comments_returned(self):
        comments, _ = self._run()
        self.assertEqual([c["id"] for c in comments], [2, 3, 4, 5])

    def test_top_level_comment_has_no_ancestors(self):
        comments, _ = self._run()
        top = next(c for c in comments if c["id"] == 2)
        self.assertNotIn("_ancestor_texts", top)

    def test_ancestors_are_nearest_first(self):
        comments, _ = self._run()
        fourth = next(c for c in comments if c["id"] == 4)
        self.assertEqual(fourth["_ancestor_texts"], ["second level", "top level"])

    def test_ancestor_chain_is_capped(self):
        comments, _ = self._run()
        deepest = next(c for c in comments if c["id"] == 5)
        self.assertLessEqual(len(deepest["_ancestor_texts"]), fetch_hn.MAX_ANCESTORS)
        self.assertEqual(
            deepest["_ancestor_texts"][: fetch_hn.MAX_ANCESTORS],
            ["third level", "second level", "top level"][: fetch_hn.MAX_ANCESTORS],
        )

    def test_parent_text_kept_for_backward_compatibility(self):
        comments, _ = self._run()
        third = next(c for c in comments if c["id"] == 3)
        self.assertEqual(third["_parent_text"], "top level")

    def test_ancestor_walk_costs_no_extra_requests(self):
        """Story is seeded into the cache and ancestors are already cached by BFS."""
        comments, calls = self._run()
        self.assertEqual(sorted(calls), [2, 3, 4, 5])
        self.assertEqual(len(calls), len(comments))
        self.assertNotIn(1, calls)  # the story itself is never fetched


class TestAncestorWalkBounds(unittest.TestCase):
    """The hops guard and the per-story cap, neither of which the happy path hits."""

    def test_hops_bound_stops_a_run_of_textless_ancestors(self):
        """Textless ancestors do not grow `ancestors`, so only `hops` ends the climb."""
        # A long chain in which every ancestor above the leaf has empty text.
        story = {"id": 1, "type": "story", "title": "S", "kids": [2]}
        chain = {2: {"id": 2, "type": "comment", "text": "root text", "parent": 1, "kids": [3]}}
        # ids 3..20: textless comments, each the child of the previous.
        for n in range(3, 21):
            chain[n] = {
                "id": n,
                "type": "comment",
                "text": "",
                "parent": n - 1,
                "kids": [n + 1] if n < 20 else [],
            }
        # The leaf carries text so it is scored and its ancestors walked.
        chain[20]["text"] = "the leaf"

        calls = []

        def fake_fetch_item(item_id):
            calls.append(item_id)
            return dict(chain[item_id]) if item_id in chain else None

        with patch.object(fetch_hn, "fetch_item", side_effect=fake_fetch_item):
            comments = fetch_hn.fetch_comment_tree(dict(story))

        leaf = next(c for c in comments if c["id"] == 20)
        # Every ancestor between the leaf and the root is textless, so the walk
        # collects nothing and must be stopped by the hops bound rather than
        # climbing all the way to the story.
        self.assertNotIn("_ancestor_texts", leaf)
        # It must not have walked the whole chain: with MAX_ANCESTORS * 2 hops it
        # can reach at most that many levels up from the leaf.
        self.assertLess(fetch_hn.MAX_ANCESTORS * 2, 18)

    def test_per_story_cap_truncates_traversal(self):
        story = {"id": 1, "type": "story", "title": "S", "kids": list(range(2, 60))}
        tree = {
            n: {"id": n, "type": "comment", "text": f"comment {n}", "parent": 1}
            for n in range(2, 60)
        }

        def fake_fetch_item(item_id):
            return dict(tree[item_id]) if item_id in tree else None

        with patch.object(fetch_hn, "MAX_COMMENTS_PER_STORY", 10), patch.object(
            fetch_hn, "fetch_item", side_effect=fake_fetch_item
        ):
            comments = fetch_hn.fetch_comment_tree(dict(story))

        self.assertEqual(len(comments), 10)

    def test_ancestors_still_correct_when_cap_truncates(self):
        """Truncation stops the whole loop, so no node outlives its cached ancestors."""
        story = {"id": 1, "type": "story", "title": "S", "kids": [2]}
        tree = {}
        for n in range(2, 12):
            tree[n] = {
                "id": n,
                "type": "comment",
                "text": f"level {n}",
                "parent": 1 if n == 2 else n - 1,
                "kids": [n + 1] if n < 11 else [],
            }

        calls = []

        def fake_fetch_item(item_id):
            calls.append(item_id)
            return dict(tree[item_id]) if item_id in tree else None

        with patch.object(fetch_hn, "MAX_COMMENTS_PER_STORY", 5), patch.object(
            fetch_hn, "fetch_item", side_effect=fake_fetch_item
        ):
            comments = fetch_hn.fetch_comment_tree(dict(story))

        self.assertEqual(len(comments), 5)
        deepest = comments[-1]
        self.assertEqual(
            deepest["_ancestor_texts"], ["level 5", "level 4", "level 3"]
        )
        # Still no extra fetches despite the truncation.
        self.assertEqual(len(calls), len(comments))


class TestFormatDigest(unittest.TestCase):
    def _digest(self, comment, score=5, reasons=("test",)):
        return fetch_hn.format_digest([(score, list(reasons), comment)], "2026-08-18")

    def test_ancestors_render_oldest_first_with_labels(self):
        comment = {
            "id": 9,
            "text": "the reply",
            "by": "someone",
            "_depth": 3,
            "_story_title": "A story",
            # storage order is nearest-first
            "_ancestor_texts": ["the parent", "the grandparent"],
        }
        out = self._digest(comment)
        self.assertIn("**Ancestor (2 levels up)**:", out)
        self.assertIn("**Parent comment**:", out)
        self.assertIn("**This comment**:", out)
        # oldest ancestor must appear before the immediate parent
        self.assertLess(
            out.index("the grandparent"), out.index("the parent")
        )
        self.assertLess(out.index("the parent"), out.index("the reply"))

    def test_single_ancestor_is_labelled_parent(self):
        comment = {
            "id": 9,
            "text": "the reply",
            "by": "x",
            "_depth": 2,
            "_story_title": "S",
            "_ancestor_texts": ["only parent"],
        }
        out = self._digest(comment)
        self.assertIn("**Parent comment**:", out)
        self.assertNotIn("levels up", out)

    def test_both_fields_present_prefers_the_ancestor_chain(self):
        """The real production shape: fetch_comment_tree sets both fields."""
        comment = {
            "id": 9,
            "text": "the reply",
            "by": "x",
            "_depth": 3,
            "_story_title": "S",
            "_ancestor_texts": ["the parent", "the grandparent"],
            "_parent_text": "the parent",
        }
        out = self._digest(comment)
        self.assertIn("**Ancestor (2 levels up)**:", out)
        self.assertIn("the grandparent", out)
        # The parent must appear exactly once -- the legacy field must not cause
        # it to be rendered a second time.
        self.assertEqual(out.count("the parent"), 1)

    def test_legacy_parent_text_still_renders(self):
        comment = {
            "id": 9,
            "text": "the reply",
            "by": "x",
            "_depth": 2,
            "_story_title": "S",
            "_parent_text": "legacy parent",
        }
        out = self._digest(comment)
        self.assertIn("**Parent comment**:", out)
        self.assertIn("legacy parent", out)

    def test_no_ancestors_omits_this_comment_header(self):
        comment = {
            "id": 9,
            "text": "orphan reply",
            "by": "x",
            "_depth": 1,
            "_story_title": "S",
        }
        out = self._digest(comment)
        self.assertNotIn("**This comment**:", out)
        self.assertIn("orphan reply", out)

    def test_long_ancestor_is_truncated(self):
        comment = {
            "id": 9,
            "text": "reply",
            "by": "x",
            "_depth": 2,
            "_story_title": "S",
            "_ancestor_texts": ["A" * (fetch_hn.ANCESTOR_TRUNCATE + 500)],
        }
        out = self._digest(comment)
        self.assertIn("...", out)
        self.assertNotIn("A" * (fetch_hn.ANCESTOR_TRUNCATE + 1), out)


if __name__ == "__main__":
    unittest.main()
