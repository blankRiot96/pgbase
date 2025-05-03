from __future__ import annotations

import typing as t
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum, auto

import pygame

from src import shared


class CollisionSide(Enum):
    RIGHT = auto()
    LEFT = auto()
    TOP = auto()
    BOTTOM = auto()


@dataclass
class CollisionData:
    colliders: dict[CollisionSide, Collider]


class Collider:
    """Have as attribute to entity"""

    all_colliders: list[t.Self] = []
    temp_colliders: list[t.Self] = []

    def __init__(self, pos, size, temp: bool = False) -> None:
        self.pos = pygame.Vector2(pos)
        self.size = size
        if not temp:
            Collider.all_colliders.append(self)

    @property
    def rect(self) -> pygame.FRect:
        return pygame.FRect(self.pos, self.size)

    def get_collision_data(self, dx, dy) -> CollisionData:
        """Returns datapacket containing collisiondata"""

        colliders = defaultdict(list)
        possible_x = []
        possible_y = []

        for collider in Collider.all_colliders + Collider.temp_colliders:
            if collider is self:
                continue

            is_colliding_x = self.rect.move(dx, 0).colliderect(collider.rect)
            is_colliding_y = self.rect.move(0, dy).colliderect(collider.rect)

            side = None
            if is_colliding_x and dx < 0:
                possible_x.append(collider.rect.right)
                side = CollisionSide.LEFT
            elif is_colliding_x and dx > 0:
                possible_x.append(collider.pos.x - self.size[0])
                side = CollisionSide.RIGHT

            if is_colliding_y and dy < 0:
                possible_y.append(collider.rect.bottom)
                side = CollisionSide.TOP
            elif is_colliding_y and dy > 0:
                possible_y.append(collider.pos.y - self.size[1])
                side = CollisionSide.BOTTOM

            if side is not None:
                colliders[side].append(collider)

        if possible_x:
            if dx < 0:
                self.pos.x = max(possible_x)
            else:
                self.pos.x = min(possible_x)

        if possible_y:
            if dy < 0:
                self.pos.y = max(possible_y)
            else:
                self.pos.y = min(possible_y)

        x_index = possible_x.index(self.pos.x) if possible_x else None
        y_index = possible_y.index(self.pos.y) if possible_y else None

        snapped = {}

        for side in (CollisionSide.LEFT, CollisionSide.RIGHT):
            if x_index is not None and colliders[side]:
                snapped[side] = colliders[side][x_index]

        for side in (CollisionSide.TOP, CollisionSide.BOTTOM):
            if y_index is not None and colliders[side]:
                snapped[side] = colliders[side][y_index]

        return CollisionData(colliders=snapped)

    def is_colliding(self, dx, dy) -> bool:
        for collider in Collider.all_colliders + Collider.temp_colliders:
            if collider is self:
                continue

            if collider.rect.move(dx, dy).colliderect(self.rect):
                return True

        return False

    def draw(self, fill=False, color="red"):
        pygame.draw.rect(
            shared.screen,
            color,
            shared.camera.transform(self.rect),
            width=not fill,
        )
