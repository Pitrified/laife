"""Every pydantic model in laife resolves its annotations.

Under Python 3.14 annotations are evaluated lazily, and ruff moves imports used only in
annotations under ``TYPE_CHECKING``. pydantic needs those names at runtime, and a model
missing one fails only when it is first built, not at import. ruff exempts the models it
can recognise (``runtime-evaluated-base-classes`` in ``ruff.toml``), but not a model whose
pydantic base comes from another module. Rebuilding every model here finds that case.
"""

import importlib
import pkgutil
from typing import TYPE_CHECKING

from pydantic import BaseModel
import pytest

import laife

if TYPE_CHECKING:
    from collections.abc import Iterator


def _subclasses(cls: type) -> Iterator[type]:
    for sub in cls.__subclasses__():
        yield sub
        yield from _subclasses(sub)


def _laife_models() -> list[type[BaseModel]]:
    for module in pkgutil.walk_packages(laife.__path__, "laife."):
        importlib.import_module(module.name)
    models = {cls for cls in _subclasses(BaseModel) if cls.__module__.startswith("laife.")}
    return sorted(models, key=lambda cls: f"{cls.__module__}.{cls.__qualname__}")


@pytest.mark.parametrize("model", _laife_models(), ids=lambda cls: cls.__qualname__)
def test_model_builds(model: type[BaseModel]) -> None:
    """The model rebuilds with every annotation resolved."""
    model.model_rebuild(force=True, raise_errors=True)
