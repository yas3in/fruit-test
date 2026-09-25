# Internal API Reference for FruitCraft Client

> **Disclaimer**: This is an internal reference document for reverse-engineered endpoints of FruitCraft. It is **NOT** an official API specification.

---

## Endpoint Matrix

### 1. `POST /player/load`
- **Method**: `POST`
- **Path**: `/player/load`
- **Request Model**: `PlayerLoadRequest`
- **Request Fields**:
  - `game_version` (string): Client app version (e.g. `"1.9.10691"`).
  - `udid` (string): Unique device identifier.
  - `os_type` (integer): OS platform type (e.g. `2` for Android).
  - `restore_key` (string, **SECRET**): Account authentication restore key.
  - `os_version` (string): Android OS version string.
  - `model` (string): Device model string.
  - `metrix_uid` (string): Analytics identifier.
  - `appsflyer_uid` (string): Analytics identifier.
  - `device_name` (string): Device hostname or model name.
  - `store_type` (string): App store distribution channel (`"myket"`, `"bazaar"`, etc.).
- **Response Model**: `APIResponse` containing `PlayerInfo` dict.
- **Response Fields**: `status`, `data.player`, `data.cards`, `data.q`, `data.hero`, `data.mine`, `needs_captcha`.
- **Auth Requirement**: Unauthenticated initial load via `restore_key`. Returns `FRUITPASSPORT` cookie header.
- **State Requirement**: None. Initializes account session and returns initial `q` state.
- **Known Side Effects**: Establishes or refreshes session token (`FRUITPASSPORT`).

---

### 2. `POST /player/getplayerinfo`
- **Method**: `POST`
- **Path**: `/player/getplayerinfo`
- **Request Model**: `dict` (optional `id` field)
- **Request Fields**:
  - `id` (string, optional): Target player ID to inspect.
- **Response Model**: `APIResponse`
- **Response Fields**: `status`, `data.name`, `data.level`, `data.rank`, `data.def_power`, `data.avatar_id`.
- **Auth Requirement**: `FRUITPASSPORT` cookie.
- **State Requirement**: Authenticated session.
- **Known Side Effects**: None (read-only query).

---

### 3. `POST /player/fillpotion`
- **Method**: `POST`
- **Path**: `/player/fillpotion`
- **Request Model**: `FillPotionRequest`
- **Request Fields**:
  - `amount` (integer): Number of potions to purchase.
- **Response Model**: `APIResponse`
- **Response Fields**: `status`, `data.potion`, `data.gold`.
- **Auth Requirement**: `FRUITPASSPORT` cookie.
- **State Requirement**: Authenticated session; requires sufficient gold balance.
- **Known Side Effects**: Deducts player gold and increments potion inventory.

---

### 4. `POST /player/comeback`
- **Method**: `POST`
- **Path**: `/player/comeback`
- **Request Model**: `dict` (empty payload `{}`)
- **Response Model**: `APIResponse`
- **Response Fields**: `status`, `data.welcome_reward`, `data.gold`.
- **Auth Requirement**: `FRUITPASSPORT` cookie.
- **State Requirement**: Authenticated session.
- **Known Side Effects**: Claims inactive/comeback rewards if available.

---

### 5. `POST /player/languagepatch`
- **Method**: `POST`
- **Path**: `/player/languagepatch`
- **Request Model**: `dict` (empty payload `{}`)
- **Response Model**: `APIResponse`
- **Response Fields**: `status`, `data.patch`.
- **Auth Requirement**: None / optional `FRUITPASSPORT`.
- **State Requirement**: None.
- **Known Side Effects**: None (read-only query).

---

### 6. `POST /battle/getopponents`
- **Method**: `POST`
- **Path**: `/battle/getopponents`
- **Request Model**: `dict` (empty payload `{}`)
- **Response Model**: `APIResponse` containing list of `Opponent`
- **Response Fields**: `status`, `data.opponents[]` (`id`, `name`, `rank`, `def_power`, `gold`, `level`).
- **Auth Requirement**: `FRUITPASSPORT` cookie.
- **State Requirement**: Authenticated session.
- **Known Side Effects**: Refreshes candidate opponent pool.

---

### 7. `POST /battle/battle`
- **Method**: `POST`
- **Path**: `/battle/battle`
- **Request Model**: `BattleRequest`
- **Request Fields**:
  - `opponent_id` (string): ID of targeted opponent.
  - `cards` (list of integers): Array of card IDs used for attack.
  - `hero_id` (integer, optional): Hero ID assigned to combat.
  - `check` (string, optional): `MD5(previous_q)` string.
