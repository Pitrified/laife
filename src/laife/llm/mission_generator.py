"""MissionGenerator - proposes a new mission objective via an LLM given world context."""

from dataclasses import dataclass

from llm_core.chains.structured_chain import StructuredLLMChain
from llm_core.chat.config.base import ChatConfig
from llm_core.prompts.prompt_loader import PromptLoader
from llm_core.prompts.prompt_loader import PromptLoaderConfig
from pydantic import BaseModel
from pydantic import Field

from laife.data_models.basemodel_kwargs import BaseModelKwargs
from laife.entities.world_map_observation import WorldMapObservation


class MissionGeneratorInput(BaseModelKwargs):
    """Input payload for MissionGenerator.invoke / ainvoke.

    Field names define the required variables that every prompt template must
    contain; the validation in StructuredLLMChain.__post_init__ derives the
    required set directly from these fields so the two can never drift apart.
    """

    observation: str
    player_state: str
    inventory: str


class MissionGeneratorResult(BaseModel):
    """Structured output returned by the mission-generator LLM."""

    objective: str = Field(
        ...,
        description="A single, concrete mission objective for the player to pursue.",
    )
    reason: str = Field(
        ...,
        description="Brief explanation of why this objective fits the current situation.",
    )


class MissionGeneratorConfig(BaseModel):
    """Configuration for a MissionGenerator."""

    chat_config: ChatConfig
    prompt_loader_config: PromptLoaderConfig


@dataclass
class MissionGenerator:
    """Propose a new mission objective for the player using an LLM.

    Instantiate with a :class:`MissionGeneratorConfig`.  Calling :meth:`ainvoke`
    (or :meth:`invoke`) returns a :class:`MissionGeneratorResult` whose
    ``objective`` string should be used to create a new :class:`~laife.llm.mission.Mission`.
    """

    config: MissionGeneratorConfig

    def __post_init__(self) -> None:
        """Build the underlying structured chain."""
        prompt_str = PromptLoader(self.config.prompt_loader_config).load_prompt()
        self._chain: StructuredLLMChain[MissionGeneratorInput, MissionGeneratorResult] = (
            StructuredLLMChain(
                chat_config=self.config.chat_config,
                prompt_str=prompt_str,
                input_model=MissionGeneratorInput,
                output_model=MissionGeneratorResult,
            )
        )

    def _build_input(
        self,
        observation: WorldMapObservation,
        player_state: str,
        inventory: str,
    ) -> MissionGeneratorInput:
        return MissionGeneratorInput(
            observation=observation.to_prompt(),
            player_state=player_state,
            inventory=inventory,
        )

    def invoke(
        self,
        observation: WorldMapObservation,
        player_state: str,
        inventory: str,
    ) -> MissionGeneratorResult:
        """Propose a mission objective synchronously."""
        return self._chain.invoke(self._build_input(observation, player_state, inventory))

    async def ainvoke(
        self,
        observation: WorldMapObservation,
        player_state: str,
        inventory: str,
    ) -> MissionGeneratorResult:
        """Propose a mission objective asynchronously."""
        return await self._chain.ainvoke(self._build_input(observation, player_state, inventory))
