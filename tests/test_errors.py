"""One message representation for structured CLI and ordinary Python errors."""

import pytest

from tamarind.errors import APIError, TamarindError, ValidationError


@pytest.mark.parametrize("kind", [TamarindError, ValidationError, APIError])
def test_recovery_guidance_updates_every_exception_representation(kind):
    kwargs = {"status_code": 503} if kind is APIError else {}
    error = kind("Request failed.", detail={"jobName": "smoke"}, **kwargs)
    error.message += " Query smoke before retrying."
    assert str(error) == error.message == "Request failed. Query smoke before retrying."
    assert error.args == (error.message,)
    assert error.detail == {"jobName": "smoke"}
    if kind is APIError:
        assert error.status_code == 503
    error.message = "Replacement guidance"
    assert str(error) == "Replacement guidance"
