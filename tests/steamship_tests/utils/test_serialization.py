# @pytest.mark.usefixtures("client")
from schema.adventure_template import AdventureTemplate
from schema.characters import Character


def test_serialize_nested_obj(
    # client: Steamship
):
    at = AdventureTemplate()
    at.characters = [Character(name="Hi")]
    d = at.dict()
    assert isinstance(d.get("characters")[0], dict)
