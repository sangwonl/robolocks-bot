from __future__ import annotations

import math

from robolocks import AimAt, BattleState, FireIfSolution, MoveTo, OrderLike, ScanArc, run_bot


IDEAL_RANGE = 24.0
MIN_RANGE = 15.0
MAX_RANGE = 34.0
SCAN_WIDTH_DEG = 165.0
FIRE_THRESHOLD = 0.35
OBSTACLE_BUFFER = 7.0
PATROL_RADIUS = 10.0


def on_tick(state: BattleState) -> list[OrderLike]:
    own = state.own_unit
    enemy = state.contacts.closest_enemy()

    if enemy is None:
        return [
            ScanArc(direction=sweep_heading(state.tick, own.turret_heading), width=SCAN_WIDTH_DEG),
            MoveTo(patrol_point(state)),
        ]

    orders: list[OrderLike] = [
        AimAt(enemy.position),
        ScanArc(direction=own.turret_heading, width=SCAN_WIDTH_DEG),
    ]

    if own.can_fire:
        orders.append(FireIfSolution(min_hit_chance=FIRE_THRESHOLD))

    move_target = choose_move_target(state, enemy)
    if move_target is not None:
        orders.append(MoveTo(move_target))

    return orders


def choose_move_target(state: BattleState, enemy) -> dict[str, float] | None:
    own = state.own_unit
    dx = own.position.x - enemy.position.x
    dy = own.position.y - enemy.position.y
    distance = max(math.hypot(dx, dy), 0.001)
    away_x = dx / distance
    away_y = dy / distance

    if distance < MIN_RANGE:
        target = {
            "x": enemy.position.x + away_x * IDEAL_RANGE,
            "y": enemy.position.y + away_y * IDEAL_RANGE,
        }
    elif distance > MAX_RANGE:
        target = enemy.position
    else:
        orbit = 1.0 if (state.tick // 180) % 2 == 0 else -1.0
        target = {
            "x": enemy.position.x + away_x * IDEAL_RANGE + (-away_y) * orbit * 8.0,
            "y": enemy.position.y + away_y * IDEAL_RANGE + away_x * orbit * 8.0,
        }

    return avoid_near_obstacles(state, target)


def avoid_near_obstacles(state: BattleState, target) -> dict[str, float]:
    own = state.own_unit
    push_x = 0.0
    push_y = 0.0

    for obstacle in state.contacts.obstacles:
        dx = own.position.x - obstacle.position.x
        dy = own.position.y - obstacle.position.y
        distance = max(math.hypot(dx, dy), 0.001)
        danger = obstacle.radius + OBSTACLE_BUFFER
        if distance < danger:
            strength = (danger - distance) / danger
            push_x += (dx / distance) * strength * 10.0
            push_y += (dy / distance) * strength * 10.0

    return {
        "x": target.x + push_x if hasattr(target, "x") else target["x"] + push_x,
        "y": target.y + push_y if hasattr(target, "y") else target["y"] + push_y,
    }


def patrol_point(state: BattleState) -> dict[str, float]:
    center = state.map.center
    phase = state.tick / 120.0
    return {
        "x": center.x + math.cos(phase) * PATROL_RADIUS,
        "y": center.y + math.sin(phase) * PATROL_RADIUS * 0.65,
    }


def sweep_heading(tick: int, fallback_heading: float) -> float:
    return fallback_heading + math.sin(tick / 45.0) * 70.0


run_bot(on_tick)
