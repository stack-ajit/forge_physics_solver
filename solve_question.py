"""
solve_question.py

Interactive FORGE runner with type-aware multi-answer reporting.

Usage:
    python solve_question.py            (interactive menu)
    python solve_question.py Q1         (solve a specific question)
    python solve_question.py all        (solve all)
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))

from src.store.func_store import FunctionStore, Stor2Ind
from src.engine.solver import FORGE_SOLVE
from src.engine.visualizer import render_all_paths, render_compact_paths
from src.engine.html_graph import generate_html

FUNCTIONS_PATH = os.path.join(os.path.dirname(__file__), "data", "functions", "physics_functions.json")
QUESTIONS_PATH = os.path.join(os.path.dirname(__file__), "data", "questions", "kinematics_questions.json")


def load_questions():
    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        return json.load(f)["questions"]


def show_menu(questions):
    print("\n" + "=" * 60)
    print("  FORGE - KINEMATICS QUESTION BANK")
    print("=" * 60)
    for q in questions:
        print(f"\n  [{q['id']}]  {q['title']}")
        print(f"        {q['statement']}")
    print("\n" + "=" * 60)


def solve(question, index):
    print("\n\n" + "#" * 60)
    print(f"  SOLVING {question['id']} : {question['title']}")
    print("#" * 60)
    print(f"\n  QUESTION:\n  {question['statement']}")

    given       = question["given"]
    target      = question["target"]
    unit        = question.get("unit", "")
    wanted_type = question.get("wanted_type")
    given_keys  = set(given.keys())

    print(f"\n  GIVEN:")
    for k, v in given.items():
        print(f"    {k.split('/')[-1]:25s} = {v}")
    print(f"\n  FIND: {target.split('/')[-1]}", end="")
    if wanted_type:
        print(f"  (interpretation requested: {wanted_type})")
    else:
        print("  (no interpretation specified)")

    result = FORGE_SOLVE(given, target, index, wanted_type=wanted_type, verbose=False)

    # ── Show all paths ───────────────────────────────────────
    if result.all_paths:
        print(render_compact_paths(result.all_paths, target, index))
        print(render_all_paths(result.all_paths, target, given_keys, index))
    else:
        print("\n  No derivation path exists from the given information.")

    # ── Report answers (Phase B - type-aware multi-answer) ───
    print("\n" + "=" * 60)
    print("  ANSWERS BY INTERPRETATION")
    print("=" * 60)

    if not result.success:
        print("\n  RESULT: UNSOLVABLE")
        print("  The given information is insufficient to derive the target.")
        print("  FORGE does not guess - it reports honestly.")
    else:
        for v in result.variants:
            is_primary = (v is result.primary)
            tag = "  <= PRIMARY (matches question)" if is_primary else ""
            print(f"\n  [{v.answer_type.upper()}]  {target.split('/')[-1]} = {round(v.value,4)} {unit}{tag}")
            print(f"     via: {v.path.describe(index)}")
            if v.assumptions:
                print(f"     assumptions: {', '.join(v.assumptions)}")

        if len(result.variants) > 1:
            print("\n  NOTE: This question has multiple valid interpretations.")
            print("  Each yields a different but physically correct answer.")
            if wanted_type:
                print(f"  The question asked for '{wanted_type}', shown as PRIMARY above.")
            else:
                print("  No interpretation was specified, so all are reported equally.")

        # primary execution trace
        print("\n" + "-" * 60)
        print("  EXECUTION TRACE (primary answer)")
        print("-" * 60)
        for step in result.trace:
            print(f"\n  Wave t={step.t}")
            for fn in step.fired:
                lbl = index.label_of(fn)
                out = index.output_of(fn)
                if out in step.produced:
                    print(f"    {lbl:30s} -> {out.split('/')[-1]} = {round(step.produced[out],4)}")
        print(f"\n  PRIMARY ANSWER: {target.split('/')[-1]} = {round(result.answer,4)} {unit}")

    # ── HTML graph ───────────────────────────────────────────
    html = generate_html(
        paths=result.all_paths, target=target, given=given_keys,
        index=index, question=question["statement"],
        answer=result.answer, unit=unit
    )
    out_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{question['id']}_graph.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n  Visual graph saved to: output/{question['id']}_graph.html")
    print()


def main():
    fs    = FunctionStore.from_json(FUNCTIONS_PATH)
    index = Stor2Ind(fs)
    questions = load_questions()
    qmap = {q["id"]: q for q in questions}

    if len(sys.argv) > 1:
        qid = sys.argv[1].upper()
        if qid == "ALL":
            for q in questions:
                solve(q, index)
        elif qid in qmap:
            solve(qmap[qid], index)
        else:
            print(f"Question '{qid}' not found. Available: {list(qmap.keys())}")
        return

    show_menu(questions)
    choice = input("\n  Enter question ID (e.g. Q1) or 'all': ").strip().upper()
    if choice == "ALL":
        for q in questions:
            solve(q, index)
    elif choice in qmap:
        solve(qmap[choice], index)
    else:
        print(f"  Invalid choice. Available: {list(qmap.keys())}")


if __name__ == "__main__":
    main()
