from __future__ import annotations

import asyncio
import codecs
import logging
import os
import signal
from pathlib import Path
from typing import Any, Callable

import discord
from dotenv import find_dotenv, load_dotenv

from runtime import (
    errorLogging as runtimeErrorLogging,
    loggingConsole as runtimeLoggingConsole,
)

log = logging.getLogger(__name__)


async def _noopHandler(message: Any = None) -> bool:
    return False


def hasUtf8Bom(filepath: str) -> bool:
    with open(filepath, "rb") as handle:
        return handle.read(3).startswith(codecs.BOM_UTF8)


def resolveEnvironmentPath(scriptPath: str) -> Path | None:
    repoRoot = Path(scriptPath).resolve().parent
    configured = str(os.getenv("JANE_ENV_PATH", "") or "").strip()
    if configured:
        candidate = Path(configured).expanduser()
        if not candidate.is_absolute():
            candidate = repoRoot / candidate
        candidate = candidate.resolve()
        return candidate if candidate.is_file() else None

    repoEnvPath = (repoRoot / ".env").resolve()
    if repoEnvPath.is_file():
        return repoEnvPath

    discovered = str(find_dotenv(usecwd=True) or "").strip()
    if not discovered:
        return None
    candidate = Path(discovered).resolve()
    return candidate if candidate.is_file() else None


def discordStartupRetryConfig(configModule: Any) -> tuple[int, float, float]:
    try:
        maxAttempts = int(getattr(configModule, "discordStartupMaxAttempts", 6) or 6)
    except (TypeError, ValueError):
        maxAttempts = 6
    try:
        baseDelaySec = float(getattr(configModule, "discordStartupRetryBaseSec", 15) or 15)
    except (TypeError, ValueError):
        baseDelaySec = 15.0
    try:
        maxDelaySec = float(getattr(configModule, "discordStartupRetryMaxDelaySec", 120) or 120)
    except (TypeError, ValueError):
        maxDelaySec = 120.0
    return max(1, maxAttempts), max(0.0, baseDelaySec), max(0.0, maxDelaySec)


def isRetryableDiscordStartupError(exc: BaseException) -> bool:
    if isinstance(exc, discord.DiscordServerError):
        return True
    if isinstance(exc, discord.HTTPException):
        try:
            status = int(getattr(exc, "status", 0) or 0)
        except (TypeError, ValueError):
            status = 0
        return status in {500, 502, 503, 504}
    if isinstance(exc, (ConnectionError, OSError, TimeoutError)):
        return True
    moduleName = exc.__class__.__module__
    return moduleName.startswith("aiohttp.")


def installTerminationHandler(botClient: Any) -> Callable[[], None]:
    loop = asyncio.get_running_loop()
    shutdownTask: asyncio.Task | None = None

    async def _shutdown() -> None:
        if not botClient.is_closed():
            await botClient.close()

    def _requestShutdown() -> None:
        nonlocal shutdownTask
        if shutdownTask is not None and not shutdownTask.done():
            return
        log.warning("Termination requested. Jane is packing up cleanly.")
        shutdownTask = loop.create_task(_shutdown(), name="runtime-sigterm-shutdown")

    try:
        loop.add_signal_handler(signal.SIGTERM, _requestShutdown)
    except (AttributeError, NotImplementedError, RuntimeError):
        return lambda: None

    def _remove() -> None:
        try:
            loop.remove_signal_handler(signal.SIGTERM)
        except (AttributeError, NotImplementedError, RuntimeError):
            return

    return _remove


async def runRuntimeServices(
    botClient: Any,
    token: str,
    *,
    configModule: Any,
) -> None:
    removeTerminationHandler = installTerminationHandler(botClient)
    try:
        await runBotWithStartupRetry(botClient, token, configModule=configModule)
    finally:
        removeTerminationHandler()



async def runBotWithStartupRetry(
    botClient: Any,
    token: str,
    *,
    configModule: Any,
) -> None:
    maxAttempts, baseDelaySec, maxDelaySec = discordStartupRetryConfig(configModule)
    attempt = 1
    while True:
        try:
            await botClient.start(token)
            return
        except discord.LoginFailure:
            raise
        except discord.PrivilegedIntentsRequired:
            raise
        except Exception as exc:
            if not isRetryableDiscordStartupError(exc) or attempt >= maxAttempts:
                raise

            delaySec = min(maxDelaySec, baseDelaySec * (2 ** (attempt - 1)))

            log.warning(
                "Discord connection attempt %d/%d hit %s; trying again in %.1fs.",
                attempt,
                maxAttempts,
                exc.__class__.__name__,
                delaySec,
            )

            if botClient.is_closed():
                botClient.clear()
            attempt += 1
            await asyncio.sleep(delaySec)


def runMain(
    *,
    botClient: Any,
    configModule: Any,
    singleInstanceLock: Any,
    processControlModule: Any | None,
    scriptPath: str,
) -> None:
    runtimeLoggingConsole.configureConsoleLogging(level=logging.INFO)
    generalErrorLogPath = runtimeErrorLogging.configureGeneralErrorLogging(configModule=configModule)
    runtimeErrorLogging.installGlobalExceptionHooks()
    log.info("Error log ready at %s", generalErrorLogPath)

    lockAcquired, lockOwnerPid = singleInstanceLock.acquire()
    if not lockAcquired:
        raise RuntimeError(
            f"Another Jane process is already running for this repo (pid={int(lockOwnerPid or 0) or 'unknown'})."
        )

    restartRequested = False
    try:
        envPath = resolveEnvironmentPath(scriptPath)
        if envPath is None:
            raise RuntimeError(
                ".env file was not found beside bot.py. Set JANE_ENV_PATH when the host keeps it elsewhere."
            )
        loadedEnvironmentVariables = load_dotenv(envPath, verbose=True, override=True)
        if not loadedEnvironmentVariables:
            raise RuntimeError(".env file not correctly loaded.")
        if hasUtf8Bom(str(envPath)):
            raise RuntimeError(".env file has a UTF-8 BOM.")
        log.info("Environment ready from %s", envPath)

        token = os.getenv("DISCORD_BOT_TOKEN")
        if not token:
            raise RuntimeError("DISCORD_BOT_TOKEN is not set.")

        if processControlModule is not None:
            processControlModule.clearRestartRequest()
        log.info("Starting Jane's Discord runtime.")
        asyncio.run(
            runRuntimeServices(
                botClient,
                token,
                configModule=configModule,
            )
        )
        restartRequested = bool(
            processControlModule is not None and processControlModule.restartRequested()
        )
    finally:
        singleInstanceLock.release()

    if restartRequested and processControlModule is not None:
        if bool(getattr(processControlModule, "supervisorManaged", lambda: False)()):
            log.warning("Restart requested. Handing Jane back to the process supervisor.")
        else:
            log.warning("Restart requested. Jane will be right back.")
        processControlModule.relaunchCurrentProcess(scriptPath=scriptPath)
    else:
        log.info("Jane has clocked out. Runtime stopped cleanly.")
