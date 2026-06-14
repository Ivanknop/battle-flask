import traceback
from flask import jsonify, session, redirect, url_for, request, render_template
import random

class BattleApp:
    def __init__(self, EntityClass, FightClass, combat_rules, choose_route,handler):
        self.EntityClass = EntityClass
        self.FightClass = FightClass
        self.combat_rules = combat_rules
        self.choose_route = choose_route
        self.handler = handler

    def register_routes(self, app):
        entity_class = self.EntityClass 
        fight_class = self.FightClass
        combat_rules = self.combat_rules
        choose_route = self.choose_route
        handler = self.handler

        @app.route("/fight/next", methods=["POST"])
        def next_turn():
            try:
                fighter_one_data = session.get("fighter_one")
                fighter_two_data = session.get("fighter_two")
                if fighter_one_data is None or fighter_two_data is None:
                    return redirect(url_for(choose_route))
                fighter_one = entity_class.from_dict(fighter_one_data)
                fighter_two = entity_class.from_dict(fighter_two_data)
                battle = fight_class(fighter_one, fighter_two)
                attacker_luck = int(session.get("attacker_luck", 0))
                defender_luck = int(session.get("defender_luck", 0))
                result = battle.play_turn(
                    attacker_luck=attacker_luck,
                    defender_luck=defender_luck,
                )
                session["fighter_one"] = fighter_one.to_dict()
                session["fighter_two"] = fighter_two.to_dict() 
                events = session.get("events", [])
                for event in reversed(result):
                    events.insert(0, event)
                session["events"] = events
                winner = battle.winner()
                if winner is not None:
                    session["finished"] = True
                    session["winner"] = winner.get_name()
                    if winner.get_name() == fighter_one.get_name():
                        session["winner_role"] = "Jugador"
                    else:
                        session["winner_role"] = "Rival"
                session["attacker_luck"] = 0
                session["defender_luck"] = 0
                session["pending_attacker_luck"] = None
                session["pending_defender_luck"] = None
                session["luck_used_this_turn"] = False

                return redirect(url_for("fight_screen"))

            except Exception:
                return jsonify({"trace": traceback.format_exc()}), 500
            
        @app.route("/fight", methods=["GET"])
        def fight_screen():
            try:
                fighter_one = session.get("fighter_one")
                fighter_two = session.get("fighter_two")
                events = session.get("events", [])
                finished = session.get("finished", False)
                winner = session.get("winner")
                winner_role = session.get("winner_role")
                if fighter_one is None or fighter_two is None:
                    return redirect(url_for(choose_route))
                return render_template(
                    "fight.html",
                    fighter_one=fighter_one,
                    fighter_two=fighter_two,
                    events=events,
                    finished=finished,
                    winner=winner,
                    winner_role=winner_role,
                    attacker_luck=session.get("attacker_luck", 0),
                    defender_luck=session.get("defender_luck", 0),
                    pending_attacker_luck=session.get("pending_attacker_luck"),
                    pending_defender_luck=session.get("pending_defender_luck"),
                    luck_used_this_turn=session.get("luck_used_this_turn", False),
                )
            except Exception:
                return jsonify({"trace": traceback.format_exc()}), 500
            
        @app.route("/start_fight", methods=["GET"])
        def start_fight():
            try:
                player_name = request.args.get("player")
                player_entity = handler.find_entity(player_name)
                player_opponent = handler.random_entity_excluding(player_name)
                session["fighter_one"] = player_entity.to_dict()
                session["fighter_two"] = player_opponent.to_dict()
                session["events"] = []
                session["finished"] = False
                session["winner"] = None
                session["winner_role"] = None
                session["attacker_luck"] = 0
                session["defender_luck"] = 0
                session["pending_attacker_luck"] = None
                session["pending_defender_luck"] = None
                session["luck_used_this_turn"] = False
                return redirect(url_for("fight_screen"))
            except Exception:
                return jsonify({"trace": traceback.format_exc()}), 500

        @app.route("/fight/luck", methods=["POST"])
        def roll_luck():
            try:
                luck_pair = combat_rules.roll_luck_pair(random)

                session["pending_attacker_luck"] = luck_pair["attacker_luck"]
                session["pending_defender_luck"] = luck_pair["defender_luck"]
                session["luck_used_this_turn"] = True
                return redirect(url_for("fight_screen"))

            except Exception:
                return jsonify({"trace": traceback.format_exc()}), 500
            
        @app.route("/fight/luck/reject", methods=["POST"])
        def reject_luck():
            try:
                session["pending_attacker_luck"] = None
                session["pending_defender_luck"] = None
                return redirect(url_for("fight_screen"))

            except Exception:
                return jsonify({"trace": traceback.format_exc()}), 500
            
        @app.route("/fight/luck/accept", methods=["POST"])
        def accept_luck():
            try:
                session["attacker_luck"] = session.get("pending_attacker_luck", 0)
                session["defender_luck"] = session.get("pending_defender_luck", 0)

                session["pending_attacker_luck"] = None
                session["pending_defender_luck"] = None

                return redirect(url_for("fight_screen"))

            except Exception:
                return jsonify({"trace": traceback.format_exc()}), 500