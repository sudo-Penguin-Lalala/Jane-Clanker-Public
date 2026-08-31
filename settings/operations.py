from __future__ import annotations

from .core import *
from .staff import *
from .env import _envText

# == Internal Link Hub ==
masterLinkHubManagerRoleIds = []
masterLinkHubWebhookName = "Jane Master Directory"
masterLinkHubWebhookAvatarUrl = ""


# == Public Utility / Suggestions ==
welcomeChannelId = 0
welcomeMessageTemplate = "Welcome to **{guild}**, {mention}."
publicRoleMenus = {}
reactionRoleCommandRoleIds = []
reactionRolePolicyRoleIds = []

suggestionChannelId = 0
suggestionForumChannelId = 0
suggestionReviewerRoleIds = []

# Optional Freedcamp task creation when suggestions are approved.
freedcampProjectId = 0
freedcampTaskGroupId = 0


# == Server Safety / Recovery ==
serverSafetyAlertChannelId = 0
serverSafetyAlertRoleId = 0
serverSafetySnapshotDir = ""
serverSafetyOffsiteSnapshotDir = ""
serverSafetyOffsiteSnapshotsEnabled = True
serverSafetyWeeklySnapshotKeepCount = 2
serverSafetyManualSnapshotKeepCount = 1
serverSafetyWeeklySnapshotGuildIds = []
serverSafetyQuarantineEnabled = False
serverSafetyIgnoredCategoryIds = []
serverSafetyPreservedChannelIds = []
serverSafetyQuarantineThreshold = 5
serverSafetyQuarantineWindowSec = 30
serverSafetyAllowedUserIds = []


# == Curfew / Jail ==
curfewCheckIntervalSec = 60
jailedRoleId = 0
jailedChannelId = 0
jailEnforceChannelIsolation = True


# Global Sheets throttling.
googleSheetsMinRequestIntervalSec = 0.05
googleSheetsMaxAttempts = 3
googleSheetsRetryBaseSec = 1.5

# Discord can occasionally 5xx during the first login/application_info call.
# Retry only startup transport/server failures; invalid token/config errors still fail fast.
discordStartupMaxAttempts = 6
discordStartupRetryBaseSec = 15
discordStartupRetryMaxDelaySec = 120

# Temporary identity backfill command: !pairDbNames
pairDbNamesSourceChannelId = 0
pairDbNamesLookbackDays = 5
pairDbNamesLookupConcurrency = 4
pairDbNamesMaxLookups = 500
pairDbNamesHistoryPageSize = 100
pairDbNamesHistoryMaxAttempts = 5
pairDbNamesHistoryRetryBaseSec = 2
pairDbNamesHistoryRetryMaxDelaySec = 20
