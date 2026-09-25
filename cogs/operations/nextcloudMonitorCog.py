from __future__ import annotations
import logging
import psutil
import json
import os
import time
import datetime
from discord import app_commands, Embed, Color, Interaction
from discord.ext import commands, tasks
from runtime import cogGuards as runtimeCogGuards

log = logging.getLogger(__name__)
DATA_FILE = '/app/data/host_dashboard_msg.json'

def make_bar(percent: float, length: int = 15) -> str:
    filled = int(round(length * (percent / 100.0)))
    return '█' * filled + '░' * (length - filled)

def format_bytes(b: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if b < 1024.0:
            return f"{b:.1f}{unit}"
        b /= 1024.0
    return f"{b:.1f}PB"

def uptime_str() -> str:
    uptime_seconds = time.time() - psutil.boot_time()
    return str(datetime.timedelta(seconds=int(uptime_seconds)))

class HostMonitorCog(runtimeCogGuards.InteractionGuardMixin, commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channel_id = None
        self.message_id = None
        self.last_net_io = None
        self.last_net_time = None
        self._load_data()
        self.update_dashboard.start()

    def _load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.channel_id = data.get('channel_id')
                    self.message_id = data.get('message_id')
            except Exception:
                pass

    def _save_data(self):
        with open(DATA_FILE, 'w') as f:
            json.dump({'channel_id': self.channel_id, 'message_id': self.message_id}, f)

    async def cog_unload(self):
        self.update_dashboard.cancel()

    @app_commands.command(name='lab_spawn', description='Spawn the live-updating btop dashboard')
    async def lab_spawn(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        embed = Embed(title="🗄️ Lab Computer", description="Initializing BTOP feed...", color=Color.dark_gray())
        msg = await interaction.followup.send(embed=embed, wait=True)
        self.channel_id = interaction.channel_id
        self.message_id = msg.id
        self._save_data()
        await self._force_update()

    async def _force_update(self):
        if not self.channel_id or not self.message_id:
            return
            
        try:
            channel = self.bot.get_channel(self.channel_id)
            if not channel: return
            msg = await channel.fetch_message(self.message_id)
            
            # --- SYSTEM STATS ---
            cpu_percents = psutil.cpu_percent(interval=0.1, percpu=True)
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            disk = psutil.disk_usage('/')
            try:
                load1, load5, load15 = os.getloadavg()
            except Exception:
                load1, load5, load15 = 0.0, 0.0, 0.0
            
            # --- NETWORK SPEED ---
            current_net_io = psutil.net_io_counters()
            current_time = time.time()
            recv_speed = sent_speed = 0
            if self.last_net_io and self.last_net_time:
                time_diff = current_time - self.last_net_time
                if time_diff > 0:
                    recv_speed = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / time_diff
                    sent_speed = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / time_diff
            self.last_net_io = current_net_io
            self.last_net_time = current_time

            # --- PROCESSES ---
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'cpu_percent']):
                try:
                    info = p.info
                    if info['name']:
                        procs.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            # Sort by CPU and get top 5
            procs = sorted(procs, key=lambda p: (p['cpu_percent'] or 0.0), reverse=True)[:6]

            # --- RENDER DASHBOARD ---
            desc = "```ansi\n"
            
            # CPU SECTION
            desc += f"\u001b[2;34mcpu\u001b[0m \u001b[2;37mLoad avg: {load1:.2f} {load5:.2f} {load15:.2f}\u001b[0m\n"
            for i, pct in enumerate(cpu_percents):
                color = "32" if pct < 50 else ("33" if pct < 85 else "31")
                desc += f"C{i} \u001b[2;{color}m[{make_bar(pct, 20)}]\u001b[0m {pct:5.1f}%\n"
            
            # MEMORY & DISK
            desc += f"\n\u001b[2;34mmem\u001b[0m                          \u001b[2;34mdisks\u001b[0m\n"
            desc += f"Total:      {format_bytes(mem.total):>8}         root \u001b[2;36m[{make_bar(disk.percent, 10)}]\u001b[0m {disk.percent}%\n"
            desc += f"Used:       {format_bytes(mem.used):>8}         Used: {format_bytes(disk.used):>8}\n"
            desc += f"Available:  {format_bytes(mem.available):>8}         Free: {format_bytes(disk.free):>8}\n"
            desc += f"Cached:     {format_bytes(getattr(mem, 'cached', 0)):>8}         \u001b[2;34mnet\u001b[0m\n"
            desc += f"Free:       {format_bytes(mem.free):>8}         ▼ RX: {format_bytes(recv_speed)}/s\n"
            desc += f"Swap Used:  {format_bytes(swap.used):>8}         ▲ TX: {format_bytes(sent_speed)}/s\n"
            
            # PROC SECTION
            desc += "\n\u001b[2;34mproc\u001b[0m filter                 reverse tree ↵ cpu lazy →\n"
            desc += f"{'Pid':<7} {'Program':<15} {'User':<10} {'Mem%':>6} {'Cpu%':>6}\n"
            for p in procs:
                pname = (p['name'] or '')[:14]
                user = (p['username'] or '')[:9]
                mem_pct = p['memory_percent'] or 0.0
                cpu_pct = p['cpu_percent'] or 0.0
                desc += f"{p['pid']:<7} {pname:<15} {user:<10} {mem_pct:5.1f}% {cpu_pct:5.1f}%\n"
            
            desc += "\n\u001b[2;37mUptime:\u001b[0m " + uptime_str() + "\n"
            desc += "```"
            
            embed = Embed(title="🗄️ Lab Computer", description=desc, color=Color.dark_teal())
            embed.set_footer(text="BTOP Clone • Feed updates every 60s")
            await msg.edit(embed=embed)
        except Exception as e:
            log.error(f"Failed to update dashboard: {e}")

    @tasks.loop(seconds=60.0)
    async def update_dashboard(self):
        await self._force_update()

    @update_dashboard.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HostMonitorCog(bot))
