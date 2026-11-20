"""te のテスト。実行: python3 -m unittest discover -s plugins/thought-experiments/tests

実セッション（issue #30、ryo-morimoto/thought-experiments の記録）で起きた失敗を、te が
それぞれ検出できるかを中心に確かめる。ネットワークには接続しない。
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "skills/running-thought-experiments/scripts"
sys.path.insert(0, str(SCRIPTS))

import te  # noqa: E402
from telib import core, rules, schema, store, views  # noqa: E402


def run(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = te.main(list(args))
    return code, out.getvalue(), err.getvalue()


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class Experiment(unittest.TestCase):
    """A temporary experiment directory with helpers to add events."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.d = Path(self._tmp.name) / "exp"
        self.assertEqual(run("init", str(self.d), "--id", "t")[0], 0)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def add(self, kind: str, payload: dict, author: str = "claude", ok: bool = True) -> tuple[int, str, str]:
        r = run("add", str(self.d), kind, "--json", json.dumps(payload), "--author", author)
        if ok:
            self.assertEqual(r[0], 0, r[2])
        return r

    def source(self, sid: str, text: str = "the official text says alpha beta", quote: str | None = None) -> None:
        f = self.d / "notes" / f"{sid}.txt"
        f.write_text(text, encoding="utf-8")
        args = ["source", "add", str(self.d), sid, "--file", str(f), "--title", sid]
        if quote:
            args += ["--quote", quote, "--page", "1"]
        self.assertEqual(run(*args)[0], 0)

    def stage_a(self, holder: dict | None = None) -> None:
        self.add("frame", {"question": "Q", "goal": "G", "terms": [{"term": "t", "reading": "r"}],
                           "mode": "destructive", "flaw": "none found"})
        self.source("rep")
        self.add("prior_answer", {"sources": ["rep"], "found": True})
        for rid, opp in (("R1", False), ("R2", True), ("R3", False)):
            self.add("rival", {"rid": rid, "text": f"rival {rid}", "is_opposite": opp, "would_reject_if": "x"})
        self.add("holder", holder or {"rival": "R1", "sources": ["rep"]})
        self.add("prediction", {"distribution": {"R1": 0.6, "R2": 0.3, "R3": 0.1}, "by_whom": "practitioner"})
        self.add("probe", {"scenario": {"fixed": "a", "varied": "b"}, "varied": ["b"], "result": "r",
                           "verdicts": {"R1": {"status": "weakened"}}})

    def operations(self) -> None:
        for v, verdict in (("c", {"R1": {"status": "eliminated"}}), ("e", {"R2": {"status": "supported"}})):
            self.add("operation", {"scenario": {"fixed": "a", "varied": v}, "varied": [v], "result": "r", "verdicts": verdict})

    def fresh_attack(self, lens: str = "method") -> dict:
        self.assertEqual(run("brief", str(self.d), "--lens", lens)[0], 0)
        brief = sorted((self.d / "briefs").glob(f"*-{lens}.md"))[-1]
        reply = self.d / "notes" / "reply.md"
        reply.write_text("P1 is secondhand", encoding="utf-8")
        self.assertEqual(run("brief", str(self.d), "--record-response", brief.name, str(reply))[0], 0)
        resp = brief.with_name(brief.stem + ".response.md")
        attack = {"reviewer": "fresh", "lens": lens,
                  "brief": {"file": f"briefs/{brief.name}", "sha256": sha(brief)},
                  "response": {"file": f"briefs/{resp.name}", "sha256": sha(resp)},
                  "objections": [{"text": "P1 secondhand", "target": "premise", "response": "restrict", "reason": "checked"}]}
        self.add("attack", attack, author=f"reviewer:{lens}")
        return attack

    def conclude(self, label: str = "empirical-checked", citation: dict | None = None, answer: str = "R2") -> None:
        cit = citation or {"source": "rep", "level": "primary"}
        self.add("conclusion", {"answer": "A", "answer_rival": answer,
                                "premises": [{"pid": "P1", "text": "fact", "label": label, "citations": [cit]}]})

    def state(self, rerun: bool = False):
        return te._load(self.d, rerun=rerun)

    def errors(self, rerun: bool = False) -> list[str]:
        _, ctx, errs = self.state(rerun)
        return errs + [e["id"] for e in rules.check(store.load_rules(), ctx)["errors"]]

    def warnings(self) -> list[str]:
        _, ctx, _ = self.state()
        return [w["id"] for w in rules.check(store.load_rules(), ctx)["warnings"]]

    def stage(self) -> str:
        _, ctx, _ = self.state()
        return rules.next_step(store.load_rules(), ctx)["stage"]


class SchemaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.s = store.load_schema()

    def ev(self, **kw) -> dict:
        return {"id": 1, "v": 1, "at": "2026-11-21T10:00:00+09:00", "author": "claude", **kw}

    def test_valid_rival(self):
        self.assertEqual(schema.validate(self.ev(kind="rival", rid="R1", text="t", would_reject_if="x"), self.s), [])

    def test_unknown_field_and_bad_author(self):
        errs = schema.validate(self.ev(kind="rival", rid="R1", text="t", would_reject_if="x", colour="red", author="me"), self.s)
        self.assertTrue(any("unknown field 'colour'" in e for e in errs))
        self.assertTrue(any("author" in e for e in errs))

    def test_missing_would_reject_if(self):
        errs = schema.validate(self.ev(kind="rival", rid="R1", text="t"), self.s)
        self.assertTrue(any("would_reject_if" in e for e in errs))

    def test_unsupported_keyword_fails_loudly(self):
        with self.assertRaises(ValueError):
            schema.validate({}, {"oneOf": []})


class AddTest(Experiment):
    def test_ids_are_assigned_and_reserved_fields_refused(self):
        self.add("frame", {"question": "Q", "goal": "G", "terms": [{"term": "t", "reading": "r"}], "mode": "constructive", "flaw": "f"})
        code, _, err = self.add("rival", {"id": 9, "rid": "R1", "text": "t", "would_reject_if": "x"}, ok=False)
        self.assertEqual(code, 2)
        self.assertIn("te assigns them", err)
        events, _ = store.read_events(self.d)
        self.assertEqual([e["id"] for e in events], [1])

    def test_holder_for_unknown_rival_is_refused(self):
        code, _, err = self.add("holder", {"rival": "R9", "strawman": True}, ok=False)
        self.assertEqual(code, 1)
        self.assertIn("unknown rival", err)

    def test_truncated_log_is_reported(self):
        (self.d / "events.jsonl").write_text('{"id": 1', encoding="utf-8")
        _, _, errs = self.state()
        self.assertTrue(any("truncated" in e for e in errs))


class FoldTest(Experiment):
    def test_verdicts_correction_and_supersede(self):
        self.stage_a()
        self.operations()
        st, _, _ = self.state()
        self.assertEqual(st["rivals"]["R1"]["status"], "eliminated")
        # correction overlays new values; the log keeps the original
        self.add("correction", {"target": {"event": 9}, "what": "R1 was not eliminated", "why": "misread",
                                "replace": {"verdicts": {"R1": {"status": "weakened"}}}})
        st, _, _ = self.state()
        self.assertEqual(st["rivals"]["R1"]["status"], "weakened")
        raw = [e for e in store.read_events(self.d)[0] if e["id"] == 9][0]
        self.assertEqual(raw["verdicts"]["R1"]["status"], "eliminated")
        # supersede takes the event out of the state
        self.add("supersede", {"target": 9, "why": "operation redone"})
        st, _, _ = self.state()
        self.assertEqual(st["rivals"]["R1"]["status"], "weakened")  # only the probe's verdict remains
        self.assertEqual([v["event"] for v in st["rivals"]["R1"]["verdicts"]], [8])

    def test_frame_supersedes_for_rescoping(self):
        self.add("frame", {"question": "wide", "goal": "G", "terms": [{"term": "t", "reading": "r"}], "mode": "destructive", "flaw": "f"})
        self.add("frame", {"question": "narrow", "goal": "G", "terms": [{"term": "t", "reading": "r"}], "mode": "destructive", "flaw": "f", "supersedes": 1})
        st, _, _ = self.state()
        self.assertEqual(st["frame"]["question"], "narrow")


class StagesTest(Experiment):
    def test_progression_to_done(self):
        self.assertEqual(self.stage(), "A")
        self.stage_a()
        self.assertEqual(self.stage(), "B")
        self.operations()
        self.assertEqual(self.stage(), "C")
        self.fresh_attack()
        self.conclude()
        self.assertEqual(self.stage(), "D")
        self.add("review", {"by_whom": "user", "text": "known result", "value": {"novelty": "low"}})
        self.add("close", {"state": "concluded"})
        self.assertEqual(self.stage(), "done")
        self.assertEqual(self.errors(), [])

    def test_prior_answer_claim_without_evidence_does_not_pass(self):
        # A real run skipped the prior-answer search; writing "searched" with nothing behind it must not pass.
        self.add("frame", {"question": "Q", "goal": "G", "terms": [{"term": "t", "reading": "r"}], "mode": "destructive", "flaw": "f"})
        self.add("prior_answer", {"found": True, "summary": "I looked"})
        _, ctx, _ = self.state()
        step = rules.next_step(store.load_rules(), ctx)
        self.assertTrue(any("prior_answer" in m["message"] for m in step["missing"]))


