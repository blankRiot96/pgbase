import functools
import math
import sys
import time
import typing as t
from pathlib import Path

import pygame

from src import shared


def updater(entities):
    for entity in entities[:]:
        entity.update()

        if not entity.alive:
            entities.remove(entity)


def drawer(entities):
    for entity in entities:
        entity.draw()


def rad_to_mouse(pos: t.Sequence):
    return math.atan2(
        (shared.mouse_pos[1] + shared.camera.offset.y) - pos[1],
        (shared.mouse_pos[0] + shared.camera.offset.x) - pos[0],
    )


def darken_image(image: pygame.Surface, alpha: float) -> pygame.Surface:
    darkened = image.copy()
    overlay = pygame.Surface(image.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, int(alpha)))  # Directly fill with alpha
    darkened.blit(overlay, (0, 0))
    return darkened


def bound_image(image: pygame.Surface):
    return image.subsurface(image.get_bounding_rect())


def debug_rect(rect: pygame.typing.RectLike):
    pygame.draw.rect(shared.screen, "red", shared.camera.transform(rect), 1)


def get_mid_point(vec1: pygame.Vector2, vec2: pygame.Vector2) -> pygame.Vector2:
    return pygame.Vector2(vec1.x + vec2.x, vec1.y + vec2.y) * 0.5


def move_towards_rad(
    vec: pygame.Vector2, radians: float, dist: float
) -> pygame.Vector2:
    v = vec.copy()
    v.x += math.cos(radians) * dist
    v.y += math.sin(-radians) * dist

    return v


def circle_surf(radius, color):
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(surf, color, (radius, radius), radius)

    return surf


def rad_to(vec1: pygame.Vector2, vec2: pygame.Vector2):
    return math.atan2(vec2.y - vec1.y, vec2.x - vec1.x)


def move_further(
    vector: pygame.Vector2, origin_vector: pygame.Vector2, distance: float = 1000
) -> pygame.Vector2:
    """
    Moves 'vector' further away from 'origin_vector' by 'distance' pixels in the same direction.

    :param vector: The vector to move.
    :param origin_vector: The reference vector from which the distance is measured.
    :param distance: The additional distance to move.
    :return: A new vector moved further away.
    """
    direction = (vector - origin_vector).normalize()  # Get unit direction
    return vector + direction * distance  # Move further in that direction


def get_asset_path(path):
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")) / path
    return path


@functools.cache
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
    if name is None:
        return pygame.Font(None, size)
    return pygame.Font(get_asset_path(name), size)


class Timer:
    """
    Class to check if time has passed. Repeatedly.
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


class CooldownTimer:
    """
    Operates once and then needs to be started again explicitely
    """

    def __init__(self, seconds: float) -> None:
        self.seconds = seconds
        self.is_cooling_down = False
        self.start_time = None
        self.amount_cooled = 1.0

    def start(self):
        self.is_cooling_down = True
        self.amount_cooled = 0.0
        self.start_time = time.perf_counter()

    def update(self):
        if not self.is_cooling_down:
            return

        time_passed = time.perf_counter() - self.start_time  # type: ignore
        self.amount_cooled = time_passed / self.seconds

        if time_passed >= self.seconds:
            self.is_cooling_down = False
            self.amount_cooled = 1.0
            self.start_time = None