- **Response Model**: `APIResponse` containing `BattleResult`
- **Response Fields**: `status`, `data.won`, `data.gold`, `data.xp`, `data.q`, `data.cards_damaged`, `needs_captcha`.
- **Auth Requirement**: `FRUITPASSPORT` cookie.
- **State Requirement**: Authenticated session; sequential execution lock per account.
- **Known Side Effects**: Modifies player gold, XP, win/loss stats, card health, and updates state `q`.

---

### 8. `POST /battle/quest`
- **Method**: `POST`
- **Path**: `/battle/quest`
- **Request Model**: `QuestRequest`
- **Request Fields**:
  - `cards` (list of integers): Selected card IDs for quest.
  - `hash` (string, optional): Specific quest hash.
  - `check` (string, optional): `MD5(previous_q)` string.
- **Response Model**: `APIResponse` containing `QuestResult`
- **Response Fields**: `status`, `data.gold`, `data.xp`, `data.potion`, `data.nectar`, `data.q`, `needs_captcha`.
- **Auth Requirement**: `FRUITPASSPORT` cookie.
- **State Requirement**: Authenticated session; valid `q` sequence.
- **Known Side Effects**: Awards gold, XP, potions, and updates state `q`.

---

### 9. `POST /cards/collectgold`
- **Method**: `POST`
- **Path**: `/cards/collectgold`
- **Request Model**: `CollectGoldRequest`
- **Request Fields**:
  - `client` (string): Client string (`"android"`).
- **Response Model**: `APIResponse` containing `CollectGoldResult`
- **Response Fields**: `status`, `data.collected_gold`, `data.player_gold`, `data.gold_collection_allowed`, `data.gold_collection_allowed_at`.
- **Auth Requirement**: `FRUITPASSPORT` cookie.
- **State Requirement**: Mine collection timestamp reached.
- **Known Side Effects**: Extracts accumulated mine gold and sets next allowed collection timestamp.

---

### 10. `POST /cards/potionize`
- **Method**: `POST`
- **Path**: `/cards/potionize`
- **Request Model**: `PotionizeRequest`
- **Request Fields**:
  - `hero_id` (integer): Hero card ID to apply potions to.
  - `amount` (integer): Number of potions to consume.
- **Response Model**: `APIResponse`
- **Response Fields**: `status`, `data.hero_power`, `data.potions_remaining`.
- **Auth Requirement**: `FRUITPASSPORT` cookie.
- **State Requirement**: Potions available in inventory.
- **Known Side Effects**: Consumes potions to boost hero stats.

---

### 11. `POST /cards/cooloff`
- **Method**: `POST`
- **Path**: `/cards/cooloff`
- **Request Model**: `CoolOffRequest`
- **Request Fields**:
  - `card_id` (integer): Card ID to heal/cool off.
- **Response Model**: `APIResponse`
- **Response Fields**: `status`, `data.gold_cost`, `data.cooldowns_bought_today`.
- **Auth Requirement**: `FRUITPASSPORT` cookie.
- **State Requirement**: Sufficient gold balance.
- **Known Side Effects**: Deducts gold and restores damaged card.

---

### 12. `POST /cards/evolve`
- **Method**: `POST`
- **Path**: `/cards/evolve`
- **Request Model**: `EvolveRequest`
- **Request Fields**:
  - `sacrifices` (list of integers): Card IDs to consume during evolution.
- **Response Model**: `APIResponse`
- **Response Fields**: `status`, `data.evolved_card`.
- **Auth Requirement**: `FRUITPASSPORT` cookie.
- **State Requirement**: Consumable cards available in deck.
- **Known Side Effects**: **PERMANENTLY CONSUMES** sacrifice cards to evolve target card.

---

### 13. `POST /cards/fruitsjsonexport`
- **Method**: `POST`
- **Path**: `/cards/fruitsjsonexport`
- **Request Model**: `dict` `{}`
- **Response Model**: `APIResponse`
- **Response Fields**: `status`, `data.cards`.
- **Auth Requirement**: `FRUITPASSPORT` cookie.
- **State Requirement**: None.
- **Known Side Effects**: Read-only JSON export of card catalog.

---

