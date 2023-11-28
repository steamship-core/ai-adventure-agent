# @pytest.mark.usefixtures("client")
from schema.characters import Character
from schema.server_settings import ServerSettings


def test_serialize_nested_obj(
    # client: Steamship
):
    at = ServerSettings()
    at.characters = [Character(name="Hi")]
    d = at.dict()
    assert isinstance(d.get("characters")[0], dict)
