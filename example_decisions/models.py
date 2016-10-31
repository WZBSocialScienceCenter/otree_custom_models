import random

from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)

from otree.db.models import Model, ForeignKey


author = 'Markus Konrad'

doc = """
Custom models example: Arbitrary number of complex decisions per player.
"""


class Constants(BaseConstants):
    name_in_url = 'example_decisions'
    players_per_group = None
    num_rounds = 3
    num_decisions_per_round = 5


class Subsession(BaseSubsession):
    def before_session_starts(self):   # called each round
        """For each player, create a fixed number of "decision stubs" with random values to be decided upon later."""
        for p in self.get_players():
            p.generate_decision_stubs()


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    def generate_decision_stubs(self):
        """
        Create a fixed number of "decision stubs", i.e. decision objects that only have a random "value" field on
        which the player will base her or his decision later in the game.
        """
        for _ in range(Constants.num_decisions_per_round):
            decision = self.decision_set.create()    # create a new Decision object as part of the player's decision set
            decision.value = random.randint(1, 10)
            decision.save()   # important: save to DB!


class Decision(Model):   # our custom model inherits from Django's base class "Model"
    REASONS = (
        ('dont_know', "Don't know"),
        ('example_reason', "Example reason"),
        ('another_example_reason', "Another example reason"),
    )

    value = models.IntegerField()    # will be randomly generated
    player_decision = models.BooleanField()
    reason = models.CharField(choices=REASONS)

    player = ForeignKey(Player)    # creates 1:m relation -> this decision was made by a certain player

    def __str__(self):
        return 'decision #%d for player %d (participant %d) - value %d'\
               % (self.pk, self.player.pk, self.player.participant.id_in_session, self.value)
