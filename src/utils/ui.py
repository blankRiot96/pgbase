import pygame

from src import shared

from .misc import load_font


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
