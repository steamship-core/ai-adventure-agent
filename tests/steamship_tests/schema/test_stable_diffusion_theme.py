from schema.stable_diffusion_theme import PIXEL_ART_THEME_1


def test_stable_diffusion_theme():
    assert PIXEL_ART_THEME_1.make_prompt("Hi") == "(pixel art) Hi"

    assert (
        PIXEL_ART_THEME_1.make_prompt("Hi {name}", {"name": "Ted"})
        == "(pixel art) Hi Ted"
    )

    # If you don't use a variable, that's ok
    assert (
        PIXEL_ART_THEME_1.make_prompt("Hi {name}", {"name": "Ted", "place": "Har"})
        == "(pixel art) Hi Ted"
    )

    # If you use a bad variable, that's ok (we'll validate when you set the prompt, not execute it)
    assert (
        PIXEL_ART_THEME_1.make_prompt(
            "Hi {name} {there}", {"name": "Ted", "place": "Har"}
        )
        == "(pixel art) Hi Ted {there}"
    )
