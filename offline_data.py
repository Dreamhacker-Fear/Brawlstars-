"""Offline map/projectile data loader and deterministic dodge planner.

This module consumes only local JSON fixtures. It has no game-client connector.
Run: python offline_scenarios.py
Test: python -m unittest discover -s tests
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "brawler_data"


def _read_json(filename):
    with (DATA / filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_maps():
    raw = _read_json("maps.json")
    if not isinstance(raw, dict):
        raise ValueError("maps.json must be an object")
    maps = {key: value for key, value in raw.items() if not key.startswith("_")}
    for map_id, arena in maps.items():
        if not isinstance(arena, dict):
            raise ValueError("map %r must be an object" % map_id)
        for field in ("width", "height", "walls", "hazards"):
            if field not in arena:
                raise ValueError("map %r missing %s" % (map_id, field))
        if float(arena["width"]) <= 0 or float(arena["height"]) <= 0:
            raise ValueError("map dimensions must be positive")
        for wall in arena["walls"]:
            if any(float(wall.get(k, 0)) < 0 for k in ("x", "y", "width", "height")):
                raise ValueError("wall coordinates and dimensions cannot be negative")
            if float(wall.get("width", 0)) <= 0 or float(wall.get("height", 0)) <= 0:
                raise ValueError("wall width and height must be positive")
        for hazard in arena["hazards"]:
            if float(hazard.get("radius", 0)) <= 0:
                raise ValueError("hazard radius must be positive")
    return maps


def load_projectiles():
    raw = _read_json("projectiles.json")
    if not isinstance(raw, dict):
        raise ValueError("projectiles.json must be an object")
    result = {key: value for key, value in raw.items() if not key.startswith("_")}
    for projectile_id, spec in result.items():
        for field in ("speed", "radius", "lifetime", "splash_radius", "gravity"):
            if field not in spec:
                raise ValueError("projectile %r missing %s" % (projectile_id, field))
        if float(spec["speed"]) <= 0 or float(spec["radius"]) <= 0 or float(spec["lifetime"]) <= 0:
            raise ValueError("projectile speed, radius and lifetime must be positive")
        if float(spec["splash_radius"]) < 0:
            raise ValueError("splash_radius cannot be negative")
    return result


def load_scenarios():
    raw = _read_json("scenarios.json")
    if not isinstance(raw, dict) or not isinstance(raw.get("scenarios"), list):
        raise ValueError("scenarios.json must contain a scenarios list")
    return raw["scenarios"]


def _inside_wall(x, y, radius, wall):
    # Circle-vs-rectangle overlap.
    nearest_x = min(max(x, wall["x"]), wall["x"] + wall["width"])
    nearest_y = min(max(y, wall["y"]), wall["y"] + wall["height"])
    return math.hypot(x - nearest_x, y - nearest_y) < radius


def plan_dodge(scenario, arena, horizon=1.0, steps=20, directions=24):
    """Return the lowest-cost normalized direction for one synthetic scenario."""
    player = scenario["player"]
    px, py = float(player["x"]), float(player["y"])
    speed, radius = float(player["speed"]), float(player["radius"])
    if speed <= 0 or radius <= 0 or horizon <= 0 or steps < 1 or directions < 4:
        raise ValueError("invalid planner parameters")

    projectiles = scenario.get("projectiles", [])
    best_direction, best_cost = (0.0, 0.0), float("inf")
    dt = horizon / steps
    for index in range(directions + 1):
        if index == directions:
            dx, dy = 0.0, 0.0  # include standing still as a candidate
        else:
            angle = math.tau * index / directions
            dx, dy = math.cos(angle), math.sin(angle)
        cost = 0.0
        for step in range(1, steps + 1):
            t = step * dt
            x = px + dx * speed * t
            y = py + dy * speed * t
            if x < radius or y < radius or x > arena["width"] - radius or y > arena["height"] - radius:
                cost += 100.0
            for wall in arena["walls"]:
                if _inside_wall(x, y, radius, wall):
                    cost += 100.0
            for hazard in arena["hazards"]:
                distance = math.hypot(x - hazard["x"], y - hazard["y"])
                if distance < hazard["radius"] + radius:
                    cost += float(hazard.get("cost", 1.0)) * (1.0 + (hazard["radius"] + radius - distance) / max(1.0, hazard["radius"]))
            for shot in projectiles:
                sx = float(shot["x"]) + float(shot["vx"]) * t
                sy = float(shot["y"]) + float(shot["vy"]) * t + 0.5 * float(shot.get("gravity", 0.0)) * t * t
                danger = radius + float(shot.get("radius", 5)) + float(shot.get("splash_radius", 0))
                if t <= float(shot.get("lifetime", horizon)) and math.hypot(x - sx, y - sy) < danger:
                    cost += 80.0
        # Small tie-breaker: avoid needless movement when risk is equivalent.
        cost += math.hypot(dx, dy) * 0.001
        if cost < best_cost:
            best_direction, best_cost = (dx, dy), cost
    return {"direction": best_direction, "cost": best_cost}
