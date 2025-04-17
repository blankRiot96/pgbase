import typing as t
import pytmx

class Entity(t.Protocol):
    objects: list

    def __init__(self, pos: tuple[int, int]) -> None:
        super().__init__()


EntityType: t.TypeAlias = t.Type[Entity]


def make_entities_from_tmx(tmx_file_path, type_factory: list[t.Type[Entity]]):
    inverted_map = {entity.__name__: entity for entity in type_factory}

    tiled_map = pytmx.load_pygame(tmx_file_path)
    for layer_index, layer in enumerate(tiled_map.layers):
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, image in layer.tiles():
                properties = tiled_map.get_tile_properties(x, y, layer_index)

                if properties is None:
                    continue
                
                entity_type = inverted_map[properties["type"]]
                entity_type((x * tiled_map.tilewidth, y * tiled_map.tileheight))
