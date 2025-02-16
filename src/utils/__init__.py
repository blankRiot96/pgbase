from __future__ import annotations

import functools
import itertools
import os
import sys
import time
import typing as t
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

import pygame
import ujson

from src import shared

from .client import LocalBroadcastClient, UDPClient
from .server import LocalBroadcastServer, UDPServer


class Button:
    DEFAULT_COLORS = {
        "bg": (100, 100, 100),
        "text": "snow",
        "hover": {
            "bg": "grey",
            "text": (220, 220, 220),
        },
        "clicked": {
            "bg": "purple",
            "text": "seagreen",
        },
    }

    def __init__(
        self,
        text: str,
        rect: pygame.Rect,
        colors: None | dict[str, pygame.typing.ColorLike] = None,
    ) -> None:
        self.text = text
        self.rect = rect
        self.font = load_font(None, int(rect.height * 0.7))

        if colors is None:
            self.colors = Button.DEFAULT_COLORS.copy()
        else:
            self.colors = colors

        self.just_clicked = False
        self.is_hovering = False

    def update(self):
        self.is_hovering = self.rect.collidepoint(shared.mouse_pos)
        self.just_clicked = shared.mjr[0] and self.is_hovering

    def draw(self):
        colors = self.colors
        if self.is_hovering:
            colors = self.colors["hover"]
            if shared.mouse_press[0]:
                colors = self.colors["clicked"]
        if self.just_clicked:
            colors = self.colors["clicked"]

        pygame.draw.rect(shared.screen, colors["bg"], self.rect)

        text_surf = self.font.render(self.text, True, colors["text"])
        text_rect = text_surf.get_rect(center=self.rect.center)

        shared.screen.blit(text_surf, text_rect)


class ItemSelector:
    """Lets you select an item"""

    PADDING = 20
    BOX_PADDING = 5

    def __init__(
        self, topleft, items: dict[str, pygame.Surface], item_scale=1.0, colors=None
    ) -> None:
        if colors is None:
            colors = {
                "bg": (100, 100, 100),
                "box": (50, 50, 50),
                "hover": (100, 100, 0),
            }

        self.colors = colors
        self.pos = pygame.Vector2(topleft)
        self.items = items
        self.currently_selected_item = list(items)[0]

        self.is_being_interacted_with = False
        self.scale_items(item_scale)
        self.create_background_image()

    def scale_items(self, item_scale):
        if item_scale != 1:
            for item_name, image in self.items.items():
                self.items[item_name] = pygame.transform.scale_by(image, item_scale)

    def create_background_image(self):
        total_width = ItemSelector.BOX_PADDING + ItemSelector.PADDING
        max_height = 0
        for item in self.items.values():
            total_width += (
                item.get_width() + ItemSelector.PADDING + ItemSelector.BOX_PADDING
            )
            if item.get_height() > max_height:
                max_height = item.get_height()

        self.bg = pygame.Surface(
            (total_width, max_height + 4 * ItemSelector.BOX_PADDING)
        )
        self.bg.fill(self.colors["bg"])

    def update(self):
        pass

    def draw(self):
        self.is_being_interacted_with = False
        shared.screen.blit(self.bg, self.pos)

        acc_x = 0
        for item_name, item_image in self.items.items():
            rect = pygame.Rect(
                self.pos.x + acc_x + ItemSelector.PADDING,
                self.pos.y + ItemSelector.BOX_PADDING,
                item_image.get_width() + 2 * ItemSelector.BOX_PADDING,
                self.bg.get_height() - (2 * ItemSelector.BOX_PADDING),
            )

            if rect.collidepoint(shared.mouse_pos):
                self.is_being_interacted_with = True
                color = self.colors["hover"]

                if shared.mjp[0]:
                    self.currently_selected_item = item_name
            else:
                color = self.colors["box"]

            pygame.draw.rect(shared.screen, color, rect)
            shared.screen.blit(
                item_image,
                (
                    self.pos.x
                    + acc_x
                    + ItemSelector.BOX_PADDING
                    + ItemSelector.PADDING,
                    self.pos.y + 2 * ItemSelector.BOX_PADDING,
                ),
            )

            acc_x += (
                item_image.get_width() + ItemSelector.BOX_PADDING + ItemSelector.PADDING
            )


