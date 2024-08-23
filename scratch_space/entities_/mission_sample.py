"""Print a bunch of missions."""

# %% imports

from laife.llm.mission import Mission, MissionHistoryEntry, MissionStatus

# %% simple mission

mission = Mission("Do the thing")
print(mission.to_prompt())

# %% history

mission.add_history_entry("try", "success")
print(mission.to_prompt())

# another
mission.add_history_entry("try", "failure")
print(mission.to_prompt())

# %% sub missions

sub_mission = Mission("Do the other thing", sub_level=1)
mission.add_sub_mission(sub_mission)
print(mission.to_prompt())

# %%
