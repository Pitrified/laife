# Player brain

The player brain is responsible for in general interacting with the language model.

Setup

1. PromptLoaderConfig has to be created, with matching PromptLoader which is a simple tool to load the prompts as string from disk
   - config has to receive in init base_prompt_fol / prompt_name / version which leads to the file as jinja
     eg `src/laife/prompts/player_brain/v1.jinja`
     when using this class, base_prompt_fol can be get from the PathParams
   - the PromptLoader gets the config and has a `load_prompt` method that returns the prompt as string,
     jinja template is not loaded/rendered at this step, just loaded as string
   - prompt loader has some mechanism to get latest version of the prompt if special `version="auto"` is given in the config,
     by looking at the files in the base_prompt_fol and finding the one with the highest version number
   - prompt string is cached in an attribute
   - prompt loader works for a single config
   - `prompt_str = PromptLoader(config).load_prompt()`
1. receive a PlayerBrainConfig(BaseModel) in brain init
   which contains as attribute
   - chat_config: ChatConfig
   - prompt_loader_config: PromptLoaderConfig

Thinking

1. prerequisite: the player does a "look around" action, and receives a description of the environment every time
   - create the action `ActionObserve` that the player can do to receive the description of the environment,
     which is stored in the player state as `last_observation`
   - stub version of the action handlers for now in player and world, but ready to be implemented later
2. the player has
   - a list of possible actions --> known at compile time in theory, dynamically get schema of `Actions` if possible
   - the current mission/submission/parent mission
   - the history of the mission (actions done, feedback received)
   - the current state of the world (from the "look around" action)
   - the player state (health, inventory, position, etc.) (for now just position, but easily extendable)
3. the player brain takes all of this information and generates an action to do
   - leverage `ActionPicker` by feeding all the information as context in args of invoke and leveraging the chain pattern of langchain to use it
4. the action is sent to the world, and the world responds with a feedback, which is added to the history of the mission
   - the feedback can be a success (that is, that mission is done), a failure, always with some information about the result of the action
   - stub for now (already existing)
5. the player brain iterates on the mission with the new history, and can pick a different action if needed
   - stub for now, leave `ActionPlan` for later
