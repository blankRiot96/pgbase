import sys, functools, pygame
from pathlib import Path

import math

import time


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
    if name is None:
        return pygame.Font(None, size)
    return pygame.Font(get_asset_path(name), size)


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