from __future__ import annotations

import logging
import sqlite3

import aiosqlite

SCHEMA_VERSION = 31


async def _readSchemaVersion(db: aiosqlite.Connection) -> int:
    async with db.execute("PRAGMA user_version;") as cursor:
        row = await cursor.fetchone()
    if row is None:
        return 0
    try:
        return int(row[0] or 0)
    except (TypeError, ValueError):
        return 0


async def _writeSchemaVersion(db: aiosqlite.Connection, version: int) -> None:
    safeVersion = max(0, int(version or 0))
    cursor = await db.execute(f"PRAGMA user_version={safeVersion};")
    await cursor.close()


async def applySchema(
    db: aiosqlite.Connection,
    *,
    logger: logging.Logger,
) -> None:
    async def _executeOptional(statement: str) -> None:
        try:
            await db.execute(statement)
        except sqlite3.OperationalError as exc:
            message = str(exc).lower()
            if "duplicate column name" in message or "already exists" in message:
                return
            raise

    await db.execute("PRAGMA journal_mode=WAL;")
    await db.execute("PRAGMA synchronous=NORMAL;")
    await db.execute("BEGIN IMMEDIATE;")
    currentVersion = await _readSchemaVersion(db)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS roblox_identity_links (
            discordUserId INTEGER PRIMARY KEY,
            robloxUserId INTEGER,
            robloxUsername TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT '',
            guildId INTEGER NOT NULL DEFAULT 0,
            confidence INTEGER NOT NULL DEFAULT 0,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            updatedAt TEXT NOT NULL DEFAULT (datetime('now')),
            lastUsedAt TEXT
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_events (
            eventId INTEGER PRIMARY KEY AUTOINCREMENT,
            guildId INTEGER NOT NULL,
            channelId INTEGER NOT NULL,
            messageId INTEGER NOT NULL DEFAULT 0,
            creatorId INTEGER NOT NULL,
            title TEXT NOT NULL,
            subtitle TEXT,
            eventAtUtc TEXT NOT NULL,
            timezone TEXT NOT NULL,
            maxAttendees INTEGER NOT NULL DEFAULT 0,
            lockRsvpAtStart INTEGER NOT NULL DEFAULT 0,
            pingRoleIdsJson TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'ACTIVE', -- ACTIVE/DELETED
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            updatedAt TEXT NOT NULL DEFAULT (datetime('now')),
            deletedAt TEXT,
            reminderSentAt TEXT,
            reminderThreadId INTEGER
        );
        """)
    await _executeOptional("ALTER TABLE scheduled_events ADD COLUMN maxAttendees INTEGER NOT NULL DEFAULT 0")
    await _executeOptional("ALTER TABLE scheduled_events ADD COLUMN lockRsvpAtStart INTEGER NOT NULL DEFAULT 0")
    await _executeOptional("ALTER TABLE scheduled_events ADD COLUMN pingRoleIdsJson TEXT NOT NULL DEFAULT '[]'")
    await _executeOptional("ALTER TABLE scheduled_events ADD COLUMN reminderSentAt TEXT")
    await _executeOptional("ALTER TABLE scheduled_events ADD COLUMN reminderThreadId INTEGER")
    await db.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_event_rsvps (
            eventId INTEGER NOT NULL,
            userId INTEGER NOT NULL,
            response TEXT NOT NULL, -- ATTENDING/TENTATIVE
            updatedAt TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (eventId, userId)
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS mcstatus (
            statusMessageId INTEGER NOT NULL,
            lastStatus TEXT NOT NULL,
            lastPlayerCount INTEGER NOT NULL,
            lastMaintenanceDate TEXT NOT NULL,
            statusChannelId INTEGER NOT NULL
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS curfew_targets (
            orgKey TEXT NOT NULL DEFAULT '',
            guildId INTEGER NOT NULL,
            userId INTEGER NOT NULL,
            timezone TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            addedBy INTEGER NOT NULL,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            updatedAt TEXT NOT NULL DEFAULT (datetime('now')),
            lastAppliedAt TEXT,
            PRIMARY KEY (guildId, userId)
        );
        """)
    await _executeOptional("ALTER TABLE curfew_targets ADD COLUMN orgKey TEXT NOT NULL DEFAULT ''")
    await db.execute("""
        CREATE TABLE IF NOT EXISTS jail_records (
            recordId INTEGER PRIMARY KEY AUTOINCREMENT,
            guildId INTEGER NOT NULL,
            userId INTEGER NOT NULL,
            jailedBy INTEGER NOT NULL,
            jailedRoleId INTEGER NOT NULL,
            jailChannelId INTEGER,
            savedRoleIdsJson TEXT NOT NULL,
            unmanageableRoleIdsJson TEXT NOT NULL,
            isolatedChannelIdsJson TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE', -- ACTIVE/REPLACED/RELEASED
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            updatedAt TEXT NOT NULL DEFAULT (datetime('now')),
            releasedBy INTEGER,
            releasedAt TEXT
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS best_of_polls (
            pollId INTEGER PRIMARY KEY AUTOINCREMENT,
            guildId INTEGER NOT NULL,
            channelId INTEGER NOT NULL,
            messageId INTEGER NOT NULL DEFAULT 0,
            createdBy INTEGER NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN', -- OPEN/CLOSED
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            closedBy INTEGER,
            closedAt TEXT
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS best_of_poll_candidates (
            pollId INTEGER NOT NULL,
            userId INTEGER NOT NULL,
            priorityRank INTEGER NOT NULL,
            priorityLabel TEXT NOT NULL,
            displayName TEXT NOT NULL DEFAULT '',
            sortOrder INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (pollId, userId)
        );
        """)
    await _executeOptional("ALTER TABLE best_of_poll_candidates ADD COLUMN displayName TEXT NOT NULL DEFAULT ''")
    await db.execute("""
        CREATE TABLE IF NOT EXISTS best_of_poll_votes (
            pollId INTEGER NOT NULL,
            voterId INTEGER NOT NULL,
            candidateUserId INTEGER NOT NULL,
            updatedAt TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (pollId, voterId)
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS best_of_poll_section_votes (
            pollId INTEGER NOT NULL,
            voterId INTEGER NOT NULL,
            sectionLabel TEXT NOT NULL,
            candidateUserId INTEGER NOT NULL,
            updatedAt TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (pollId, voterId, sectionLabel)
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS hall_reaction_posts (
            messageId INTEGER NOT NULL,
            hallType TEXT NOT NULL, -- FAME/SHAME
            guildId INTEGER NOT NULL,
            sourceChannelId INTEGER NOT NULL,
            targetChannelId INTEGER NOT NULL,
            sourceAuthorId INTEGER NOT NULL,
            reactionEmoji TEXT NOT NULL,
            reactionCount INTEGER NOT NULL DEFAULT 0,
            reactionBreakdownJson TEXT NOT NULL DEFAULT '{}',
            postedMessageId INTEGER,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (messageId, hallType)
        );
        """)
    await _executeOptional("ALTER TABLE hall_reaction_posts ADD COLUMN reactionBreakdownJson TEXT NOT NULL DEFAULT '{}'")
    await db.execute("""
        CREATE TABLE IF NOT EXISTS silly_gambling_wallets (
            userId INTEGER PRIMARY KEY,
            balance INTEGER NOT NULL DEFAULT 1000,
            gamesPlayed INTEGER NOT NULL DEFAULT 0,
            totalLost INTEGER NOT NULL DEFAULT 0,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            updatedAt TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS silly_gambling_api_credits (
            requestId TEXT PRIMARY KEY,
            userId INTEGER NOT NULL,
            points INTEGER NOT NULL DEFAULT 0,
            directDollars INTEGER NOT NULL DEFAULT 0,
            creditedDollars INTEGER NOT NULL,
            conversionRate INTEGER NOT NULL DEFAULT 5,
            source TEXT NOT NULL DEFAULT '',
            createdAt TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS community_polls (
            pollId INTEGER PRIMARY KEY AUTOINCREMENT,
            guildId INTEGER NOT NULL,
            channelId INTEGER NOT NULL,
            messageId INTEGER NOT NULL DEFAULT 0,
            creatorId INTEGER NOT NULL,
            question TEXT NOT NULL,
            optionsJson TEXT NOT NULL,
            anonymous INTEGER NOT NULL DEFAULT 0,
            multiSelect INTEGER NOT NULL DEFAULT 0,
            roleGateIdsJson TEXT NOT NULL DEFAULT '[]',
            hideResultsUntilClosed INTEGER NOT NULL DEFAULT 0,
            messageResultsToCreator INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'OPEN', -- OPEN/CLOSED
            closesAt TEXT,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            updatedAt TEXT NOT NULL DEFAULT (datetime('now')),
            closedAt TEXT
        );
        """)
    for statement in (
        "ALTER TABLE community_polls ADD COLUMN anonymous INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE community_polls ADD COLUMN multiSelect INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE community_polls ADD COLUMN roleGateIdsJson TEXT NOT NULL DEFAULT '[]'",
        "ALTER TABLE community_polls ADD COLUMN hideResultsUntilClosed INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE community_polls ADD COLUMN messageResultsToCreator INTEGER NOT NULL DEFAULT 0"
    ):
        await _executeOptional(statement)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS community_poll_votes (
            pollId INTEGER NOT NULL,
            userId INTEGER NOT NULL,
            optionIndex INTEGER NOT NULL,
            optionIndexesJson TEXT,
            updatedAt TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (pollId, userId)
        );
        """)
    await _executeOptional("ALTER TABLE community_poll_votes ADD COLUMN optionIndexesJson TEXT")
    await db.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            reminderId INTEGER PRIMARY KEY AUTOINCREMENT,
            guildId INTEGER NOT NULL,
            channelId INTEGER NOT NULL,
            userId INTEGER NOT NULL,
            reminderText TEXT NOT NULL,
            remindAtUtc TEXT NOT NULL,
            targetType TEXT NOT NULL DEFAULT 'USER', -- USER/ROLE
            targetRoleIdsJson TEXT NOT NULL DEFAULT '[]',
            recurringIntervalSec INTEGER NOT NULL DEFAULT 0,
            sourceReminderId INTEGER,
            status TEXT NOT NULL DEFAULT 'PENDING', -- PENDING/SENT/CANCELED
            dmDelivered INTEGER NOT NULL DEFAULT 0,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            updatedAt TEXT NOT NULL DEFAULT (datetime('now')),
            sentAt TEXT
        );
        """)
    for statement in (
        "ALTER TABLE reminders ADD COLUMN targetType TEXT NOT NULL DEFAULT 'USER'",
        "ALTER TABLE reminders ADD COLUMN targetRoleIdsJson TEXT NOT NULL DEFAULT '[]'",
        "ALTER TABLE reminders ADD COLUMN recurringIntervalSec INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE reminders ADD COLUMN sourceReminderId INTEGER",
    ):
        await _executeOptional(statement)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS suggestions (
            suggestionId INTEGER PRIMARY KEY AUTOINCREMENT,
            guildId INTEGER NOT NULL,
            channelId INTEGER NOT NULL,
            messageId INTEGER NOT NULL DEFAULT 0,
            submitterId INTEGER NOT NULL,
            content TEXT NOT NULL,
            anonymous INTEGER NOT NULL DEFAULT 0,
            threadId INTEGER,
            freedcampId INTEGER,
            status TEXT NOT NULL DEFAULT 'PENDING', -- PENDING/APPROVED/REJECTED/IMPLEMENTED
            reviewerId INTEGER,
            reviewNote TEXT,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            updatedAt TEXT NOT NULL DEFAULT (datetime('now')),
            reviewedAt TEXT
        );
        """)
    for statement in (
        "ALTER TABLE suggestions ADD COLUMN anonymous INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE suggestions ADD COLUMN threadId INTEGER",
        "ALTER TABLE suggestions ADD COLUMN freedcampId INTEGER",
    ):
        await _executeOptional(statement)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS suggestion_status_boards (
            messageId INTEGER PRIMARY KEY,
            guildId INTEGER NOT NULL,
            channelId INTEGER NOT NULL,
            createdAt TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS guild_stats_snapshots (
            snapshotId INTEGER PRIMARY KEY AUTOINCREMENT,
            guildId INTEGER NOT NULL,
            memberCount INTEGER NOT NULL DEFAULT 0,
            humanCount INTEGER NOT NULL DEFAULT 0,
            botCount INTEGER NOT NULL DEFAULT 0,
            textChannelCount INTEGER NOT NULL DEFAULT 0,
            voiceChannelCount INTEGER NOT NULL DEFAULT 0,
            forumChannelCount INTEGER NOT NULL DEFAULT 0,
            stageChannelCount INTEGER NOT NULL DEFAULT 0,
            roleCount INTEGER NOT NULL DEFAULT 0,
            boostCount INTEGER NOT NULL DEFAULT 0,
            capturedAt TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS guild_member_activity_daily (
            guildId INTEGER NOT NULL,
            activityDate TEXT NOT NULL,
            joinCount INTEGER NOT NULL DEFAULT 0,
            leaveCount INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (guildId, activityDate)
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS guild_channel_activity_daily (
            guildId INTEGER NOT NULL,
            channelId INTEGER NOT NULL,
            activityDate TEXT NOT NULL,
            messageCount INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (guildId, channelId, activityDate)
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS guild_feature_flags (
            guildId INTEGER NOT NULL,
            featureKey TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            updatedBy INTEGER,
            updatedAt TEXT NOT NULL DEFAULT (datetime('now')),
            note TEXT,
            PRIMARY KEY (guildId, featureKey)
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS audit_events (
            eventId INTEGER PRIMARY KEY AUTOINCREMENT,
            guildId INTEGER NOT NULL DEFAULT 0,
            actorId INTEGER NOT NULL DEFAULT 0,
            source TEXT NOT NULL,
            action TEXT NOT NULL,
            targetType TEXT NOT NULL DEFAULT '',
            targetId TEXT NOT NULL DEFAULT '',
            severity TEXT NOT NULL DEFAULT 'INFO',
            detailsJson TEXT NOT NULL DEFAULT '{}',
            authorizedBy TEXT NOT NULL DEFAULT '',
            createdAt TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS reaction_role_entries (
            entryId INTEGER PRIMARY KEY AUTOINCREMENT,
            guildId INTEGER NOT NULL,
            channelId INTEGER NOT NULL,
            messageId INTEGER NOT NULL,
            emojiKey TEXT NOT NULL,
            roleId INTEGER NOT NULL,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(messageId, emojiKey)
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS button_role_entries (
            entryId INTEGER PRIMARY KEY AUTOINCREMENT,
            guildId INTEGER NOT NULL,
            channelId INTEGER NOT NULL,
            messageId INTEGER NOT NULL,
            roleId INTEGER NOT NULL,
            buttonLabel TEXT NOT NULL DEFAULT '',
            emojiSpec TEXT NOT NULL DEFAULT '',
            orderIndex INTEGER NOT NULL DEFAULT 0,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(messageId, roleId)
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS blocked_self_roles (
            guildId INTEGER NOT NULL,
            roleId INTEGER NOT NULL,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (guildId, roleId)
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS link_hub_boards (
            hubId INTEGER PRIMARY KEY AUTOINCREMENT,
            guildId INTEGER NOT NULL,
            channelId INTEGER NOT NULL,
            rootMessageId INTEGER NOT NULL DEFAULT 0,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            createdBy INTEGER NOT NULL DEFAULT 0,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            updatedAt TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(guildId, channelId)
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS link_hub_sections (
            sectionId INTEGER PRIMARY KEY AUTOINCREMENT,
            hubId INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            sortOrder INTEGER NOT NULL DEFAULT 0,
            messageId INTEGER NOT NULL DEFAULT 0,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            updatedAt TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (hubId) REFERENCES link_hub_boards(hubId) ON DELETE CASCADE
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS link_hub_entries (
            entryId INTEGER PRIMARY KEY AUTOINCREMENT,
            sectionId INTEGER NOT NULL,
            entryType TEXT NOT NULL DEFAULT 'DOCUMENT',
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            sortOrder INTEGER NOT NULL DEFAULT 0,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            updatedAt TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (sectionId) REFERENCES link_hub_sections(sectionId) ON DELETE CASCADE
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS retry_jobs (
            jobId INTEGER PRIMARY KEY AUTOINCREMENT,
            jobType TEXT NOT NULL,
            payloadJson TEXT NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'PENDING', -- PENDING/PROCESSING/FAILED/DEAD/DONE
            attempts INTEGER NOT NULL DEFAULT 0,
            maxAttempts INTEGER NOT NULL DEFAULT 5,
            nextAttemptAt TEXT NOT NULL DEFAULT (datetime('now')),
            lastError TEXT,
            source TEXT NOT NULL DEFAULT '',
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            updatedAt TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS db_schema_migrations (
            migrationId INTEGER PRIMARY KEY AUTOINCREMENT,
            fromVersion INTEGER NOT NULL,
            toVersion INTEGER NOT NULL,
            appliedAt TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
    # Hot-path indexes
    indexStatements = (
        "CREATE INDEX IF NOT EXISTS idx_roblox_identity_username ON roblox_identity_links(robloxUsername)",
        "CREATE INDEX IF NOT EXISTS idx_roblox_identity_updated ON roblox_identity_links(updatedAt)",
        "CREATE INDEX IF NOT EXISTS idx_scheduled_events_status_time ON scheduled_events(status, eventAtUtc)",
        "CREATE INDEX IF NOT EXISTS idx_scheduled_events_message ON scheduled_events(messageId)",
        "CREATE INDEX IF NOT EXISTS idx_scheduled_event_rsvps_event_response ON scheduled_event_rsvps(eventId, response, updatedAt)",
        "CREATE INDEX IF NOT EXISTS idx_curfew_targets_enabled ON curfew_targets(enabled, guildId, userId)",
        "CREATE INDEX IF NOT EXISTS idx_curfew_targets_org_enabled ON curfew_targets(orgKey, enabled, userId)",
        "CREATE INDEX IF NOT EXISTS idx_jail_records_active ON jail_records(guildId, userId, status, createdAt)",
        "CREATE INDEX IF NOT EXISTS idx_best_of_polls_status ON best_of_polls(guildId, status, createdAt)",
        "CREATE INDEX IF NOT EXISTS idx_best_of_candidates_poll_rank ON best_of_poll_candidates(pollId, priorityRank, sortOrder)",
        "CREATE INDEX IF NOT EXISTS idx_best_of_votes_poll_candidate ON best_of_poll_votes(pollId, candidateUserId)",
        "CREATE INDEX IF NOT EXISTS idx_best_of_section_votes_poll_section_candidate ON best_of_poll_section_votes(pollId, sectionLabel, candidateUserId)",
        "CREATE INDEX IF NOT EXISTS idx_best_of_section_votes_poll_voter ON best_of_poll_section_votes(pollId, voterId)",
        "CREATE INDEX IF NOT EXISTS idx_hall_posts_target_created ON hall_reaction_posts(targetChannelId, createdAt)",
        "CREATE INDEX IF NOT EXISTS idx_gambling_wallet_balance ON silly_gambling_wallets(balance)",
        "CREATE INDEX IF NOT EXISTS idx_gambling_api_credits_user_created ON silly_gambling_api_credits(userId, createdAt)",
        "CREATE INDEX IF NOT EXISTS idx_community_polls_status_closes ON community_polls(guildId, status, closesAt)",
        "CREATE INDEX IF NOT EXISTS idx_community_polls_message ON community_polls(messageId)",
        "CREATE INDEX IF NOT EXISTS idx_community_poll_votes_poll_option ON community_poll_votes(pollId, optionIndex)",
        "CREATE INDEX IF NOT EXISTS idx_reminders_status_time ON reminders(status, remindAtUtc)",
        "CREATE INDEX IF NOT EXISTS idx_reminders_user_status ON reminders(guildId, userId, status, remindAtUtc)",
        "CREATE INDEX IF NOT EXISTS idx_suggestions_status_created ON suggestions(guildId, status, createdAt)",
        "CREATE INDEX IF NOT EXISTS idx_suggestions_message ON suggestions(messageId)",
        "CREATE INDEX IF NOT EXISTS idx_suggestions_thread ON suggestions(threadId)",
        "CREATE INDEX IF NOT EXISTS idx_suggestion_boards_guild ON suggestion_status_boards(guildId, channelId)",
        "CREATE INDEX IF NOT EXISTS idx_guild_stats_snapshots_guild_time ON guild_stats_snapshots(guildId, capturedAt)",
        "CREATE INDEX IF NOT EXISTS idx_guild_member_activity_daily_guild_date ON guild_member_activity_daily(guildId, activityDate)",
        "CREATE INDEX IF NOT EXISTS idx_guild_channel_activity_daily_guild_date ON guild_channel_activity_daily(guildId, activityDate)",
        "CREATE INDEX IF NOT EXISTS idx_feature_flags_guild_key ON guild_feature_flags(guildId, featureKey)",
        "CREATE INDEX IF NOT EXISTS idx_audit_events_guild_created ON audit_events(guildId, createdAt)",
        "CREATE INDEX IF NOT EXISTS idx_audit_events_source_created ON audit_events(source, createdAt)",
        "CREATE INDEX IF NOT EXISTS idx_reaction_roles_message ON reaction_role_entries(messageId)",
        "CREATE INDEX IF NOT EXISTS idx_reaction_roles_guild_channel ON reaction_role_entries(guildId, channelId)",
        "CREATE INDEX IF NOT EXISTS idx_button_roles_message ON button_role_entries(messageId, orderIndex)",
        "CREATE INDEX IF NOT EXISTS idx_button_roles_guild_channel ON button_role_entries(guildId, channelId)",
        "CREATE INDEX IF NOT EXISTS idx_blocked_self_roles_guild ON blocked_self_roles(guildId)",
        "CREATE INDEX IF NOT EXISTS idx_link_hubs_guild_channel ON link_hub_boards(guildId, channelId)",
        "CREATE INDEX IF NOT EXISTS idx_link_hub_sections_hub_sort ON link_hub_sections(hubId, sortOrder, sectionId)",
        "CREATE INDEX IF NOT EXISTS idx_link_hub_entries_section_sort ON link_hub_entries(sectionId, sortOrder, entryId)",
        "CREATE INDEX IF NOT EXISTS idx_retry_jobs_status_next ON retry_jobs(status, nextAttemptAt)",
        "CREATE INDEX IF NOT EXISTS idx_retry_jobs_type_status ON retry_jobs(jobType, status, updatedAt)",
    )
    for statement in indexStatements:
        await db.execute(statement)
    if currentVersion < SCHEMA_VERSION:
        await db.execute(
            """
                INSERT INTO db_schema_migrations (fromVersion, toVersion)
                VALUES (?, ?)
                """,
            (currentVersion, SCHEMA_VERSION),
        )
        await _writeSchemaVersion(db, SCHEMA_VERSION)
    await db.commit()
    if currentVersion < SCHEMA_VERSION:
        logger.info(
            "Database schema upgraded: v%s -> v%s",
            currentVersion,
            SCHEMA_VERSION,
        )
