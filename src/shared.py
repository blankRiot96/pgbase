from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    import pygame

    from src.enums import State
    from src.utils import Camera

# Canvas
screen: pygame.Surface
srect: pygame.Rect
camera: Camera

# Events
events: list[pygame.event.Event]
mouse_pos: pygame.Vector2
mouse_press: tuple[int, ...]
mjr: tuple[bool, ...]
mjp: tuple[bool, ...]
keys: list[bool]
kp: list[bool]
kr: list[bool]
dt: float
clock: pygame.Clock


# States
next_state: State | None
