from importlib.resources import files


def test_package_declares_inline_types() -> None:
    assert files("tamarind").joinpath("py.typed").is_file()
