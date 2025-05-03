from src import shared, utils
from src.coins import Coin
from src.player import Player
from src.tiles import Tile

ENTITIES: list[utils.EntityType] = [Tile, Player, Coin]


class World:
    def __init__(self):
        utils.make_entities_from_tmx("assets/map.tmx", type_factory=ENTITIES)

    def update(self):
        shared.player.update()
        for entity in ENTITIES:
            for obj in entity.objects:
                obj.update()

    def draw(self):
        shared.player.draw()
        for entity in ENTITIES:
            for obj in entity.objects:
                obj.draw()
