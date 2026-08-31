from __future__ import annotations

from .core import *
from .staff import *
from .operations import *
from .env import _envFlag, _envInt, _envText

# == Best Of ==
bestOfCommandRoleIds = []
bestOfRobloxLookupEnabled = True
bestOfRobloxLookupConcurrency = 8
bestOfRobloxLookupTimeoutSec = 3.0
# Best Of role priority (lowest -> highest):
# Former MR -> MR -> Former HR -> HR -> Former ANROCOM -> Command Staff -> ANROCOM
bestOfFormerMrRoleId = 0
bestOfMrRoleId = middleRankRoleId
bestOfFormerHrRoleId = 0
bestOfHrRoleId = highRankRoleId
bestOfFormerAnrocomRoleId = 0
bestOfFormerAnrocomRoleIds = []
bestOfCommandStaffRoleId = 0
bestOfAnrocomRoleIds = []


# == Hall of Fame / Shame ==
hallOfFameChannelId = 0
hallOfShameChannelId = 0
hallReactionThreshold = 5
hallUseWebhook = True
hallIgnoreBotMessages = True
hallAllowedCategoryIds = []


# == Voice Chat ==
_canCreateVoiceChatAll = []
_canCreateVoiceChatBasic = []

voiceChannelCreationCategory = 0
voiceChatRebalanceMaxPositionEdits = 4
voiceChatRebalanceEditDelaySec = 1.25
permanentVoiceChatChannelIds = []


# == Roblox / Identity ==
robloxGroupId = 0
robloxGroupUrl = ""

# Jane Identity links Discord users to Roblox accounts through a Discord-started
# Roblox OAuth flow. The web server only handles the OAuth callback.
roverApiBaseUrl = "https://registry.rover.link/api/guilds/{guildId}/discord-to-roblox/{discordId}"
roverApiKeyHeader = "Authorization"
roverApiKeyUseBearer = True
roverVerifyUrl = "https://rover.link/verify"
roverCacheTtlSec = 120
roverCacheMaxEntries = 2000
roverIdentityDbTimeoutSec = 1.5
robloxHttpTimeoutSec = 10
robloxGroupRolesCacheTtlSec = 3600


# == Roblox Flagging / Scanning ==
# If a passing attendee is in any of these groups, they are marked FLAGGED.
robloxFlagGroupIds = []

# Flag Roblox accounts younger than this many days (0 to disable).
robloxAccountAgeFlagDays = 100

# Group scan cache.
robloxGroupScanCacheDays = 7

# Badge scan.
robloxBadgeScanEnabled = True
robloxBadgeScanCacheDays = 7
robloxBadgeScanBatchSize = 100
robloxBadgeImportMax = 200

# Outfit viewer.
robloxOutfitScanEnabled = True
robloxOutfitScanCacheDays = 7
robloxOutfitMax = 0
robloxOutfitMaxPages = 20
robloxOutfitThumbSize = "420x420"

# Inventory scanning.
robloxInventoryScanEnabled = True
robloxInventoryScanCacheDays = 7
robloxInventoryScanMaxPages = 5


# == Gambling API ==
# Use 0.0.0.0 to allow external callers via token auth.
gamblingApiEnabled = True
gamblingApiHost = "0.0.0.0"
gamblingApiPort = 8787
gamblingApiMaxConcurrency = 8
gamblingPointsToDollarRate = 5  # 1 point => 5 anrobucks


# == Hidden / Misc ==
skinAllowedUserIds = []
skinCooldownBypassRoleIds = []


# == Organization Profiles ==
# Jane is still a single bot process, but org-specific settings now live behind
# profile keys so other groups can be added without turning config.py into a
# bigger singleton mess than it already is.
defaultOrganizationKey = ""
organizationCommandFeatureMap = {}
organizationProfiles = {}
guildOrganizationKeys = {}

minecraftAuthenticationToken = _envText("MINECRAFT_RCON_TOKEN")
minecraftRCONAddress = ""
minecraftRCONPort = 25575
minecraftRCONTimeoutSeconds = 5
minecraftServerMaxPlayersFallback = 60
minecraftAllowedRoleIds = []
minecraftCheckCooldownSeconds = 30
