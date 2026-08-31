from __future__ import annotations

from .env import _envFlag, _envInt, _envText

# == Core Bot ==
# Jane's Discord bot token. Keep this in `.env`, not in versioned config.
token = _envText("DISCORD_BOT_TOKEN")

# Primary servers.
serverId = 0
# JANE_TEST_GUILD_ID lets each machine point at its own dev guild.
# Falls back to the shared default below.
serverIdTesting = 0
testGuildIds = []


# == Credentials / External APIs ==
# Keep API keys and credential paths in `.env`, not in versioned config.
# Roblox and RoVer credentials.
robloxOpenCloudApiKey = _envText("ROBLOX_OPEN_CLOUD_API_KEY")
roverApiKey = _envText("ROVER_API_KEY")
gamblingApiToken = _envText("JANE_GAMBLING_API_TOKEN")


# == Command Access / Runtime ==
# Allowed servers for command usage.
allowedCommandGuildIds = []

# Reserved runtime override users.
overridingUserIds = []
# Command sync toggles.
clearGlobalCommands = False
clearGuildCommands = False

# Unknown guilds never receive commands. Diagnostic invite creation is also
# off by default because invite URLs grant access to another server. If it is
# deliberately enabled, the runtime enforces bounded age and use counts.
unknownGuildInviteCreationEnabled = False
unknownGuildInviteMaxAgeSec = 300
unknownGuildInviteMaxUses = 1

# Temporary command lock.
temporaryCommandLockEnabled = False
temporaryCommandAllowedUserIds = []

# Runtime / diagnostics access.
errorMirrorUserId = 0
janeTerminalAllowedUserId = errorMirrorUserId
opsAllowedUserIds = []
runtimeControlAllowedUserIds = []
permissionSimulatorGuildIds = []

# Runtime task tuning.
runtimeBudgetRobloxConcurrency = 6
runtimeBudgetLowPriorityRobloxPriority = 50
runtimeBudgetLowestPriorityRobloxPriority = 1000
runtimeBudgetInteractiveDiscordPriority = -100
runtimeBudgetLowPriorityDiscordPriority = 50
runtimeBudgetLowestPriorityDiscordPriority = 1000
runtimeBudgetSheetsConcurrency = 2
runtimeBudgetInteractiveSheetsConcurrency = 2
runtimeBudgetBackgroundSheetsConcurrency = 1
runtimeBudgetDiscordConcurrency = 6
runtimeBudgetInteractionAckConcurrency = 24
runtimeBudgetBackgroundConcurrency = 2
runtimeTaskStatsPath = "runtime/data/task-stats.json"
eventLoopWatchdogEnabled = True
eventLoopWatchdogIntervalSec = 5.0
eventLoopWatchdogWarnAfterSec = 2.0
eventLoopWatchdogStackTaskLimit = 8

# Runtime database snapshots stay local/ignored. They are intentionally not
# committed to git, but they give us a recoverable DB copy around restarts.
dbRuntimeSnapshotEnabled = True
dbRuntimeSnapshotOnStartup = True
dbRuntimeSnapshotOnShutdown = True
dbRuntimeSnapshotDir = "backups/dbSnapshots"
dbRuntimeSnapshotRetention = 20
dbRuntimeDiagnosticReportPath = "runtime/data/db-state/latest.json"
runtimeTaskStatsFlushIntervalSec = 30
runtimeTaskStatsFlushDirtyCount = 25
discordEntityCacheTtlSec = 300
retryQueuePollIntervalSec = 6
retryQueueInitialDelaySec = 30
webhookHealthCheckIntervalSec = 600
webhookHealthInitialDelaySec = 180
webhookHealthMaxRowsPerRun = 50
reminderDueBatchLimit = 20
reminderDeliveryConcurrency = 3
generalErrorLogDir = ""
generalErrorLogMaxBytes = 2 * 1024 * 1024
generalErrorLogBackupCount = 5
automationReportChannelId = 0
autoGitUpdateEnabled = False
enablePrivateExtensions = False
enableDestructiveCommands = False
destructiveCommandsDryRun = True
disableGitPullOnManualRestart = True
allowGitPullOnManualRestart = False
autoGitUpdateRemote = "origin"
autoGitUpdateBranch = ""
autoGitUpdateCheckIntervalSec = 60
autoGitUpdateInitialDelaySec = 120
autoGitUpdatePauseDrainSec = 5
autoGitUpdateInstallRequirements = _envFlag("JANE_INSTALL_REQUIREMENTS_ON_UPDATE", False)
autoGitUpdateDependencyInstallTimeoutSec = 600
# Timeout for individual git fetch/pull/stash/status commands.
autoGitUpdateGitCommandTimeoutSec = 120
# Extra paths to preserve in addition to the updater's built-in runtime defaults.
autoGitUpdatePreservePaths = [
    "backups/serverSnapshots",
    "backups/serverSnapshotsOffsite",
]
copyServerRoleBatchCreateLimit = 12
copyServerRoleBatchMutationLimit = 18

# Optional extension layers.
extraExtensionNames: list[str] = []
destructiveCommandGuildIds = []
destructiveCommandCooldownSec = 30

# Optional config sanity suppressions (ID keys intentionally left unset).
configSanityOptionalIdKeys = [
    "bestOfFormerMrRoleId",
    "bestOfFormerHrRoleId",
    "bestOfFormerAnrocomRoleId",
    "bestOfAnrocomRoleId",
]


# == Shared Role IDs ==
# Core moderation / training roles.
moderatorRoleId = 0
instructorRoleId = 0

# Shared rank / clearance roles.
middleRankRoleId = 0
highRankRoleId = 0
