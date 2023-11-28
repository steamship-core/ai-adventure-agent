from schema.server_settings import ServerSettings


def test_server_settings_extra_field():
    ss = ServerSettings.parse_obj({"characters": []})
    assert ss
    assert not hasattr(ss, "characters")