class MapItem:
    """Placeholder for the real entities"""

    def __init__(self, pos, entity_type, image) -> None:
        self.pos = pygame.Vector2(pos)
        self.image = image
        self.rect = self.image.get_rect(topleft=self.pos)
        self.entity_type = entity_type

    def draw(self):
        shared.screen.blit(self.image, shared.camera.transform(self.pos))


class WorldMap:
    """The entire world, categorized in a map."""

    def __init__(self, file_path: str | Path, entity_classes: list[t.Type]) -> None:
        # self.chunks: dict[tuple[int, int], list[WorldEntity]] = {}

        self.file_path = file_path
        self.entity_classes = entity_classes
        self.reverse_entity_class_map = {
            entity_type.__name__: entity_type for entity_type in self.entity_classes
        }

        self.load_map_items()

    def load_map_items(self):
        self.entities: list[MapItem] = []

        with open(self.file_path) as f:
            schema = ujson.load(f)

        for class_name, position in schema:
            cls = self.reverse_entity_class_map[class_name]
            image = cls.get_placeholder_img()
            self.entities.append(MapItem(position, cls, image))

    def dump(self) -> None:
        jsonable_map = [
            [entity.entity_type.__name__, (entity.pos.x, entity.pos.y)]
            for entity in self.entities
        ]

        with open(self.file_path, "w") as f:
            ujson.dump(jsonable_map, f, indent=2)

    def load(self) -> list:
        entities = []
        with open(self.file_path) as f:
            json_map = ujson.load(f)
            for entity_class, entity_pos in json_map:
                entity = self.reverse_entity_class_map[entity_class](entity_pos)
                entities.append(entity)

        return entities

    def draw(self):
        for entity in self.entities:
            entity.draw()


class PlacementMode(Enum):
    FREE = auto()
    GRID = auto()


class _CommandBar:
    """Command Bar for the placement handler"""

    HEIGHT = 40

    def __init__(self) -> None:
        self.command_just_ejected = False

        self._command_text = ""
        self._command_being_typed = False
        self.font = load_font(None, 32)

    def get_command(self) -> str:
        return self._command_text

    def update(self):
        self.command_just_ejected = False
        for event in shared.events:
            if event.type == pygame.TEXTINPUT:
                if self._command_being_typed:
                    self._command_text += event.text

                if event.text == ":":
                    self._command_being_typed = True
                    self._command_text = ""

        if shared.kp[pygame.K_RETURN]:
            self.command_just_ejected = True
            self._command_being_typed = False

    def draw(self):
        if not self._command_being_typed:
            return

        bg_rect = pygame.Rect(
            0,
            shared.srect.height - _CommandBar.HEIGHT,
            shared.srect.width,
            _CommandBar.HEIGHT,
        )
        pygame.draw.rect(shared.screen, "purple", bg_rect)
        text_surf = self.font.render(":" + self._command_text, True, "white")
        text_rect = text_surf.get_rect()

        text_rect.centery = bg_rect.centery
        text_rect.x += 10
        shared.screen.blit(text_surf, text_rect)


