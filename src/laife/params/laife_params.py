"""Laife project params.

Parameters are actual value of the config.

The class is a singleton, so it can be accessed from anywhere in the code.

There is a parameter regarding the environment type (stage and location), which
is used to load different paths and other parameters based on the environment.
"""

from loguru import logger as lg

from laife.meta.singleton import Singleton
from laife.params.env_type import EnvType
from laife.params.laife_paths import LaifePaths
from laife.params.llm_services import LLMServicesParams


class LaifeParams(metaclass=Singleton):
    """Laife project parameters."""

    def __init__(self) -> None:
        """Load the Laife params."""
        lg.info("Loading Laife params")
        self.set_env_type()

    def set_env_type(self, env_type: EnvType | None = None) -> None:
        """Set the environment type.

        Args:
            env_type (EnvType | None): The environment type.
                If None, it will be set from the environment variables.
                Defaults to None.
        """
        if env_type is not None:
            self.env_type = env_type
        else:
            self.env_type = EnvType.from_env_var()
        self.load_config()

    def load_config(self) -> None:
        """Load the laife configuration."""
        self.paths = LaifePaths(env_type=self.env_type)
        self.llm_services = LLMServicesParams(env_type=self.env_type)

    def __str__(self) -> str:
        """Return the string representation of the object."""
        s = "LaifeParams:"
        s += f"\n{self.paths}"
        s += f"\n{self.llm_services}"
        return s

    def __repr__(self) -> str:
        """Return the string representation of the object."""
        return str(self)


def get_laife_params() -> LaifeParams:
    """Get the laife params."""
    return LaifeParams()


def get_laife_paths() -> LaifePaths:
    """Get the laife paths."""
    return get_laife_params().paths


def get_llm_services_params() -> LLMServicesParams:
    """Get the llm services params."""
    return get_laife_params().llm_services
