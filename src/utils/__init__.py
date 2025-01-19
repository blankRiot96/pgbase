import enum
import functools
import sys
import time
import typing as t
from enum import Enum, auto
from pathlib import Path

import pygame

from src import shared


def get_asset_path(path):
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")) / path
    return path


@functools.lru_cache
def load_image(
    path: str,
    alpha: bool,
    bound: bool = False,
    scale: float = 1.0,
    smooth: bool = False,
) -> pygame.Surface:
    img = pygame.image.load(get_asset_path(path))
    if scale != 1.0:
        if smooth:
            img = pygame.transform.smoothscale_by(img, scale)
        else:
            img = pygame.transform.scale_by(img, scale)
    if bound:
        img = img.subsurface(img.get_bounding_rect()).copy()
    if alpha:
        return img.convert_alpha()
    return img.convert()


@functools.lru_cache
def load_font(name: str | None, size: int) -> pygame.Font:
    return pygame.Font(get_asset_path(name), size)


class Gravity:
    """Applies gravity"""

    def __init__(self) -> None:
        self.velocity = 0.0

    def update(self):
        self.velocity += shared.WORLD_GRAVITY * shared.dt
        if self.velocity > shared.MAX_FALL_VELOCITY:
            self.velocity = shared.MAX_FALL_VELOCITY


class CollisionSide(Enum):
    RIGHT = auto()
    LEFT = auto()
    TOP = auto()
    BOTTOM = auto()


class Collider:
    """Have as attribute to entity"""

    all_colliders: list[t.Self] = []

    def __init__(self, pos, size) -> None:
        self.pos = pygame.Vector2(pos)
        self.size = size
        Collider.all_colliders.append(self)

    @property
    def rect(self) -> pygame.FRect:
        return pygame.FRect(self.pos, self.size)

    def get_collision_sides(self, dx, dy) -> set[CollisionSide]:
        """Returns empty set if no collision"""

        sides = set()
        for collider in Collider.all_colliders:
            if collider is self:
                continue

            c = lambda x, y: self.rect.move(x, y).colliderect(collider.rect)

            if c(dx, 0) and dx < 0:
                sides.add(CollisionSide.LEFT)
            if c(dx, 0) and dx > 0:
                sides.add(CollisionSide.RIGHT)
            if c(0, dy) and dy < 0:
                sides.add(CollisionSide.TOP)
            if c(0, dy) and dy > 0:
                self.pos.y = collider.pos.y - self.size[1]
                sides.add(CollisionSide.BOTTOM)

        return sides

    def draw(self):
        pygame.draw.rect(shared.screen, "red", self.rect, width=1)


class Timer:
    """
    Class to check if time has passed.
    """

    def __init__(self, time_to_pass: float):
        self.time_to_pass = time_to_pass
        self.start = time.perf_counter()

    def reset(self):
        self.start = time.perf_counter()

    def tick(self) -> bool:
        if time.perf_counter() - self.start > self.time_to_pass:
            self.start = time.perf_counter()
            return True
        return False
