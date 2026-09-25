"""Command-line Interface for FruitCraft Bot using Click and Rich."""

import asyncio
import os
import sys
from typing import Optional
import click
from rich.console import Console
from rich.table import Table

from fruitcraft_bot.api.client import FruitCraftAPIClient
from fruitcraft_bot.config import AccountConfig, AppSettings, DeviceConfig
from fruitcraft_bot.services.auth import AuthService
from fruitcraft_bot.services.battle import BattleService, STRATEGY_MAP
from fruitcraft_bot.services.cards import CardService, StrongestCardsStrategy
from fruitcraft_bot.services.mine import MineService
from fruitcraft_bot.services.player import PlayerService
from fruitcraft_bot.services.quest import QuestService
from fruitcraft_bot.services.rankings import RankingService
from fruitcraft_bot.services.tribe import TribeService
from fruitcraft_bot.storage.state import StateDatabase

console = Console()


def get_account_config(restore_key_arg: Optional[str] = None) -> AccountConfig:
    """Resolve account credentials from CLI argument or environment variables."""
    settings = AppSettings()
    raw_key = restore_key_arg or (settings.restore_key.get_secret_value() if settings.restore_key else None)
    if not raw_key:
        console.print("[bold red]Error:[/bold red] No restore key provided. Set FRUITCRAFT_RESTORE_KEY in environment or pass --restore-key.")
        sys.exit(1)
    return AccountConfig(account_id="cli", restore_key=raw_key)


def run_async(coro):
    """Utility helper to run async coroutine from synchronous Click command."""
    return asyncio.run(coro)


@click.group()

def cli():
    """FruitCraft Unofficial Automation CLI."""
    pass


@cli.command()
@click.option("--restore-key", help="Account restore key")
def login(restore_key: Optional[str]):
    """Authenticate account via player/load."""
    cfg = get_account_config(restore_key)

    async def _impl():
        client = FruitCraftAPIClient()
        auth = AuthService(client)
        try:
            info = await auth.load_player(cfg.restore_key, cfg.device)
            console.print(f"[bold green]Authenticated Successfully![/bold green]")
            console.print(f"Player Name: [cyan]{info.name}[/cyan] (ID: {info.id})")
            console.print(f"Level: {info.level} | Gold: {info.gold:,} | Nectar: {info.nectar:,} | Potion: {info.potion:,}")
        finally:
            await client.close()

    run_async(_impl())


@cli.command()
@click.option("--restore-key", help="Account restore key")
def player(restore_key: Optional[str]):
    """Inspect authenticated player details."""
    cfg = get_account_config(restore_key)

    async def _impl():
        client = FruitCraftAPIClient()
        auth = AuthService(client)
        try:
            info = await auth.load_player(cfg.restore_key, cfg.device)
            table = Table(title=f"Player Profile: {info.name}")
            table.add_column("Property", style="bold yellow")
            table.add_column("Value", style="cyan")

            table.add_row("ID", info.id)
            table.add_row("Level", str(info.level))
            table.add_row("XP", f"{info.xp:,}")
            table.add_row("Gold", f"{info.gold:,}")
            table.add_row("Nectar", f"{info.nectar:,}")
            table.add_row("Potion", f"{info.potion:,}")
            table.add_row("Rank", f"{info.rank:,}")
            table.add_row("League Rank", f"{info.league_rank:,}")
            table.add_row("Tribe", info.tribe or "None")
            table.add_row("Total Battles", f"{info.total_battles:,}")
            table.add_row("Won / Lost", f"{info.won_battles:,} / {info.lost_battles:,}")

            console.print(table)
        finally:
            await client.close()

    run_async(_impl())


@cli.command()
@click.option("--restore-key", help="Account restore key")
def opponents(restore_key: Optional[str]):
    """Fetch potential battle opponents."""
    cfg = get_account_config(restore_key)

    async def _impl():
        client = FruitCraftAPIClient()
        auth = AuthService(client)
        battle = BattleService(client, auth)
        try:
            await auth.load_player(cfg.restore_key, cfg.device)
            opps = await battle.get_opponents()

            table = Table(title="Available Opponents")
            table.add_column("ID", style="dim")
            table.add_column("Name", style="bold cyan")
            table.add_column("Defense Power", style="red")
            table.add_column("Gold Reward", style="yellow")
            table.add_column("Level", style="magenta")

            for o in opps:
                table.add_row(o.id, o.name, f"{o.def_power:,}", f"{o.gold:,}", str(o.level))

            console.print(table)
        finally:
            await client.close()

    run_async(_impl())


