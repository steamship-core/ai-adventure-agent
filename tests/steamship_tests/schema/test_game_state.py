from schema.game_state import GameState


def test_game_state_dict():
    gs = GameState()
    d = gs.dict()
    assert d
    assert "active_mode" in d
