"""
scripts/json_to_proto.py

Converts physics_functions.json to physics_functions.pb (binary protobuf).
Run this once after generating func_pb2.py.

Steps:
    1. pip install grpcio-tools
    2. python -m grpc_tools.protoc -I src/protos --python_out=src/protos src/protos/funt/func.proto
    3. python scripts/json_to_proto.py
    4. In main.py, switch to: FunctionStore.from_proto("data/functions/physics_functions.pb")
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.protos.funt import func_pb2

JSON_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "functions", "physics_functions.json"
)
PROTO_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "functions", "physics_functions.pb"
)


def convert():
    # Read JSON
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    # Build protobuf FunctionStore
    store = func_pb2.FunctionStore()
    for fn in data["functions"]:
        func        = store.functions.add()
        func.name   = fn["name"]
        func.output = fn["output"]
        for inp in fn["input"]:
            func.input.append(inp)

    # Write binary .pb file
    # This is what sir meant by ParseFromString(f.read())
    with open(PROTO_PATH, "wb") as f:
        f.write(store.SerializeToString())

    print(f"Done -- {len(data['functions'])} functions written to:")
    print(f"  {PROTO_PATH}")
    print(f"\nNow in main.py you can use:")
    print(f"  FunctionStore.from_proto('data/functions/physics_functions.pb')")


if __name__ == "__main__":
    convert()
