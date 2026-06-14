# battle-flask

Flask integration layer for [battle-core](https://github.com/Ivanknop/battle-core). Provides `BattleApp`, a configurable class that registers shared battle routes into any Flask application.

No domain logic. No direct dependency on `battle-core` — receives domain classes as constructor parameters.

## Installation

```bash
pip install git+https://github.com/Ivanknop/battle-flask.git
```

## Requirements

- Python 3.12+
- Flask
- A project using `battle-core` with `Entity` subclasses that implement `from_dict` and `to_dict`

## Usage

```python
from flask import Flask
from battle_flask.battle_flask import BattleApp
from model.my_entity import MyEntity
from model.my_fight import MyFight
from model.my_combat_rules import MyCombatRules
import model.handler_data as handler_data

def create_app():
    app = Flask(__name__)
    app.secret_key = "your-secret"

    battle_app = BattleApp(
        EntityClass=MyEntity,
        FightClass=MyFight,
        combat_rules=MyCombatRules(),
        choose_route="choose_character",  # name of your selection route
        handler=handler_data,
    )
    battle_app.register_routes(app)

    @app.route("/")
    def index(): ...

    @app.route("/choose_character")
    def choose_character(): ...

    return app
```

## What `register_routes` provides

Calling `battle_app.register_routes(app)` registers the following routes:

| Route | Method | Description |
|---|---|---|
| `/start_fight` | GET | Reads `?player=<name>`, loads entities via handler, initializes session |
| `/fight` | GET | Renders `fight.html` with current session state |
| `/fight/next` | POST | Executes one turn, updates session |
| `/fight/luck` | POST | Rolls luck pair, stores as pending in session |
| `/fight/luck/accept` | POST | Confirms pending luck for the turn |
| `/fight/luck/reject` | POST | Discards pending luck |

## Handler interface

The `handler` parameter must expose these two functions:

```python
def find_entity(name: str) -> Entity:
    ...

def random_entity_excluding(name: str) -> Entity:
    ...
```

Both must return an instance of the project's `Entity` subclass. The handler can be backed by a database (SQLAlchemy), a CSV file, or any other source — `BattleApp` does not care.

## Template interface

`register_routes` expects a `fight.html` template in the project's `templates/` folder. The template receives these context variables:

| Variable | Type | Description |
|---|---|---|
| `fighter_one` | dict | Serialized entity (from `to_dict()`) |
| `fighter_two` | dict | Serialized entity (from `to_dict()`) |
| `events` | list[str] | Turn event log (most recent first) |
| `finished` | bool | Whether the fight is over |
| `winner` | str or None | Winner's name |
| `winner_role` | str or None | `"Jugador"` or `"Rival"` |
| `attacker_luck` | int | Active attacker luck (0 if none) |
| `defender_luck` | int | Active defender luck (0 if none) |
| `pending_attacker_luck` | int or None | Rolled but not yet accepted |
| `pending_defender_luck` | int or None | Rolled but not yet accepted |
| `luck_used_this_turn` | bool | Whether luck was rolled this turn |

The selection template (e.g. `choose_character.html`) must submit the player's name as a `player` query parameter to `/start_fight`:

```html
<a href="/start_fight?player={{ entity.get_name() }}">Fight</a>
```

## Used by

- [pokemonBattle-py](https://github.com/Ivanknop/pokemonBattle-py)
- [superHeroBattle](https://github.com/Ivanknop/superHeroBattle)
- [country-battle](https://github.com/Ivanknop/country-battle)