# FruitCraft Python Automation Client (`fruitcraft_bot`)

A clean, modular, async Python 3.11+ automation library and command-line interface for FruitCraft based on public reverse-engineered client specifications (`FruitcraftClient-py`).

> [!IMPORTANT]
> **Reverse-Engineered Unofficial API Disclaimer**:
> - This software is an **unofficial** client derived from reverse-engineered network traffic and protocol specifications. It is **NOT** an official FruitCraft API.
> - **Anti-Bypass & Security Policy**: This client does **NOT** attempt CAPTCHA bypass, authentication bypass, server-side validation bypass, or security exploit operations. When a CAPTCHA request is returned by the game server (`needs_captcha == true`), automation worker threads automatically halt and await manual user intervention.
> - **Credential Safety**: Passports and restore keys are never logged, stored in plaintext database tables, or printed to standard output.

---

## Features

- **XOR Protocol Engine**: Pure Python XOR encryption/decryption (`ali1343faraz1055antler288based`), URL & Base64 encoding.
- **State Machine & Hashing (`q`)**: Sequential `MD5(q)` check calculation and account execution locking (`asyncio.Lock`).
- **Auto-Battle Worker**: Configurable opponent selection strategies (`WeakestDefenseStrategy`, `StrongestDefenseStrategy`, `ClosestPowerStrategy`, `HighestRewardStrategy`, `CustomStrategy`), card selection, and auto-healing.
- **Server-Scheduled Mine Worker**: Reads `gold_collection_allowed_at` from server responses and calculates exact collection timings instead of arbitrary sleep loops.
- **Auto-Quest Worker**: Automated quest runner with potion/nectar reward tracking.
- **Multi-Account Scheduler**: Completely isolated account containers ensuring zero shared state or cookies.
- **SQLite Persistence**: Local database history tracking account stats, battles, quests, mine collections, and errors.
- **Interactive CLI**: Rich Click/Rich command-line interface.

---

## Installation

### Prerequisites
- Python 3.11+
- `pip` or `hatch`

```bash
# Clone or navigate to the repository
cd fruitcraft_bot

# Install dependencies and editable package
pip install -e .
```

---

## Configuration

Copy `.env.example` to `.env` and configure your credentials:

```bash
cp .env.example .env
```

### Environment Variables (`.env`)

```ini
# Account Secrets (Never commit this file!)
FRUITCRAFT_RESTORE_KEY=your_restore_key_here
FRUITCRAFT_GAME_VERSION=1.9.10691
FRUITCRAFT_BASE_URL=http://iran.fruitcraft.ir

# Automation Settings
FRUITCRAFT_BATTLE_DELAY_MIN=3.0
FRUITCRAFT_BATTLE_DELAY_MAX=6.0
FRUITCRAFT_QUEST_DELAY_MIN=4.0
FRUITCRAFT_QUEST_DELAY_MAX=8.0
FRUITCRAFT_MAX_BATTLES_PER_RUN=50
FRUITCRAFT_STOP_ON_CAPTCHA=true
```

---

## How to Obtain & Use the Account Restore Key

1. Open FruitCraft on your mobile device.
2. Go to **Settings** -> **Account / Restore Key**.
3. Note your unique restoration key string.
4. Set `FRUITCRAFT_RESTORE_KEY` in your `.env` file or pass `--restore-key <KEY>` to CLI commands.

---

## Command Line Interface (CLI) Usage

### 1. Test Capabilities & Health Check
```bash
fruitcraft check-health
```

### 2. Login & Inspect Player Profile
```bash
fruitcraft login
fruitcraft player
```

### 3. Inspect Opponents
```bash
fruitcraft opponents
```

### 4. Manual & Auto Battle
```bash
# Battle specific opponent ID
fruitcraft battle --opponent 123456

# Battle using weakest defense strategy
fruitcraft battle --strategy weakest
```

### 5. Execute Quest
```bash
fruitcraft quest
```

### 6. Collect Mine Gold
```bash
fruitcraft collect-gold
```

### 7. View Leaderboards & Tribe
```bash
fruitcraft rankings
fruitcraft tribe
```

### 8. Inspect Stored Statistics
```bash
fruitcraft stats
```

---

## Programmatic Library Usage

```python
import asyncio
from fruitcraft_bot.api.client import FruitCraftAPIClient
from fruitcraft_bot.services.auth import AuthService
from fruitcraft_bot.services.battle import BattleService, WeakestDefenseStrategy
from fruitcraft_bot.services.cards import CardService

async def main():
    client = FruitCraftAPIClient()
    auth = AuthService(client)
    
    # Authenticate
    await auth.load_player(restore_key="YOUR_RESTORE_KEY")
    
    # Fetch opponents & battle weakest
    battle_service = BattleService(client, auth)
    opponents = await battle_service.get_opponents()
    target = WeakestDefenseStrategy().select_opponent(opponents)
    
    if target:
        result = await battle_service.battle(opponent_id=target.id, cards=[1, 2, 3, 4])
        print(f"Battle outcome: Won={result.won}, Gold={result.gold_earned}")

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Architecture & Project Structure

```
fruitcraft_bot/
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
├── docs/
│   └── API.md
├── src/
│   └── fruitcraft_bot/
│       ├── api/               # Low-level HTTP client, XOR crypto, models, errors
│       ├── services/          # Game domain services (player, battle, quest, cards, mine, tribe, rankings, live_battle)
│       ├── automation/        # Workers & scheduler (battle, quest, mine)
│       ├── storage/           # SQLite state database
│       ├── config.py          # Config management
│       └── cli.py             # Click / Rich CLI
└── tests/                     # Unit test suite
```

---

## Troubleshooting & Known Limitations

- **Rate Limit Codes (`156`, `124`, `184`)**: Handled automatically by the API client with built-in retry backoffs (4s / 2s).
- **CAPTCHA Pausing**: When `needs_captcha` is flagged by the game server, worker loops pause and record state in SQLite. Open the official game client to resolve the CAPTCHA before resuming automation.
- **Game Version Compatibility**: Game version defaults to `1.9.10691`. If the server updates version checks, set `FRUITCRAFT_GAME_VERSION` in `.env`.
- **Experimental Endpoints**: Endpoints like `store/buycardpack` are isolated in `StoreService` and disabled by default behind experimental flags.

---

## License

MIT License. Educational and reverse-engineering reference implementation.
