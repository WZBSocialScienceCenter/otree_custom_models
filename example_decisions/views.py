from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants, Player, Decision
from django.forms import modelformset_factory


DecisionFormSet = modelformset_factory(Decision, fields=('player_decision', 'reason'), extra=0)


class MakeDecisionsPage(Page):
    def vars_for_template(self):
        decision_qs = Decision.objects.filter(player__exact=self.player)
        assert len(decision_qs) == Constants.num_decisions_per_round

        decisions_formset = DecisionFormSet(queryset=decision_qs)

        return {
            'decision_formset': decisions_formset,
            'decision_values_and_forms': zip([dec.value for dec in decision_qs], decisions_formset.forms),
        }

    def before_next_page(self):
        # get the raw submitted data as dict
        submitted_data = self.form.data

        # get all decisions belonging to this player and save as dict with decision ID lookup
        decision_objs_by_id = {dec.pk: dec for dec in self.player.decision_set.all()}
        assert len(decision_objs_by_id) == Constants.num_decisions_per_round

        for i in range(Constants.num_decisions_per_round):
            input_prefix = 'form-%d-' % i

            # get the inputs
            dec_id = int(submitted_data[input_prefix + 'id'])
            player_decision = submitted_data[input_prefix + 'player_decision']
            reason = submitted_data[input_prefix + 'reason']

            # lookup by ID and save submitted data
            dec = decision_objs_by_id[dec_id]

            if player_decision != '':
                dec.player_decision = player_decision == 'True'
            else:
                dec.player_decision = None

            if reason != '':
                dec.reason = reason
            else:
                dec.reason = None

            # important: save to DB!
            dec.save()


page_sequence = [
    MakeDecisionsPage,
]