### 14. `POST /ranking/global`
- **Method**: `POST`
- **Path**: `/ranking/global`
- **Request Model**: `dict` `{}`
- **Response Model**: `APIResponse`
- **Response Fields**: `status`, `data.rankings[]`.
- **Auth Requirement**: `FRUITPASSPORT` cookie.
- **State Requirement**: None.
- **Known Side Effects**: None (read-only query).

---

### 15. `POST /ranking/league`
- **Method**: `POST`
- **Path**: `/ranking/league`
- **Request Model**: `dict` `{}`
- **Response Model**: `APIResponse`
- **Response Fields**: `status`, `data.rankings[]`.
- **Auth Requirement**: `FRUITPASSPORT` cookie.
- **State Requirement**: None.
- **Known Side Effects**: None (read-only query).

---

### 16. `POST /ranking/tribe`
- **Method**: `POST`
- **Path**: `/ranking/tribe`
- **Request Model**: `dict` `{}`
- **Response Model**: `APIResponse`
- **Response Fields**: `status`, `data.rankings[]`.
- **Auth Requirement**: `FRUITPASSPORT` cookie.
- **State Requirement**: None.
- **Known Side Effects**: None (read-only query).

---

### 17. `POST /tribe/members`
- **Method**: `POST`
- **Path**: `/tribe/members`
- **Request Model**: `dict` `{}`
- **Response Model**: `APIResponse` containing list of `TribeMember`
- **Response Fields**: `status`, `data.members[]`.
- **Auth Requirement**: `FRUITPASSPORT` cookie.
- **State Requirement**: Account must belong to a tribe.
- **Known Side Effects**: None (read-only query).

---

### 18. `POST /live-battle/help`
- **Method**: `POST`
- **Path**: `/live-battle/help`
- **Request Model**: `LiveBattleHelpRequest`
- **Request Fields**:
  - `battle_id` (string): Active live battle ID.
- **Response Model**: `APIResponse`
- **Response Fields**: `status`, `data.help_cost`.
- **Auth Requirement**: `FRUITPASSPORT` cookie.
- **State Requirement**: Active live battle session.
- **Known Side Effects**: Requests help assist.

---

### 19. `POST /live-battle/setcardforlivebattle`
- **Method**: `POST`
- **Path**: `/live-battle/setcardforlivebattle`
- **Request Model**: `SetCardForLiveBattleRequest`
- **Request Fields**:
  - `round` (integer): Round index.
  - `card` (integer): Selected card ID.
  - `battle_id` (string): Active live battle ID.
- **Response Model**: `APIResponse`
- **Response Fields**: `status`.
- **Auth Requirement**: `FRUITPASSPORT` cookie.
- **State Requirement**: Active live battle round.
- **Known Side Effects**: Locks card choice for round.

---

### 20. `POST /live-battle/livebattle`
- **Method**: `POST`
- **Path**: `/live-battle/livebattle`
- **Request Model**: `LiveBattleRequest`
- **Request Fields**:
  - `opponent_id` (string): Opponent ID.
- **Response Model**: `APIResponse`
- **Response Fields**: `status`, `data.battle_id`.
- **Auth Requirement**: `FRUITPASSPORT` cookie.
- **State Requirement**: None.
- **Known Side Effects**: Initiates live battle matchmaking.

---

### 21. `POST /error/messages`
- **Method**: `POST`
- **Path**: `/error/messages`
- **Request Model**: `dict` `{}`
- **Response Model**: `APIResponse`
- **Response Fields**: `status`, `data.messages`.
- **Auth Requirement**: None.
- **State Requirement**: None.
- **Known Side Effects**: None (read-only error string mapping).

---

### 22. `POST /device/constants`
- **Method**: `POST`
- **Path**: `/device/constants`
- **Request Model**: `dict` `{}`
- **Response Model**: `APIResponse`
- **Response Fields**: `status`, `data.constants`.
- **Auth Requirement**: None.
- **State Requirement**: None.
- **Known Side Effects**: None.

---

### 23. `POST /store/buycardpack` *(Experimental)*
- **Method**: `POST`
- **Path**: `/store/buycardpack`
- **Request Model**: `BuyCardPackRequest`
- **Request Fields**:
  - `pack_id` (integer): Pack tier identifier.
  - `currency` (string): Currency (`"gold"`, `"nectar"`).
- **Response Model**: `APIResponse`
- **Response Fields**: `status`, `data.cards_unlocked`.
- **Auth Requirement**: `FRUITPASSPORT` cookie.
- **State Requirement**: Explicit experimental flag enabled (`experimental_enabled=True`).
- **Known Side Effects**: Consumes currency and grants card packs.
