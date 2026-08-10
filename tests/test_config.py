from tamarind import config


def test_precedence_flag_over_env_over_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("TAMARIND_API_KEY", raising=False)
    monkeypatch.delenv("TAMARIND_PROFILE", raising=False)

    # Profile on disk
    config.save_profile("default", api_key="from-profile")
    assert config.load_config().api_key == "from-profile"

    # Env beats profile
    monkeypatch.setenv("TAMARIND_API_KEY", "from-env")
    assert config.load_config().api_key == "from-env"

    # Explicit flag beats env
    assert config.load_config(api_key="from-flag").api_key == "from-flag"


def test_defaults_and_trailing_slash(tmp_path, monkeypatch):
    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("TAMARIND_API_BASE", raising=False)
    cfg = config.load_config(api_base="https://x.test/api")
    assert cfg.api_base == "https://x.test/api/"
    assert cfg.catalog_base == "https://mcp.tamarind.bio/"


def test_mask_key():
    assert config.mask_key(None) == "<none>"
    assert config.mask_key("sk_abcdefgh") == "sk_a…efgh"
    assert "*" in config.mask_key("short")
