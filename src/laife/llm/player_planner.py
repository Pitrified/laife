"""Player planner - decomposes a mission into ordered sub-missions via an LLM."""

from dataclasses import dataclass

from llm_core.chains.structured_chain import StructuredLLMChain
from llm_core.chat.config.base import ChatConfig
from llm_core.prompts.prompt_loader import PromptLoader
from llm_core.prompts.prompt_loader import PromptLoaderConfig
from pydantic import BaseModel
from pydantic import Field

from laife.data_models.basemodel_kwargs import BaseModelKwargs
from laife.entities.world_map_observation import WorldMapObservation
from laife.llm.mission import Mission
from laife.llm.mission import MissionHistory


class PlayerPlannerInput(BaseModelKwargs):
    """Input payload for PlayerPlanner.invoke / ainvoke.

    Field names define the required variables that every prompt template must
    contain; the validation in StructuredLLMChain.__post_init__ derives the
    required set directly from these fields so the two can never drift apart.
    """

    mission: str
    history: str
    observation: str
    player_state: str


class PlayerPlannerResult(BaseModel):
    """Structured output returned by the planner LLM."""

    sub_missions: list[str] = Field(
        ...,
        description="Ordered list of sub-mission objectives to complete the top-level mission.",
        min_length=1,
    )
    reason: str = Field(..., description="Why these sub-missions were chosen.")


class PlayerPlannerConfig(BaseModel):
    """Configuration for a PlayerPlanner."""

    chat_config: ChatConfig
    prompt_loader_config: PromptLoaderConfig


@dataclass
class PlayerPlanner:
    """Decompose a mission into ordered sub-missions using an LLM.

    Instantiate with a :class:`PlayerPlannerConfig`.  Calling :meth:`ainvoke`
    (or :meth:`invoke`) returns a :class:`PlayerPlannerResult` whose
    ``sub_missions`` list should be written into the current
    :class:`~laife.llm.mission.Mission` via ``add_sub_mission``.
    """

    config: PlayerPlannerConfig

    def __post_init__(self) -> None:
        """Build the underlying structured chain."""
        prompt_str = PromptLoader(self.config.prompt_loader_config).load_prompt()
        self._chain: StructuredLLMChain[PlayerPlannerInput, PlayerPlannerResult] = (
            StructuredLLMChain(
                chat_config=self.config.chat_config,
                prompt_str=prompt_str,
                input_model=PlayerPlannerInput,
                output_model=PlayerPlannerResult,
            )
        )

    def _build_input(
        self,
        mission: Mission,
        history: MissionHistory,
        observation: WorldMapObservation,
        player_state: str,
    ) -> PlayerPlannerInput:
        return PlayerPlannerInput(
            mission=mission.to_prompt(),
            history=history.to_prompt(),
            observation=observation.to_prompt(),
            player_state=player_state,
        )

    def invoke(
        self,
        mission: Mission,
        history: MissionHistory,
        observation: WorldMapObservation,
        player_state: str,
    ) -> PlayerPlannerResult:
        """Decompose the mission synchronously and return the planning result."""
        return self._chain.invoke(self._build_input(mission, history, observation, player_state))

    async def ainvoke(
        self,
        mission: Mission,
        history: MissionHistory,
        observation: WorldMapObservation,
        player_state: str,
    ) -> PlayerPlannerResult:
        """Decompose the mission asynchronously and return the planning result."""
        return await self._chain.ainvoke(
            self._build_input(mission, history, observation, player_state)
        )
