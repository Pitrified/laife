"""Print a bunch of missions."""

# %% imports

from laife.llm.mission import Mission
from laife.llm.mission import MissionHistory
from laife.llm.mission import MissionHistoryEntry
from laife.llm.mission import MissionStatus
from laife.llm.mission import MissionStep
from laife.llm.mission import MissionType

# %% simple mission

ms = MissionStep(
    mission_type=MissionType.CRAFT,
    objective="Craft a hammer",
)
mission = Mission(steps=[ms])
print(mission.to_prompt())

# %% with step constructor

m2 = Mission.from_step(ms)
print(m2.to_prompt())

# %% add a step

ms2 = MissionStep(
    mission_type=MissionType.BUILD,
    objective="Build a house",
    status=MissionStatus.ACTIVE,
)
mission.add_step(ms2)
print(mission.to_prompt())

# %% all steps at once

m3 = Mission.from_steps(ms, ms2)
print(m3.to_prompt())

# %% history

mission_history_entry = MissionHistoryEntry(
    action="try",
    result="success",
)
mission_history = MissionHistory(history=[mission_history_entry])
print(mission.to_prompt())

# another
mhe2 = MissionHistoryEntry(
    action="try",
    result="failure",
)
mission_history.add_history_entry(mhe2)
print(mission_history.to_prompt())

# %%
