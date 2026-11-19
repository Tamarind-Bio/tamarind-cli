"""v1 operations on the public :class:`tamarind.Tamarind` client.

Today's methods keep their names and follow the server's switch on their own (see
:mod:`tamarind._v1.classic`). The operations only v1 has are added beside them: new
resources (``client.projects``, ``client.molecules``...) and new methods on today's
resources (``client.jobs.get``, ``client.tools.facets``...). They take the v1
arguments and return v1's answers (decoded JSON), and they send a request only when
v1 is on for the key; otherwise they raise
:class:`~tamarind._v1.switch.V1NotEnabledError` and send nothing.
"""

from __future__ import annotations

import importlib
from typing import Any, Iterator


class V1Method:
    """One v1 operation, sent through ``http``'s v1 client when v1 is on for its key."""

    def __init__(self, http: Any, path: tuple[str, ...], doc: str | None):
        self._http = http
        self._path = path
        self.__name__ = path[-1]
        self.__doc__ = doc

    def bound(self) -> Any:
        """The v1 client's own method (checks the switch first)."""
        target = self._http.v1(f"Tamarind().{'.'.join(self._path)}")
        for name in self._path:
            target = getattr(target, name)
        return target

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.bound()(*args, **kwargs)

    def raw(self, *args: Any, **kwargs: Any) -> Any:
        """The ``httpx.Response`` itself, for its headers."""
        return self.bound().raw(*args, **kwargs)

    def __repr__(self) -> str:
        return f"<v1 operation Tamarind().{'.'.join(self._path)}>"


def _v1() -> Any:
    # Imported on first use, so `import tamarind` doesn't load the generated client.
    return importlib.import_module("tamarind._v1.client")


def _doc(resource: type, name: str) -> str | None:
    member = resource.__dict__.get(name)
    return getattr(member, "__doc__", None)


# The v1 client's resource class for each attribute name.
_CLASSES = {
    "me": "Me",
    "api_keys": "ApiKeys",
    "service_accounts": "ServiceAccounts",
    "organization": "Organization",
    "usage": "Usage",
    "models": "Models",
    "projects": "Projects",
    "projects.notes": "ProjectNotes",
    "molecules": "Molecules",
    "assays": "Assays",
    "tools": "Tools",
    "jobs": "Jobs",
    "files": "Files",
    "pipelines": "Pipelines",
    "custom_tools": "CustomTools",
}
# The resources only v1 has; the others are today's, with v1 methods added.
NEW_RESOURCES = ("me", "api_keys", "service_accounts", "organization", "usage", "models", "projects", "molecules", "assays")


def _class(path: tuple[str, ...]) -> type:
    return getattr(_v1(), _CLASSES[".".join(path)])


class v1_method:
    """A v1 operation as a method of one of today's resources, which name their
    :class:`~tamarind.http.HTTPClient` with ``_v1_http()``."""

    def __init__(self, resource: str, name: str | None = None):
        self._resource = resource
        self._name = name

    def __set_name__(self, owner: type, name: str) -> None:
        self._name = self._name or name

    def __get__(self, obj: Any, owner: type | None = None) -> Any:
        if obj is None:
            return self
        assert self._name is not None
        return V1Method(obj._v1_http(), (self._resource, self._name), _doc(_class((self._resource,)), self._name))


class V1Resource:
    """Every operation of one v1 resource (``projects``, ``molecules``...)."""

    def __init__(self, http: Any, path: tuple[str, ...]):
        self._http = http
        self._path = path
        self._members: dict[str, Any] | None = None

    def _load(self) -> dict[str, Any]:
        if self._members is None:
            cls = _class(self._path)
            operation = _v1().Operation
            members: dict[str, Any] = {
                name: V1Method(self._http, self._path + (name,), _doc(cls, name))
                for name, member in vars(cls).items()
                if isinstance(member, operation)
            }
            for sub, _ in _CLASSES.items():
                parts = tuple(sub.split("."))
                if len(parts) == len(self._path) + 1 and parts[:-1] == self._path:
                    members[parts[-1]] = V1Resource(self._http, parts)
            self._members = members
        return self._members

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._load()[name]
        except KeyError:
            raise AttributeError(f"Tamarind().{'.'.join(self._path)} has no attribute {name!r}") from None

    def __dir__(self) -> list[str]:
        return sorted(set(super().__dir__()) | set(self._load()))

    @property
    def __doc__(self) -> str | None:  # type: ignore[override]
        return _class(self._path).__doc__

    def __repr__(self) -> str:
        return f"<v1 resource Tamarind().{'.'.join(self._path)}>"


def resources(http: Any) -> dict[str, V1Resource]:
    return {name: V1Resource(http, (name,)) for name in NEW_RESOURCES}


def paginate(method: Any, *args: Any, **params: Any) -> Iterator[Any]:
    """Yield every item of a v1 list operation, following ``nextCursor`` page by page:
    ``Tamarind.paginate(client.projects.list, limit=200)``. Takes the same arguments
    as ``method``; ``limit`` sets the page size."""
    if not isinstance(method, V1Method):
        raise TypeError("Tamarind.paginate() takes a v1 list operation such as client.projects.list")
    return _v1().Tamarind.paginate(method.bound(), *args, **params)
