import os
import sys
import json

app_root = r"D:\Application\local-chain-app\LocalChain_AI_System"
if app_root not in sys.path:
    sys.path.insert(0, app_root)

from subsystem_rag.knowledge_graph.device_knowledge_graph import TOPOLOGY_KNOWLEDGE_SSOT

mapping = {}
for d in TOPOLOGY_KNOWLEDGE_SSOT.values():
    for s in d.get("subsystems", {}).values():
        for a in s.get("assemblies", {}).values():
            for cid, cdata in a.get("components", {}).items():
                mapping[cid] = cdata["name_vn"]

with open(os.path.join(app_root, "frontend_test", "component_map.json"), "w", encoding="utf-8") as f:
    json.dump(mapping, f, ensure_ascii=False, indent=4)

print("Exported component mapping successfully.")
