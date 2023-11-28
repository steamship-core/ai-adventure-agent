from schema.image_theme import ImageTheme
from schema.server_settings import ServerSettings


def test_server_settings_extra_field():
    ss = ServerSettings.parse_obj({"characters": []})
    assert ss
    assert not hasattr(ss, "characters")


def test_server_settings_nested_obj():
    ss = ServerSettings.parse_obj({"image_themes": [{"name": "test"}]})
    assert ss
    assert ss.image_themes
    assert len(ss.image_themes) == 1
    assert isinstance(ss.image_themes[0], ImageTheme)
