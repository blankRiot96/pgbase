import typing as t

from src import shared
from src.enums import State
from src.game_state import GameState


class StateLike(t.Protocol):
    def update(self): ...

    def draw(self): ...


class StateManager:
    def __init__(self) -> None:
        self.state_dict: dict[State, StateLike] = {
            State.GAME: GameState,
        }

        shared.next_state = State.GAME
        self.set_state()

    def set_state(self):
        self.state_obj: StateLike = self.state_dict.get(shared.next_state)()
        shared.next_state = None

    def update(self):
        self.state_obj.update()
        if shared.next_state is not None:
            self.set_state()

    def draw(self):
        self.state_obj.draw()
