"""Print a bunch of missions."""

# %% imports

from laife.entities.action import Action
from laife.entities.action import ActionBuild
from laife.entities.action import ActionCraft
from laife.llm.mission import Mission
from laife.llm.mission import MissionHistory
from laife.llm.mission import MissionHistoryEntry
from laife.llm.mission import MissionStatus

# %% simple mission

mission = Mission(objective="Build a settlement")
print(mission.to_prompt())

# %% mission with sub-missions

mission.add_sub_mission("Gather wood")
mission.add_sub_mission("Craft a hammer")
print(mission.to_prompt())

# %% nested sub-missions

sub = mission.steps[0]
sub.add_sub_mission("Find a forest")
sub.add_sub_mission("Chop trees")
print(sub.to_prompt())

# %% mission with statuses

m2 = Mission(objective="Craft a sword", status=MissionStatus.ACTIVE)
m2.add_sub_mission("Mine iron ore")
m2.steps[0].status = MissionStatus.COMPLETED
m2.add_sub_mission("Smelt iron")
print(m2.to_prompt())

# %% history

action1 = Action(
    act=ActionCraft(
        utensil_name="hammer",
        description="A sturdy wooden hammer",
    ),
    reason="Need a hammer to build the house",
)
entry1 = MissionHistoryEntry(action=action1, result="success")
history = MissionHistory(history=[entry1])
print(history.to_prompt())

# another entry
action2 = Action(
    act=ActionBuild(
        building_type="house",
        description="A small wooden house",
        size=3,
    ),
    reason="Build a shelter before nightfall",
)
entry2 = MissionHistoryEntry(action=action2, result="failure - not enough materials")
history.add_history_entry(entry2)
print(history.to_prompt())

# %%
