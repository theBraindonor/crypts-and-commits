# c001-boss-edition rumors

## Campaign deletion guard is misdescribed in the campaign-manager skills (found during e019)

Both providers' `campaign-manager` templates say campaign deletion protects "linked/historical memberships, reverse boss claims and archived state". In code (`core/coupling.py`, `campaign_operation("delete")`), deletion is blocked only by a non-empty `bosses` list or a reverse boss claim; the archived-state check explicitly exempts `delete`, so an archived bossless campaign can be deleted. Decide whether archived campaigns should be protected from deletion (a core change) or whether the skill wording should drop "archived state" (a template change). workflow.md and tool-reference.md now describe the current code behavior.

## Long-running MCP server needs a restart to see new docs (found during e019)

A crypts-and-commits MCP server started before `tool-reference` was registered keeps listing the old docs set until it restarts. Worth a line in the migration guide's redeployment steps if it bites adopters.