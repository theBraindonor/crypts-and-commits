import re

SOURCEBOOK_DIR_NAME = ".sourcebook"
LORE_DIR_NAME = "lore"
REGION_DIR_NAME = "region"
CAMPAIGN_DIR_NAME = "campaigns"
ENCOUNTER_DIR_NAME = "encounters"
NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
RESERVED_NAMES = frozenset({".", ".."})
WORLD_FILE_NAME = "world.md"
CAMPAIGN_STATUSES = ("draft", "open", "paused", "completed", "abandoned")
DEFAULT_CAMPAIGN_STATUS = "draft"
ENCOUNTER_STATUSES = ("draft", "reviewed", "open", "completed", "abandoned")
DEFAULT_ENCOUNTER_STATUS = "draft"
