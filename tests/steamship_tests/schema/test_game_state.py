from schema.game_state import GameState


def test_game_state_dict():
    gs = GameState()
    assert gs.dict()
