"""World judge - LLM-based validation of build, craft and complete requests."""

from typing import TYPE_CHECKING

from llm_core.chains.structured_chain import StructuredLLMChain
from llm_core.chat.config.base import ChatConfig
from llm_core.data_models.basemodel_kwargs import BaseModelKwargs
from llm_core.prompts.prompt_loader import PromptLoader
from llm_core.prompts.prompt_loader import PromptLoaderConfig
from pydantic import BaseModel

if TYPE_CHECKING:
    from laife.entities.building import Building


class WorldJudgeInput(BaseModelKwargs):
    """Input of the judge chains; the field names are the prompt variables."""

    action_type: str
    action_details: str
    observation: str
    player_state: str


class WorldJudgeResult(BaseModel):
    """Result from the world judge LLM."""

    success: bool
    feedback: str


class WorldJudgeConfig(BaseModel):
    """Configuration for the WorldJudge: one chat config, one prompt per judge."""

    chat_config: ChatConfig
    build_prompt: PromptLoaderConfig
    craft_prompt: PromptLoaderConfig
    complete_prompt: PromptLoaderConfig


class WorldJudge:
    """The world's LLM judgement: owns the build, craft and complete chains.

    Each method takes plain values and returns the verdict; acting on it is
    the runner's job.
    """

    def __init__(self, config: WorldJudgeConfig) -> None:
        """Build the three chains from config."""
        self.config = config
        self.build_chain = self._chain(config.build_prompt)
        self.craft_chain = self._chain(config.craft_prompt)
        self.complete_chain = self._chain(config.complete_prompt)

    def _chain(
        self, prompt: PromptLoaderConfig
    ) -> StructuredLLMChain[WorldJudgeInput, WorldJudgeResult]:
        """Build one judge chain on *prompt*."""
        return StructuredLLMChain(
            chat_config=self.config.chat_config,
            prompt_str=PromptLoader(prompt).load_prompt(),
            input_model=WorldJudgeInput,
            output_model=WorldJudgeResult,
        )

    async def check_build(
        self, building: Building, observation: str, player_state: str
    ) -> WorldJudgeResult:
        """Judge whether *building* can be built here."""
        return await self.build_chain.ainvoke(
            WorldJudgeInput(
                action_type="build",
                action_details=(
                    f"building_type={building.building_type.building_type}"
                    f", name={building.name}"
                    f", size={building.size}"
                    f", description={building.description}"
                ),
                observation=observation,
                player_state=player_state,
            )
        )

    async def check_craft(
        self, utensil_name: str, description: str, observation: str, player_state: str
    ) -> WorldJudgeResult:
        """Judge whether the utensil can be crafted here."""
        return await self.craft_chain.ainvoke(
            WorldJudgeInput(
                action_type="craft",
                action_details=f"utensil_name={utensil_name}, description={description}",
                observation=observation,
                player_state=player_state,
            )
        )

    async def check_complete(
        self, objective: str, outcome: str, observation: str, player_state: str
    ) -> WorldJudgeResult:
        """Judge whether *outcome* satisfies *objective*."""
        return await self.complete_chain.ainvoke(
            WorldJudgeInput(
                action_type=f"complete: {objective}",
                action_details=outcome,
                observation=observation,
                player_state=player_state,
            )
        )
