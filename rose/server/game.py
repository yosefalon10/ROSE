import random
import logging
import os

from twisted.internet import reactor, task

from rose.common import actions, config, error, message, obstacles  # NOQA
from . import track
from . import player
from . import score

log = logging.getLogger("game")
points_for_obstacles = {"penguin": 10,
                        "water": 4,
                        "crack": 5,
                        "": 0,
                        "trash": -10,
                        "bike": -10,
                        "barrier": -10}

actions_for_obstacles = {"penguin": "pickup", "water": "brake",
                         "crack": "jump", "": "none"}


class Game(object):
    """
    Implements the server for the car race
    """

    def __init__(self):
        self.hub = None
        self.track = track.Track()
        self.looper = task.LoopingCall(self.loop)
        self.players = {}
        self.free_cars = set(range(config.number_of_cars))
        self.free_lanes = set(range(config.max_players))
        self._rate = config.game_rate
        self.started = False
        self.actions = []
        self.timeleft = config.game_duration

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, value):
        if value != self._rate:
            log.info("change game rate to %d frames per second", value)
            self._rate = value
            if self.started:
                self.looper.stop()
                self.looper.start(1.0 / self._rate)
            else:
                self.update_clients()

    def best(self, name):
        best_x = Game.evaluate(self.track, self.players[name].ghost_x, self.players[name].ghost_y, 6)
        return best_x[1]

    def best_for_player(self, name):
        next_x = Game.evaluate(self.track, self.players[name].x, self.players[name].y, 6)[1]
        next_obstacle = self.track.get(next_x, self.players[name].y - 1)
        if next_x == self.players[name].x and next_obstacle in actions_for_obstacles.keys():
            return actions_for_obstacles[next_obstacle]
        if next_x < self.players[name].x:
            return "left"
        if next_x > self.players[name].x:
            return "right"
        return "none"

    @staticmethod
    def evaluate(world, x, y, times=6):
        if times == 0:
            return 0, x
        best_grade, best_x = -1000, x
        for next_x in Game.possible_moves(x):
            next_obstacle, grade = world.get(next_x, y - 1), 0
            if next_x == x:
                grade += points_for_obstacles[next_obstacle]
            elif next_obstacle in ("crack", "water"):
                grade -= 10
            next_grade, final_x = Game.evaluate(world, next_x, y - 1, times - 1)
            grade += next_grade
            if grade > best_grade: best_grade, best_x = grade, next_x
        return best_grade, best_x

    @staticmethod
    def possible_moves(x):
        if x in [2, 5]: return [x - 1, x]
        if x in [0, 3]: return [x + 1, x]
        return [x, x - 1, x + 1]

    def start(self):
        if self.started:
            raise error.GameAlreadyStarted()
        if not self.players:
            raise error.ActionForbidden("start a game with no players.")
        self.track.reset()
        for p in self.players.values():
            p.reset()
        self.timeleft = config.game_duration
        self.started = True
        self.looper.start(1.0 / self._rate)

    def stop(self):
        if not self.started:
            raise error.GameNotStarted()
        self.looper.stop()
        self.started = False
        self.update_clients()
        for p in self.players.values():
            print(f"\n\nsuccess rate for player {p.name}: {round(p.score / p.score_ghost, 3) * 100}%")
        # self.print_stats()

    def add_player(self, name):
        if name in self.players:
            raise error.PlayerExists(name)
        if not self.free_cars:
            raise error.TooManyPlayers()
        car = random.choice(tuple(self.free_cars))
        self.free_cars.remove(car)
        lane = random.choice(tuple(self.free_lanes))
        self.free_lanes.remove(lane)
        log.info("add player: %r, lane: %r, car: %r", name, lane, car)
        self.players[name] = player.Player(name, car, lane)
        reactor.callLater(0, self.update_clients)

    def remove_player(self, name):
        if name not in self.players:
            raise error.NoSuchPlayer(name)
        player = self.players.pop(name)
        self.free_cars.add(player.car)
        self.free_lanes.add(player.lane)
        log.info("remove player: %r, lane: %r, car: %r", name, player.lane, player.car)
        if not self.players and self.started:
            log.info("Stopping game. No players connected.")
            self.stop()
        else:
            reactor.callLater(0, self.update_clients)

    def drive_player(self, name, info):
        # log.info("drive_player: %r %r", name, info)
        if name not in self.players:
            raise error.NoSuchPlayer(name)
        if "action" not in info:
            raise error.InvalidMessage("action required")
        action = info["action"]
        next_x = self.best(name)
        self.players[name].ghost_x = next_x
        if action not in actions.ALL:
            raise error.InvalidMessage("invalid drive action %s" % action)
        best_action = self.best_for_player(name)
        if action != best_action:
            if best_action == "none":
                print(f"\nplayer {name} should have not moved\n")
            else:
                print(f"\nplayer {name} should have turned {best_action}\n")
        else:
            print(f"\nplayer {name} chose the best move\n")
        self.players[name].action = action
        self.players[name].response_time = info.get("response_time", 1.0)

    def print_stats(self):
        lines = ["Stats:"]
        top_scorers = sorted(self.players.values(), reverse=True)
        for i, p in enumerate(top_scorers):
            line = "%d  %10s  row:%d  score:%d" % (i + 1, p.name, p.y, p.score)
            lines.append(line)
            lines.append(f"success rate for player {p.name}: {round(p.score / p.score_ghost, 3) * 100}%")
        log.info("%s", os.linesep.join(lines))

    def loop(self):
        self.track.update()
        score.process(self.players, self.track)
        if self.timeleft > 0:
            self.update_clients()
            self.timeleft -= 1
        else:
            self.stop()

    def update_clients(self):
        msg = message.Message("update", self.state())
        self.hub.broadcast(msg)

    def state(self):
        return {
            "started": self.started,
            "track": self.track.state(),
            "players": [p.state() for p in self.players.values()],
            "timeleft": self.timeleft,
            "rate": self.rate,
        }
