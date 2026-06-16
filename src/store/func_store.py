"""
src/store/func_store.py
FunctionStore, FuncIndex, Stor2Ind

Now carries semantic metadata:
    answer_type  -- "exact" | "average" | "instantaneous" | "total"
    assumptions  -- list of physical assumptions the equation rests on
"""

from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Dict, List
import json


@dataclass
class Function:
    name:        str
    input:       List[str]
    output:      str
    priority:    int = 99
    label:       str = ""
    answer_type: str = "exact"
    assumptions: List[str] = field(default_factory=list)

    def short(self):
        return self.name.split("(")[0].split("/")[-1]

    def __repr__(self):
        return f"Function({self.label or self.name})"


@dataclass
class FunctionStore:
    functions: List[Function] = field(default_factory=list)

    @classmethod
    def from_json(cls, path: str) -> "FunctionStore":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls(functions=[
            Function(
                name=fn["name"],
                input=fn["input"],
                output=fn["output"],
                priority=fn.get("priority", 99),
                label=fn.get("label", ""),
                answer_type=fn.get("answer_type", "exact"),
                assumptions=fn.get("assumptions", [])
            )
            for fn in data["functions"]
        ])

    @classmethod
    def from_proto(cls, path: str) -> "FunctionStore":
        from src.protos.funt import func_pb2
        proto_store = func_pb2.FunctionStore()
        with open(path, "rb") as f:
            proto_store.ParseFromString(f.read())
        return cls(functions=[
            Function(name=fn.name, input=list(fn.input), output=fn.output)
            for fn in proto_store.functions
        ])

    def get(self, name: str):
        for fn in self.functions:
            if fn.name == name:
                return fn
        return None

    def __len__(self):
        return len(self.functions)

    def __repr__(self):
        return f"FunctionStore({len(self)} functions)"


@dataclass
class FuncIndex:
    i2f:         Dict[str, List[str]] = field(default_factory=dict)
    o2f:         Dict[str, List[str]] = field(default_factory=dict)
    f2i:         Dict[str, List[str]] = field(default_factory=dict)
    f2o:         Dict[str, str]       = field(default_factory=dict)
    priority:    Dict[str, int]       = field(default_factory=dict)
    label:       Dict[str, str]       = field(default_factory=dict)
    answer_type: Dict[str, str]       = field(default_factory=dict)
    assumptions: Dict[str, List[str]] = field(default_factory=dict)

    def funcs_needing(self, var):   return self.i2f.get(var, [])
    def funcs_producing(self, var): return self.o2f.get(var, [])
    def inputs_of(self, fn):        return self.f2i.get(fn, [])
    def output_of(self, fn):        return self.f2o.get(fn, "")
    def priority_of(self, fn):      return self.priority.get(fn, 99)
    def label_of(self, fn):         return self.label.get(fn, fn.split("/")[-1])
    def answer_type_of(self, fn):   return self.answer_type.get(fn, "exact")
    def assumptions_of(self, fn):   return self.assumptions.get(fn, [])

    def __repr__(self):
        return f"FuncIndex({len(self.f2i)} functions, {len(self.i2f)} input-keys)"


def Stor2Ind(fs: FunctionStore) -> FuncIndex:
    """Build FuncIndex from FunctionStore. Called once at startup."""
    i2f         = defaultdict(list)
    o2f         = defaultdict(list)
    f2i         = {}
    f2o         = {}
    priority    = {}
    label       = {}
    answer_type = {}
    assumptions = {}

    for fn in fs.functions:
        f2i[fn.name]         = fn.input
        f2o[fn.name]         = fn.output
        priority[fn.name]    = fn.priority
        label[fn.name]       = fn.label
        answer_type[fn.name] = fn.answer_type
        assumptions[fn.name] = fn.assumptions
        for inp in fn.input:
            i2f[inp].append(fn.name)
        o2f[fn.output].append(fn.name)

    return FuncIndex(
        i2f=dict(i2f), o2f=dict(o2f),
        f2i=f2i, f2o=f2o,
        priority=priority, label=label,
        answer_type=answer_type, assumptions=assumptions
    )