class WorldPlacementHandler:
    """Handles the placement of entities into the world"""

    def __init__(
        self,
        world_map: WorldMap,
        starting_keybinds_file_name: str,
        left_bounds: float | None = None,
        right_bounds: float | None = None,
        top_bounds: float | None = None,
        bottom_bounds: float | None = None,
    ) -> None:
        self.world_map = world_map
        self.check_if_dir_exists()
        self.current_keybinds_file_chosen = (
            f"assets/editor_keybinds/{starting_keybinds_file_name}.json"
        )
        with open(self.current_keybinds_file_chosen) as f:
            self.last_config = ujson.load(f)
            self.last_read_time = time.time()

        self.left_bounds = left_bounds
        self.right_bounds = right_bounds
        self.top_bounds = top_bounds
        self.bottom_bounds = bottom_bounds

        self.mode = PlacementMode.GRID
        self.current_entity_pos = pygame.Vector2()
        self.current_entity_type = self.world_map.reverse_entity_class_map[
            list(self.last_config.values())[0]
        ]
        self.current_entity_image = pygame.Surface((50, 50))
        self.crect = self.current_entity_image.get_rect()

        self.placement_modes = itertools.cycle([PlacementMode.FREE, PlacementMode.GRID])

        self._last_placed_pos = pygame.Vector2(0, 0)
        self._last_free_placement = pygame.Vector2(0, 0)
        self._out_of_bounds = False

        self.command_bar = _CommandBar()

    def check_if_dir_exists(self):
        if not Path("assets/editor_keybinds").exists():
            raise FileNotFoundError(
                "To use `WorldPlacementHandler` an editor_keybinds/ directory needs to be present and populated with keybinds"
            )

    def on_place(self):
        if not shared.mouse_press[0] or self._out_of_bounds:
            return

        for item in self.world_map.entities:
            if self.crect.colliderect(item.rect):
                return

        if self.mode == PlacementMode.FREE:
            self._last_free_placement = self.current_entity_pos.copy()
        self._last_placed_pos = pygame.Vector2(
            self.current_entity_image.get_rect(topleft=self.current_entity_pos).center
        )
        self.world_map.entities.append(
            MapItem(
                self.current_entity_pos,
                self.current_entity_type,
                self.current_entity_image,
            )
        )

    def is_config_valid(self, config) -> bool:
        return True

    def update(self):
        self.command_bar.update()
        if self.command_bar._command_being_typed:
            return

        if self.command_bar.command_just_ejected:
            file_name = self.command_bar.get_command()
            self.current_keybinds_file_chosen = (
                f"assets/editor_keybinds/{file_name}.json"
            )
            print(f"Keybinds file: {self.current_keybinds_file_chosen}")

        if shared.kp[pygame.K_p]:
            self.mode = next(self.placement_modes)
            print(f"Switched to `{self.mode}`")

        try:
            if (
                os.stat(self.current_keybinds_file_chosen).st_mtime
                > self.last_read_time
            ) or self.command_bar.command_just_ejected:
                with open(self.current_keybinds_file_chosen) as f:
                    config = ujson.load(f)
                    self.last_read_time = time.time()
            else:
                config = self.last_config
        except FileNotFoundError:
            config = self.last_config

        if not self.is_config_valid(config):
            config = self.last_config
        else:
            self.last_config = config

        if self.command_bar.command_just_ejected:
            self.current_entity_type = self.world_map.reverse_entity_class_map[
                list(self.last_config.values())[0]
            ]

        for keybind, class_name in config.items():
            if shared.kp[getattr(pygame, keybind)]:
                print(f"Current Entity selected: `{class_name}`")
                self.current_entity_type = self.world_map.reverse_entity_class_map[
                    class_name
                ]

        self.current_entity_pos = shared.mouse_pos + shared.camera.offset

        self._out_of_bounds = False
        offset = self.current_entity_pos
        if self.left_bounds is not None:
            if offset.x < self.left_bounds:
                self._out_of_bounds = True

        if self.right_bounds is not None:
            if offset.x > self.right_bounds:
                self._out_of_bounds = True

        if self.top_bounds is not None:
            if offset.y < self.top_bounds:
                self._out_of_bounds = True
        if self.bottom_bounds is not None:
            if offset.y > self.bottom_bounds:
                self._out_of_bounds = True

        if self.mode == PlacementMode.GRID:
            self.current_entity_pos = shared.mouse_pos + shared.camera.offset
            width, height = self.current_entity_image.get_size()
            self.current_entity_pos.x //= width
            self.current_entity_pos.y //= height

            self.current_entity_pos.x *= width
            self.current_entity_pos.y *= height

        self.current_entity_image = self.current_entity_type.get_placeholder_img()
        self.crect = self.current_entity_image.get_rect(topleft=self.current_entity_pos)

        self.on_place()

    def draw(self):
        if not self.command_bar._command_being_typed and not self._out_of_bounds:
            shared.screen.blit(
                self.current_entity_image,
                shared.camera.transform(self.current_entity_pos),
            )
        self.command_bar.draw()


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

    def attach_to(self, pos, smoothness_factor=0.08):
        self.offset.x += (
            pos[0] - self.offset.x - (shared.srect.width // 2)
        ) * smoothness_factor
        self.offset.y += (
            pos[1] - self.offset.y - (shared.srect.height // 2)
        ) * smoothness_factor

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

    def draw(self):
        pygame.draw.rect(
            shared.screen, "red", shared.camera.transform(self.rect), width=1
        )


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
