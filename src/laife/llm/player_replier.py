"""PlayerReplier - generates an in-character reply to an incoming player message."""

from dataclasses import dataclass

from pydantic import BaseModel

from laife.data_models.basemodel_kwargs import BaseModelKwargs
from laife.llm.prompt_loader import PromptLoader
from laife.llm.prompt_loader import PromptLoaderConfig
from laife.llm.structured_chain import StructuredLLMChain
from laife.llm_services.chat.config.base import ChatConfig


class PlayerReplyInput(BaseModelKwargs):
    """Input payload for PlayerReplier.ainvoke.

    Field names define the required variables that every prompt template must
    contain; the validation in StructuredLLMChain.__post_init__ derives the
    required set directly from these fields so the two can never drift apart.

    This class must never hold asyncio objects - it is called from inside
    WorldRunner.handle_player_input and must remain free of world I/O.
    """

    sender_name: str
    sender_prompt: str
    message: str
    own_state: str
    own_mission: str
    own_history: str


class PlayerReplyOutput(BaseModel):
    """Structured output returned by the replier LLM."""

    reply: str


class PlayerReplierConfig(BaseModel):
    """Configuration for a PlayerReplier."""

    chat_config: ChatConfig
    prompt_loader_config: PromptLoaderConfig


@dataclass
class PlayerReplier:
    """Generate an in-character reply to a message from another player.

    Instantiate with a :class:`PlayerReplierConfig`.  Calling :meth:`ainvoke`
    returns a :class:`PlayerReplyOutput` whose ``reply`` string should be
    forwarded back to the sender via :class:`~laife.entities.world_channel.WResInteract`.

    This class must never put anything onto an asyncio queue.  It
    only awaits the external LLM network call, making it safe to call
    directly from inside the world simulation loop.
    """

    config: PlayerReplierConfig

    def __post_init__(self) -> None:
        """Build the underlying structured chain."""
        prompt_str = PromptLoader(self.config.prompt_loader_config).load_prompt()
        self._chain: StructuredLLMChain[PlayerReplyInput, PlayerReplyOutput] = StructuredLLMChain(
            chat_config=self.config.chat_config,
            prompt_str=prompt_str,
            input_model=PlayerReplyInput,
            output_model=PlayerReplyOutput,
        )

    async def ainvoke(self, reply_input: PlayerReplyInput) -> PlayerReplyOutput:
        """Generate a reply asynchronously."""
        return await self._chain.ainvoke(reply_input)
