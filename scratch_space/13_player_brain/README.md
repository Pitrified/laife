# Player brain

The player brain is responsible for in general interacting with the language model.

Setup

1. receive a PlayerBrainConfig(BaseModel) in init

Thinking

1. prerequisite: the player does a "look around" action, and receives a description of the environment every time
2. the player has
    - a list of possible actions    
    - the current mission/submission/parent mission
    - the history of the mission (actions done, feedback received)
    - the current state of the world (from the "look around" action)
    - the player state (health, inventory, position, etc.)
3. the player brain takes all of this information and generates an action to do
4. the action is sent to the world, and the world responds with a feedback, which is added to the history of the mission
    - the feedback can be a success (that is, that mission is done), a failure, always with some information about the result of the action
5. the player brain iterates on the mission with the new history, and can pick a different action if needed
