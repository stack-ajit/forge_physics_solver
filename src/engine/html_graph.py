"""
src/engine/html_graph.py

Generates an interactive HTML visualization of all derivation paths.
Produces a standalone .html file the user can open in any browser.

Each path is rendered as a flow diagram:
    given variables -> equations -> intermediate results -> target
"""

from __future__ import annotations
from typing import List
from src.store.func_store import FuncIndex
from src.engine.graph import Path


def _short(var: str) -> str:
    return var.split("/")[-1]


def generate_html(
    paths:    List[Path],
    target:   str,
    given:    set,
    index:    FuncIndex,
    question: str,
    answer,
    unit:     str
) -> str:
    """Build a complete standalone HTML page visualizing all paths."""

    short_target = _short(target)
    given_chips = "".join(
        f'<span class="chip given">{_short(g)}</span>' for g in given
    )

    path_blocks = []
    for i, path in enumerate(paths):
        selected = (i == 0)
        badge = '<span class="badge sel">SELECTED · shortest</span>' if selected else ''
        node_html = []

        # starting givens
        node_html.append('<div class="row">')
        for g in given:
            node_html.append(f'<div class="node given-node">{_short(g)}</div>')
        node_html.append('</div>')

        for step, fn in enumerate(path.funcs, 1):
            inputs  = [_short(x) for x in index.inputs_of(fn)]
            output  = _short(index.output_of(fn))
            formula = index.label_of(fn)

            node_html.append('<div class="arrow">&#8595;</div>')
            node_html.append(f'<div class="eq">{formula}</div>')
            node_html.append('<div class="arrow">&#8595;</div>')
            cls = "target-node" if output == short_target else "result-node"
            node_html.append(f'<div class="row"><div class="node {cls}">{output}</div></div>')

        block = f'''
        <div class="path {'selected' if selected else ''}">
            <div class="path-head">PATH {i+1} &nbsp; <span class="len">{path.length} equations</span> {badge}</div>
            <div class="flow">{''.join(node_html)}</div>
        </div>
        '''
        path_blocks.append(block)

    answer_html = (
        f'<div class="answer success">ANSWER &nbsp; {short_target} = {round(answer,4)} {unit}</div>'
        if answer is not None
        else '<div class="answer fail">UNSOLVABLE &mdash; insufficient information</div>'
    )

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FORGE - {short_target}</title>
<style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{
        font-family: 'Segoe UI', system-ui, sans-serif;
        background: #0f1117;
        color: #e6e9ef;
        padding: 32px;
        line-height: 1.5;
    }}
    h1 {{ font-size: 22px; color: #7ee8a2; margin-bottom: 6px; }}
    .question {{
        background: #1a1d27;
        border-left: 3px solid #58a6ff;
        padding: 14px 18px;
        border-radius: 6px;
        margin: 16px 0 24px;
        color: #c9d1d9;
    }}
    .given-bar {{ margin-bottom: 24px; }}
    .chip {{
        display:inline-block; padding: 4px 12px; border-radius: 14px;
        font-size: 13px; margin: 2px 4px; background:#243; color:#7ee8a2;
    }}
    .target-label {{ color:#ffa657; font-weight:600; }}
    .paths {{ display:flex; flex-wrap:wrap; gap:20px; }}
    .path {{
        background:#161922; border:1px solid #2a2f3a;
        border-radius:10px; padding:18px; min-width:220px;
    }}
    .path.selected {{ border-color:#238636; box-shadow:0 0 0 1px #238636; }}
    .path-head {{ font-size:14px; font-weight:600; margin-bottom:14px; color:#f0f6fc; }}
    .len {{ color:#8b949e; font-weight:400; font-size:12px; }}
    .badge {{ font-size:11px; padding:2px 8px; border-radius:8px; }}
    .badge.sel {{ background:#0d3320; color:#7ee8a2; border:1px solid #238636; }}
    .flow {{ display:flex; flex-direction:column; align-items:center; }}
    .row {{ display:flex; gap:8px; flex-wrap:wrap; justify-content:center; }}
    .node {{
        padding:8px 14px; border-radius:8px; font-size:13px; font-weight:500;
        margin:2px;
    }}
    .given-node {{ background:#1f3a2e; color:#7ee8a2; border:1px solid #2d5a44; }}
    .result-node {{ background:#1e2a44; color:#79c0ff; border:1px solid #2d4a7a; }}
    .target-node {{ background:#3a2a1a; color:#ffa657; border:1px solid #6e4a22; font-weight:700; }}
    .eq {{
        background:#241a2e; color:#d2a8ff; border:1px solid #4a3a5a;
        padding:6px 12px; border-radius:6px; font-family:monospace;
        font-size:13px; margin:2px;
    }}
    .arrow {{ color:#58a6ff; font-size:18px; line-height:1; margin:3px 0; }}
    .answer {{
        margin-top:28px; padding:16px 22px; border-radius:8px;
        font-size:18px; font-weight:700; text-align:center;
    }}
    .answer.success {{ background:#0d3320; color:#7ee8a2; border:1px solid #238636; }}
    .answer.fail {{ background:#2d1117; color:#f97583; border:1px solid #6e2232; }}
</style>
</head>
<body>
    <h1>FORGE &mdash; Forward Reasoning Graph Engine</h1>
    <div class="question">{question}</div>
    <div class="given-bar">
        <strong>Given:</strong> {given_chips}
        &nbsp;&nbsp; <span class="target-label">Find: {short_target}</span>
    </div>
    <h2 style="font-size:16px;margin-bottom:14px;color:#8b949e;">
        {len(paths)} derivation path(s) found
    </h2>
    <div class="paths">{''.join(path_blocks)}</div>
    {answer_html}
</body>
</html>'''

    return html
