from src import shared, utils
from src.player import Player
from src.tiles import Tile

type_factory = {
    "1": Player,
    "2": Tile,
}


def make_entities_from_txt(txt_file: str, tileside, entities):
    with open(txt_file) as f:
        world = f.readlines()

    for i, row in enumerate(world):
        row = row.strip("\n")
        for j, col in enumerate(row):
            if col == " ":
                continue
            pos = j * tileside, i * tileside
            entities.append(type_factory[col](pos))


class World:
    def __init__(self):
        shared.entities = []
        make_entities_from_txt("assets/map.txt", shared.TILE_SIDE, shared.entities)

    def update(self):
        for entity in shared.entities:
            entity.update()

    def draw(self):
        for entity in shared.entities:
            entity.draw()
