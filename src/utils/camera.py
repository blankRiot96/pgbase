import pygame

from src import shared


class Camera:
    def __init__(
        self,
        left_bounds: float | None = None,
        right_bounds: float | None = None,
        top_bounds: float | None = None,
        bottom_bounds: float | None = None,
    ) -> None:

        self.left_bounds = left_bounds
        self.right_bounds = right_bounds
        self.top_bounds = top_bounds
        self.bottom_bounds = bottom_bounds
        self.offset = pygame.Vector2()
        self.rect = pygame.Rect(0, 0, shared.srect.width, shared.srect.height)

    def attach_to(self, pos, smoothness_factor=0.08):
        self.offset.x += (
            pos[0] - self.offset.x - (shared.srect.width // 2)
        ) * smoothness_factor
        self.offset.y += (
            pos[1] - self.offset.y - (shared.srect.height // 2)
        ) * smoothness_factor

        self.rect.topleft = self.offset

    def bound(self):
        offset = self.offset

        if self.left_bounds is not None:
            if offset.x < self.left_bounds:
                offset.x = self.left_bounds

        if self.right_bounds is not None:
            if offset.x > self.right_bounds - shared.srect.width:
                offset.x = self.right_bounds - shared.srect.width

        if self.top_bounds is not None:
            if offset.y < self.top_bounds:
                offset.y = self.top_bounds

        if self.bottom_bounds is not None:
            if offset.y > self.bottom_bounds - shared.srect.height:
                offset.y = self.bottom_bounds - shared.srect.height

    def transform(self, pos) -> pygame.Vector2 | pygame.Rect | pygame.FRect:
        if isinstance(pos, pygame.Rect) or isinstance(pos, pygame.FRect):
            return pos.move(*-self.offset)
        return pygame.Vector2(pos[0] - self.offset.x, pos[1] - self.offset.y)