@cli.command()
@click.option("--opponent", help="Target opponent ID")
@click.option("--strategy", default="weakest", help="Strategy: weakest, strongest, closest, highest_reward")
@click.option("--restore-key", help="Account restore key")
def battle(opponent: Optional[str], strategy: str, restore_key: Optional[str]):
    """Execute battle against chosen opponent or selected strategy."""
    cfg = get_account_config(restore_key)

    async def _impl():
        client = FruitCraftAPIClient()
        auth = AuthService(client)
        b_service = BattleService(client, auth)
        try:
            await auth.load_player(cfg.restore_key, cfg.device)
            target_id = opponent

            if not target_id:
                opps = await b_service.get_opponents()
                strat_obj = STRATEGY_MAP.get(strategy.lower(), STRATEGY_MAP["weakest"])
                selected_opp = strat_obj.select_opponent(opps)
                if not selected_opp:
                    console.print("[red]No suitable opponent found.[/red]")
                    return
                target_id = selected_opp.id
                console.print(f"Selected opponent [cyan]{selected_opp.name}[/cyan] (ID: {target_id}, Defense: {selected_opp.def_power:,})")

            available_cards = auth.player_info.cards if (auth.player_info and auth.player_info.cards) else []
            card_sel = StrongestCardsStrategy().select(available_cards, count=4)
            if not card_sel.cards:
                if not available_cards:
                    console.print("[bold red]Error:[/bold red] No cards found in player deck profile.")
                else:
                    console.print(f"[bold red]Error:[/bold red] All {len(available_cards)} cards in your deck are currently damaged or in cooldown.")
                return

            console.print(f"Attacking with top {len(card_sel.cards)} usable cards: [yellow]{card_sel.cards}[/yellow]")

            res = await b_service.battle(
                opponent_id=target_id,
                cards=card_sel.cards,
                hero_id=card_sel.hero_id,
            )
            color = "green" if res.won else "red"
            console.print(f"[{color}]Battle Result: {'WON' if res.won else 'LOST'}[/{color}]")
            console.print(f"Gold Earned: [yellow]{res.gold_earned:,}[/yellow] | XP: [cyan]{res.xp_earned:,}[/cyan]")
        finally:
            await client.close()

    run_async(_impl())


@cli.command()
@click.option("--restore-key", help="Account restore key")
def quest(restore_key: Optional[str]):
    """Execute single quest."""
    cfg = get_account_config(restore_key)

    async def _impl():
        client = FruitCraftAPIClient()
        auth = AuthService(client)
        q_service = QuestService(client, auth)
        try:
            await auth.load_player(cfg.restore_key, cfg.device)
            available_cards = auth.player_info.cards if (auth.player_info and auth.player_info.cards) else []
            card_sel = StrongestCardsStrategy().select(available_cards, count=4)
            if not card_sel.cards:
                if not available_cards:
                    console.print("[bold red]Error:[/bold red] No cards found in player deck profile.")
                else:
                    console.print(f"[bold red]Error:[/bold red] All {len(available_cards)} cards in your deck are currently damaged or in cooldown.")
                return

            console.print(f"Executing quest with top usable cards: [yellow]{card_sel.cards}[/yellow]")
            res = await q_service.do_quest(cards=card_sel.cards)
            console.print("[bold green]Quest Executed![/bold green]")
            console.print(f"Gold Earned: [yellow]{res.gold:,}[/yellow] | XP: {res.xp:,} | Potions: {res.potion}")
        finally:
            await client.close()

    run_async(_impl())


@cli.command(name="collect-gold")
@click.option("--restore-key", help="Account restore key")
def collect_gold(restore_key: Optional[str]):
    """Collect mine gold."""
    cfg = get_account_config(restore_key)

    async def _impl():
        client = FruitCraftAPIClient()
        auth = AuthService(client)
        c_service = CardService(client, auth)
        try:
            await auth.load_player(cfg.restore_key, cfg.device)
            res = await c_service.collect_gold()
            console.print(f"[bold green]Gold Collection Result:[/bold green]")
            console.print(f"Collected Gold: [yellow]{res.collected_gold:,}[/yellow]")
            console.print(f"Total Player Gold: [yellow]{res.player_gold:,}[/yellow]")
            console.print(f"Collection Allowed Next: {res.gold_collection_allowed_at}")
        finally:
            await client.close()

    run_async(_impl())


