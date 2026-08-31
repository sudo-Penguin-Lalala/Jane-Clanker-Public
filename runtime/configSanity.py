from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import discord

import config
from . import taskBudgeter


@dataclass
class ConfigIssue:
    level: str
    key: str
    message: str


def _normalizeSingleId(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return parsed if parsed > 0 else 0


_DELETED_KEY_PREFIXES = (
    "recruitment",
    "anrors",
    "recruiter",
    "honorguard",
    "hg",
    "anrd",
    "orbat",
    "loa",
    "dept",
    "bg",
    "pendingbg",
    "session",
    "training",
    "instructor",
    "newapplicant",
    "cno",
    "doo",
    "ddoo",
    "sectionchief",
    "commandstaff",
    "foi",
    "crs",
    "shiftsupervisor",
    "juniorsu",
    "msb",
    "middlerank",
    "highrank",
    "moderatorrole",
    "serversafety",
    "division",
    "freedcamp",
    "project",
    "masterlinkhub",
)


def _isDeletedFeatureKey(key: str) -> bool:
    lower = key.lower()
    return any(lower.startswith(prefix) for prefix in _DELETED_KEY_PREFIXES)


def _optionalIdKeys() -> set[str]:
    configured = getattr(config, "configSanityOptionalIdKeys", []) or []
    normalized = {str(value).strip() for value in configured if str(value).strip()}
    return normalized


def _iterSingleIdKeys() -> list[str]:
    out: list[str] = []
    for name in dir(config):
        if name.startswith("_"):
            continue
        if not name.endswith("Id"):
            continue
        if name.endswith("Ids"):
            continue
        if _isDeletedFeatureKey(name):
            continue
        out.append(name)
    return sorted(set(out))


def _iterListIdKeys() -> list[str]:
    out: list[str] = []
    for name in dir(config):
        if name.startswith("_"):
            continue
        if not name.endswith("Ids"):
            continue
        if _isDeletedFeatureKey(name):
            continue
        out.append(name)
    return sorted(set(out))


def _classifyIdKey(key: str) -> str:
    lower = key.lower()
    if "channel" in lower:
        return "channel"
    if "role" in lower:
        return "role"
    return "generic"


async def _fetchReachableChannel(bot: discord.Client, channelId: int) -> Optional[discord.abc.GuildChannel]:
    channel = bot.get_channel(channelId)
    if channel is None:
        try:
            channel = await taskBudgeter.runDiscord(lambda: bot.fetch_channel(channelId))
        except Exception:
            channel = None
    if isinstance(channel, discord.abc.GuildChannel):
        return channel
    return None


async def _resolveGuild(bot: discord.Client) -> Optional[discord.Guild]:
    serverId = _normalizeSingleId(getattr(config, "serverId", 0))
    if serverId <= 0:
        return None
    guild = bot.get_guild(serverId)
    if guild is not None:
        return guild
    try:
        fetched = await taskBudgeter.runDiscord(lambda: bot.fetch_guild(serverId))
    except Exception:
        return None
    return fetched if isinstance(fetched, discord.Guild) else None


async def runConfigSanityCheck(bot: discord.Client) -> dict[str, Any]:
    issues: list[ConfigIssue] = []
    optional = _optionalIdKeys()
    guild = await _resolveGuild(bot)
    roleIdSet: set[int] = set()
    if guild is not None:
        try:
            roles = await taskBudgeter.runDiscord(lambda: guild.fetch_roles())
        except Exception:
            roles = list(getattr(guild, "roles", []))
        roleIdSet = {int(role.id) for role in roles}

    # single IDs
    for key in _iterSingleIdKeys():
        value = _normalizeSingleId(getattr(config, key, 0))
        if value <= 0:
            if key not in optional:
                issues.append(ConfigIssue("warning", key, "Missing or non-positive ID."))
            continue

        kind = _classifyIdKey(key)
        if kind == "channel":
            channel = await _fetchReachableChannel(bot, value)
            if channel is None:
                issues.append(ConfigIssue("warning", key, f"Channel {value} is not reachable."))
        elif kind == "role" and roleIdSet:
            if value not in roleIdSet:
                issues.append(
                    ConfigIssue(
                        "warning",
                        key,
                        f"Role {value} was not found in server {getattr(config, 'serverId', 0)}.",
                    )
                )

    # list IDs
    for key in _iterListIdKeys():
        rawValues = getattr(config, key, None)
        if rawValues is None:
            continue
        if not isinstance(rawValues, (list, tuple, set)):
            issues.append(ConfigIssue("warning", key, "Expected a list/tuple/set of IDs."))
            continue
        for idx, value in enumerate(rawValues):
            normalized = _normalizeSingleId(value)
            indexedKey = f"{key}[{idx}]"
            if normalized <= 0:
                if key not in optional:
                    issues.append(ConfigIssue("warning", indexedKey, "Missing or non-positive ID."))
                continue
            kind = _classifyIdKey(key)
            if kind == "role" and roleIdSet and normalized not in roleIdSet:
                issues.append(
                    ConfigIssue(
                        "warning",
                        indexedKey,
                        f"Role {normalized} was not found in server {getattr(config, 'serverId', 0)}.",
                    )
                )

    warningCount = sum(1 for issue in issues if issue.level == "warning")
    errorCount = sum(1 for issue in issues if issue.level == "error")
    summary = {
        "ok": errorCount == 0,
        "warningCount": warningCount,
        "errorCount": errorCount,
        "issues": [{"level": i.level, "key": i.key, "message": i.message} for i in issues],
    }
    return summary
