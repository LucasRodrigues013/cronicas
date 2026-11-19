"""Book VI proposed travel atlas, *never* implicit canonical geography.

Exact data lives in bookvi_atlas_PROPOSAL.json (mirrored from story-archive).
Only public named functions may be used in authoring; all results disclose status.
"""
from __future__ import annotations

import heapq
import json
import math
from pathlib import Path

ATLAS_PATH = Path(__file__).with_name("bookvi_atlas_PROPOSAL.json")


def load() -> dict:
    data = json.loads(ATLAS_PATH.read_text(encoding="utf-8"))
    if data.get("status") != "PROPOSTA_GEOGRAFICA_NAO_CANONICA":
        raise ValueError("Atlas must be explicitly labeled NON-CANON")
    return data


def direct_distance(a: str, b: str, *, data: dict | None = None) -> float:
    data = data or load()
    idx = {x["id"]: x for x in data["nodes"]}
    if a not in idx or b not in idx:
        raise KeyError("Unknown place ID")
    x, y = idx[a], idx[b]
    return math.hypot(x["x_km"] - y["x_km"], x["y_km"] - y["y_km"])


def route(start: str, end: str, *, mode: str = "ROAD", data: dict | None = None) -> dict:
    data = data or load()
    valid = {n["id"] for n in data["nodes"]}
    if start not in valid or end not in valid:
        raise KeyError("Unknown place ID")
    if mode not in ("ROAD", "SEA"):
        raise ValueError("Unsupported network mode")
    queue = [(0.0, start)]
    cost = {start: 0.0}
    previous: dict[str, str] = {}
    graph: dict[str, list[tuple[str, float]]] = {n: [] for n in valid}
    for link in data["edges"]:
        if link["mode"] != mode:
            continue
        graph[link["a"]].append((link["b"], link["km"]))
        graph[link["b"]].append((link["a"], link["km"]))
    while queue:
        weight, node = heapq.heappop(queue)
        if weight > cost.get(node, math.inf):
            continue
        if node == end:
            break
        for nxt, km in graph[node]:
            alt = weight + km
            if alt < cost.get(nxt, math.inf):
                cost[nxt] = alt
                previous[nxt] = node
                heapq.heappush(queue, (alt, nxt))
    if end not in cost:
        return {"status": "PROPOSTA", "reachable": False, "distance_km": None, "path": []}
    path = [end]
    while path[-1] != start:
        path.append(previous[path[-1]])
    path.reverse()
    return {"status": "PROPOSTA", "reachable": True, "distance_km": round(cost[end], 2), "path": path}


def travel(start: str, end: str, *, transport: str = "carriage", data: dict | None = None) -> dict:
    data = data or load()
    speeds = {
        "horse": data["assumptions"]["horse_km_day"],
        "carriage": data["assumptions"]["carriage_km_day"],
        "merchant": data["assumptions"]["merchant_km_day"],
        "army": data["assumptions"]["army_km_day"],
        "relay": data["assumptions"]["relay_km_day"],
    }
    if transport not in speeds:
        raise ValueError("Unsupported land transport")
    itinerary = route(start, end, data=data)
    return dict(itinerary, mode=transport,
                days=round(itinerary["distance_km"] / speeds[transport], 2)
                if itinerary["reachable"] else None)


def argos_block(destination: str, *, data: dict | None = None) -> dict:
    data = data or load()
    a = data["assumptions"]
    origin = a["argos_departure_location_id"]
    direct = direct_distance(origin, destination, data=data)
    corridor = direct * a["argos_route_detour_factor"]
    hours = corridor / a["argos_reference_cruise_kmh"] + a["argos_operations_overhead_h"]
    return {
        "status": "PROPOSTA_NAO_VOO_OBSERVADO",
        "origin": origin, "destination": destination,
        "distance_direct_km": round(direct, 2),
        "route_estimate_km": round(corridor, 2),
        "block_minutes": int(math.floor(hours * 60 + 0.5)),
        "peak_D537_kmh_is_not_cruise": True,
        "requires_external_landing_authorization": True,
    }


def city_transit(*, journey: str, data: dict | None = None) -> dict:
    data = data or load()
    speed = data["assumptions"]["urban_tram_speed_kmh"]
    if journey == "old_avenue_end_to_end":
        km, transfer = data["canonical"]["avenida_km"], 0
    elif journey == "old_city_to_new_district":
        km, transfer = data["assumptions"]["full_city_route_proposed_km"], 5
    elif journey == "civic_centre_to_campo":
        km, speed, transfer = data["canonical"]["eixo_aurora_km"], 30, 5
    else:
        raise ValueError("Unknown city journey")
    return {"status": "PROPOSTA_DE_SERVICO_NAO_CIRCULANDO",
            "journey": journey, "distance_km": km,
            "minutes": round(km / speed * 60 + transfer, 1)}


def validate(*, data: dict | None = None) -> dict:
    data = data or load()
    nodes = data["nodes"]
    ids = [n["id"] for n in nodes]
    errors = []
    if len(set(ids)) != len(ids):
        errors.append("Duplicate node IDs")
    for e in data["edges"]:
        if e["a"] not in ids or e["b"] not in ids:
            errors.append("Edge has unknown endpoint")
            continue
        if not math.isfinite(e["km"]) or e["km"] <= 0:
            errors.append("Nonpositive or nonfinite edge")
        if e["km"] + 1e-6 < direct_distance(e["a"], e["b"], data=data):
            errors.append("Edge shorter than its straight line")
    c = data["canonical"]
    if abs(c["eixo_urbano_km"] + c["eixo_rural_km"] - c["eixo_aurora_km"]) > 1e-6:
        errors.append("Eixo Aurora urban+rural inconsistent")
    if abs(direct_distance("TA", "CA", data=data) - c["campo_straight_km"]) > 1e-6:
        errors.append("Campo straight-line inconsistent")
    if route("TA", "TH", data=data)["distance_km"] != 320:
        errors.append("Thalor anchor 320km proposal regressed")
    if route("TA", "CV", data=data)["distance_km"] != 545:
        errors.append("Calderva anchor 545km proposal regressed")
    for item in data["examples"]:
        destination = item["id"]
        if argos_block(destination, data=data)["block_minutes"] != item["argos_block_min"]:
            errors.append("ARGOS forecast desynchronized at " + destination)
        if abs(route("TA", destination, data=data)["distance_km"] - item["road_km"]) > 1e-6:
            errors.append("Land route desynchronized at " + destination)
    if c["argos_certified_cruise_kmh"] is not None:
        errors.append("Uncertified ARGOS cruise must remain null")
    if data["status"] != "PROPOSTA_GEOGRAFICA_NAO_CANONICA":
        errors.append("Proposal status was removed")
    return {"status": "VALIDATED_AS_PROPOSAL" if not errors else "REJECTED",
            "errors": errors, "node_count": len(nodes), "edge_count": len(data["edges"]),
            "canon_promoted": False}