@cli.command()
@click.option("--restore-key", help="Account restore key")
def rankings(restore_key: Optional[str]):
    """Display global leaderboard rankings."""
    cfg = get_account_config(restore_key)

    async def _impl():
        client = FruitCraftAPIClient()
        r_service = RankingService(client)
        try:
            data = await r_service.get_global_rankings()
            console.print(f"[bold cyan]Global Rankings Output:[/bold cyan]")
            console.print(data)
        finally:
            await client.close()

    run_async(_impl())


@cli.command()
@click.option("--restore-key", help="Account restore key")
def tribe(restore_key: Optional[str]):
    """Fetch tribe members listing."""
    cfg = get_account_config(restore_key)

    async def _impl():
        client = FruitCraftAPIClient()
        t_service = TribeService(client)
        try:
            members = await t_service.get_members()
            table = Table(title="Tribe Members")
            table.add_column("ID", style="dim")
            table.add_column("Name", style="bold cyan")
            table.add_column("Level", style="yellow")
            table.add_column("Defense Power", style="red")

            for m in members:
                table.add_row(m.id, m.name, str(m.level), f"{m.def_power:,}")

            console.print(table)
        finally:
            await client.close()

    run_async(_impl())


@cli.command()
def stats():
    """Display stored local statistics database summary."""
    db = StateDatabase()
    s = db.get_stats("cli")
    table = Table(title="Local Automation Statistics")
    table.add_column("Metric", style="bold yellow")
    table.add_column("Count / Value", style="cyan")

    table.add_row("Total Battles", str(s["total_battles"]))
    table.add_row("Wins / Losses", f"{s['wins']} / {s['losses']}")
    table.add_row("Battle Gold", f"{s['battle_gold']:,}")
    table.add_row("Total Quests", str(s["total_quests"]))
    table.add_row("Quest Gold", f"{s['quest_gold']:,}")
    table.add_row("Mine Gold Collected", f"{s['mine_gold']:,}")
    table.add_row("Total Gold Earned", f"{s['total_gold_earned']:,}")

    console.print(table)


@cli.command()
def start():
    """Start full background automation runner (Battles, Quests, Mine Collection)."""
    settings = AppSettings()
    accounts = settings.get_accounts()

    if not accounts:
        console.print("[bold red]Error:[/bold red] No accounts configured. Please set FRUITCRAFT_RESTORE_KEY in .env file.")
        sys.exit(1)

    console.print("[bold green]Starting FruitCraft Automation Scheduler...[/bold green]")
    console.print(f"Loaded accounts: [cyan]{list(accounts.keys())}[/cyan]")
    console.print("Press Ctrl+C to stop.")

    from fruitcraft_bot.automation.scheduler import Scheduler
    scheduler = Scheduler(accounts, db_path=settings.db_path)

    async def _run():
        try:
            await scheduler.start()
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping scheduler...[/yellow]")
        finally:
            await scheduler.stop()

    run_async(_run())


@cli.command(name="check-health")
@click.option("--restore-key", help="Account restore key")
def check_health(restore_key: Optional[str]):
    """Capability and health check against server endpoints."""
    cfg = get_account_config(restore_key)

    async def _impl():
        client = FruitCraftAPIClient()
        auth = AuthService(client)
        try:
            console.print("[yellow]Checking endpoint capabilities...[/yellow]")
            info = await auth.load_player(cfg.restore_key, cfg.device)
            console.print("✔ [green]POST player/load[/green]: SUCCESS")

            b_service = BattleService(client, auth)
            opps = await b_service.get_opponents()
            console.print("✔ [green]POST battle/getopponents[/green]: SUCCESS")

            c_service = CardService(client, auth)
            g_res = await c_service.collect_gold()
            console.print("✔ [green]POST cards/collectgold[/green]: SUCCESS")

            console.print("\n[bold green]Health Check Completed successfully![/bold green]")
        except Exception as e:
            console.print(f"✖ [bold red]Health Check Failed:[/bold red] {e}")
        finally:
            await client.close()

    run_async(_impl())


if __name__ == "__main__":
    cli()