class KnownFailuresTest(Experiment):
    def test_attack_written_as_fresh_without_artifacts_is_not_accepted(self):
        # A fork wrote its own attack and could label it fresh. Without brief/response files it must not count.
        self.stage_a()
        self.operations()
        self.add("attack", {"reviewer": "fresh", "lens": "method",
                            "objections": [{"text": "o", "target": "premise", "response": "bar", "reason": "r"}]})
        self.conclude()
        self.assertEqual(self.stage(), "C")

    def test_tampered_brief_is_an_error(self):
        self.stage_a()
        self.operations()
        attack = self.fresh_attack()
        (self.d / attack["brief"]["file"]).write_text("rewritten after the fact", encoding="utf-8")
        self.assertIn("artifacts-match", self.errors())

    def test_self_attack_warns(self):
        self.stage_a()
        self.operations()
        self.add("attack", {"reviewer": "self", "lens": "own", "objections": [{"text": "o", "target": "inference", "response": "bar", "reason": "r"}]})
        self.assertIn("self-attack", self.warnings())
        self.conclude()
        self.assertEqual(self.stage(), "C")
        # a decision by Claude does not count; only the user's does
        self.add("decision", {"what": "accept", "accepts": 11})
        self.assertEqual(self.stage(), "C")
        self.add("decision", {"what": "no subagents here; accept the self attack", "accepts": 11}, author="user")
        self.assertEqual(self.stage(), "D")

    def test_strawman_cannot_be_eliminated_silently(self):
        # The holder was missing for the attacked rival in a real run.
        self.stage_a(holder={"rival": "R2", "sources": ["rep"]})
        self.operations()  # eliminates R1, which has no holder
        self.assertIn("eliminate-needs-holder", self.errors())

    def test_flagged_strawman_passes_with_warning(self):
        self.stage_a(holder={"rival": "R1", "strawman": True, "strongest_held": "the held view"})
        self.operations()
        self.add("holder", {"rival": "R3", "sources": ["rep"]})
        self.assertNotIn("eliminate-needs-holder", self.errors())
        self.assertIn("strawman", self.warnings())

    def test_secondhand_fact_needs_primary(self):
        # 6.01 億円/人 was taken from a manual quoting the guideline: secondary, without the primary.
        self.stage_a()
        self.operations()
        self.fresh_attack()
        self.conclude(citation={"source": "rep", "level": "secondary"})
        self.assertIn("checked-needs-primary", self.errors())

    def test_secondary_with_obtained_primary_passes(self):
        self.stage_a()
        self.source("guideline")
        self.operations()
        self.fresh_attack()
        self.conclude(citation={"source": "rep", "level": "secondary", "primary_of": "guideline"})
        self.assertNotIn("checked-needs-primary", self.errors())

    def test_secondhand_value_in_an_operation_warns(self):
        # Found by migrating the life-value record: 6.01 億円/人 came from a sabo document quoting
        # the R6 guideline, which was never obtained, and it drove two operations, not a premise.
        self.stage_a()
        run("source", "add", str(self.d), "guideline-r6", "--url", "http://127.0.0.1:9/r6.pdf")
        self.source("sabo")
        self.add("operation", {"scenario": {"fixed": "a", "varied": "value"}, "varied": ["value"], "result": "r",
                               "verdicts": {"R1": {"status": "weakened"}},
                               "sources": [{"source": "sabo", "level": "secondary", "primary_of": "guideline-r6"}]})
        self.assertIn("operation-secondhand", self.warnings())

    def test_unobtainable_source_cannot_be_checked(self):
        # Knutson et al. 2019 could not be fetched; premises citing it must stay unverified.
        self.stage_a()
        code, out, _ = run("source", "add", str(self.d), "paywalled", "--url", "http://127.0.0.1:9/paper.pdf")
        self.assertEqual(code, 1)
        self.assertIn("obtained=none", out)
        self.operations()
        self.fresh_attack()
        self.conclude(citation={"source": "paywalled", "level": "primary"})
        self.assertIn("unobtainable-is-unverified", self.errors())

    def test_post_hoc_prediction(self):
        self.stage_a()
        self.operations()
        self.add("prediction", {"distribution": {"R2": 1.0, "R1": 0.0}, "by_whom": "me, after the fact"})
        self.assertIn("no-post-hoc-prediction", self.errors())

    def test_numbers_drift_from_scripts(self):
        self.stage_a()
        (self.d / "scripts" / "calc.py").write_text(
            "import json, os, pathlib\npathlib.Path(os.environ['TE_OUTPUTS'], 'n.json').write_text(json.dumps({'n': 42}))\n", encoding="utf-8")
        self.assertEqual(run("run", str(self.d))[0], 0)
        self.assertNotIn("outputs-reproduce", self.errors(rerun=True))
        (self.d / "outputs" / "n.json").write_text('{"n": 41}', encoding="utf-8")
        self.assertIn("outputs-reproduce", self.errors(rerun=True))

    def test_adopting_an_eliminated_rival(self):
        self.stage_a()
        self.operations()
        self.fresh_attack()
        self.conclude(answer="R1")
        self.assertIn("answer-rival-survives", self.errors())

    def test_unanswered_objection_blocks_stage_c(self):
        self.stage_a()
        self.operations()
        a = self.fresh_attack()
        self.add("attack", {**a, "objections": [{"text": "unanswered", "target": "conclusion"}]}, author="reviewer:method")
        self.conclude()
        _, ctx, _ = self.state()
        step = rules.next_step(store.load_rules(), ctx)
        self.assertEqual(step["stage"], "C")


