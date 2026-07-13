from __future__ import annotations

import math

from robolocks import AimAt, BattleState, FireIfSolution, MoveTo, OrderLike, ScanArc, run_bot


# Wall Runner
#
# This bot first probes east until movement stalls, treats that as the first
# wall, then drives a clockwise lap with that wall on its right side. Because the
# current SDK does not expose field bounds directly, it learns wall coordinates
# from contact/stall behavior and keeps a target offset from the learned wall.

SCAN_WIDTH_DEG = 170.0
FIRE_THRESHOLD = 0.35
PROBE_AHEAD_M = 80.0
FOLLOW_AHEAD_M = 18.0
WALL_OFFSET_M = 8.0
STALL_EPS_M = 0.12
STALL_TICKS_TO_WALL = 18
OBSTACLE_CLEARANCE_M = 8.0
OBSTACLE_PUSH_M = 16.0

PHASE_PROBE = "probe"
PHASE_FOLLOW = "follow"

WALL_EAST = 0
WALL_NORTH = 1
WALL_WEST = 2
WALL_SOUTH = 3

phase = PHASE_PROBE
wall = WALL_EAST
wall_marks: dict[int, float] = {}
last_position: tuple[float, float] | None = None
stall_ticks = 0


def on_tick(state: BattleState) -> list[OrderLike]:
    global phase, wall, last_position, stall_ticks

    own = state.own_unit
    enemy = state.contacts.closest_enemy()
    moved = movement_since_last_tick(own.position.x, own.position.y)

    orders: list[OrderLike] = [
        ScanArc(direction=own.turret_heading, width=SCAN_WIDTH_DEG),
    ]
    if enemy:
        orders.append(AimAt(enemy.position))
        if own.can_fire:
            orders.append(FireIfSolution(min_hit_chance=FIRE_THRESHOLD))

    if moved < STALL_EPS_M:
        stall_ticks += 1
    else:
        stall_ticks = max(0, stall_ticks - 2)

    if phase == PHASE_PROBE:
        if stall_ticks >= STALL_TICKS_TO_WALL:
            wall_marks[WALL_EAST] = own.position.x
            wall = WALL_EAST
            phase = PHASE_FOLLOW
            stall_ticks = 0
        target = {"x": own.position.x + PROBE_AHEAD_M, "y": own.position.y}
    else:
        if stall_ticks >= STALL_TICKS_TO_WALL:
            mark_wall(wall, own.position.x, own.position.y)
            wall = (wall + 1) % 4
            stall_ticks = 0
        target = follow_wall_target(own.position.x, own.position.y, wall)

    orders.append(MoveTo(avoid_obstacles(state, target)))
    return orders


def movement_since_last_tick(x: float, y: float) -> float:
    global last_position
    if last_position is None:
        last_position = (x, y)
        return 999.0
    px, py = last_position
    last_position = (x, y)
    return math.hypot(x - px, y - py)


def mark_wall(wall_id: int, x: float, y: float) -> None:
    if wall_id == WALL_EAST:
        wall_marks[WALL_EAST] = max(wall_marks.get(WALL_EAST, x), x)
    elif wall_id == WALL_NORTH:
        wall_marks[WALL_NORTH] = max(wall_marks.get(WALL_NORTH, y), y)
    elif wall_id == WALL_WEST:
        wall_marks[WALL_WEST] = min(wall_marks.get(WALL_WEST, x), x)
    else:
        wall_marks[WALL_SOUTH] = min(wall_marks.get(WALL_SOUTH, y), y)


def follow_wall_target(x: float, y: float, wall_id: int) -> dict[str, float]:
    if wall_id == WALL_EAST:
        wall_x = wall_marks.get(WALL_EAST, x + WALL_OFFSET_M)
        return {"x": wall_x - WALL_OFFSET_M, "y": y + FOLLOW_AHEAD_M}
    if wall_id == WALL_NORTH:
        wall_y = wall_marks.get(WALL_NORTH, y + WALL_OFFSET_M)
        return {"x": x - FOLLOW_AHEAD_M, "y": wall_y - WALL_OFFSET_M}
    if wall_id == WALL_WEST:
        wall_x = wall_marks.get(WALL_WEST, x - WALL_OFFSET_M)
        return {"x": wall_x + WALL_OFFSET_M, "y": y - FOLLOW_AHEAD_M}
    wall_y = wall_marks.get(WALL_SOUTH, y - WALL_OFFSET_M)
    return {"x": x + FOLLOW_AHEAD_M, "y": wall_y + WALL_OFFSET_M}


def avoid_obstacles(state: BattleState, target: dict[str, float]) -> dict[str, float]:
    own = state.own_unit
    push_x = 0.0
    push_y = 0.0

    for obstacle in state.contacts.obstacles:
        dx = own.position.x - obstacle.position.x
        dy = own.position.y - obstacle.position.y
        distance = max(math.hypot(dx, dy), 0.001)
        danger = obstacle.radius + OBSTACLE_CLEARANCE_M
        if distance >= danger:
            continue
        strength = (danger - distance) / danger
        push_x += (dx / distance) * strength * OBSTACLE_PUSH_M
        push_y += (dy / distance) * strength * OBSTACLE_PUSH_M

    return {
        "x": target["x"] + push_x,
        "y": target["y"] + push_y,
    }


run_bot(on_tick)