class SourcesTest(Experiment):
    def test_quote_verified_against_text(self):
        self.source("a", text="Line one.\nThe   value is 601 million yen per person.", quote="value is 601 million yen")
        self.source("b", text="Something else entirely.", quote="value is 601 million yen")
        src = store.read_sources(self.d)
        self.assertTrue(src["a"]["quotes"][0]["verified"])
        self.assertFalse(src["b"]["quotes"][0]["verified"])
        self.assertIn("quotes-verified", self.warnings())

    def test_raw_copies_are_git_ignored(self):
        self.source("a")
        self.assertIn("*", (self.d / "sources/raw/.gitignore").read_text(encoding="utf-8"))
        self.assertTrue(any(p.name.startswith("a.") for p in (self.d / "sources/raw").iterdir()))


class ScoreTest(Experiment):
    def test_brier(self):
        self.stage_a()
        self.operations()
        self.fresh_attack()
        self.conclude(answer="R2")
        s = core.score(self.state()[0])
        # (0.6-0)^2 + (0.3-1)^2 + (0.1-0)^2 = 0.36 + 0.49 + 0.01
        self.assertAlmostEqual(s["brier"], 0.86)
        self.assertEqual(s["p_answer"], 0.3)

    def test_no_score_without_answer(self):
        self.stage_a()
        self.operations()
        self.fresh_attack()
        self.add("conclusion", {"answer": "undecidable", "answer_rival": None,
                                "premises": [{"pid": "P1", "text": "t", "label": "argued"}]})
        self.assertIsNone(core.score(self.state()[0]))


class ViewsTest(Experiment):
    def test_brief_leaves_out_history_and_eliminated_rivals(self):
        self.stage_a()
        self.operations()
        st, _, _ = self.state()
        text = views.brief(st, store.load_instructions()["lens"][0])
        self.assertNotIn("rival R1", text)          # eliminated
        self.assertNotIn("would_reject_if", text)   # the author's own criteria
        self.assertNotIn("practitioner", text.split("## What to return")[0].replace("You are a practitioner", ""))
        self.assertIn("primary source", text)

    def test_render_and_argdown(self):
        self.stage_a()
        self.operations()
        self.fresh_attack()
        self.conclude()
        code, out, _ = run("render", str(self.d), "--lang", "ja")
        self.assertEqual(code, 0)
        self.assertIn("## 対立仮説", out)
        self.assertIn("eliminated", out)
        code, out, _ = run("render", str(self.d), "--argdown")
        self.assertIn("[R1]: rival R1 #eliminated", out)
        self.assertIn("----", out)


class VersionTest(unittest.TestCase):
    def test_lock_roundtrip_and_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / "te.lock"
            self.assertEqual(run("lock", str(lock), "--repo", "https://example.invalid/plugins")[0], 0)
            self.assertEqual(run("version", "--verify", str(lock))[0], 0)
            lock.write_text(lock.read_text(encoding="utf-8").replace(store.bundle_sha256(), "0" * 64), encoding="utf-8")
            self.assertEqual(run("version", "--verify", str(lock))[0], 1)


class DataTest(unittest.TestCase):
    def test_rules_name_only_known_predicates_and_instructions(self):
        rl, instr = store.load_rules(), store.load_instructions()
        for section in ("stage", "invariant", "warning"):
            for entry in rl[section]:
                for req in entry.get("requires", [entry]):
                    self.assertIn(req["pred"], rules.PREDICATES, req)
        for stage in rl["stage"]:
            for sid in stage.get("show", []):
                self.assertIn(sid, instr["show"])


if __name__ == "__main__":
    unittest.main()
