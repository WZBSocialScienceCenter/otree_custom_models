from .utils import get_field_names_for_csv
from . import models
from ._builtin import Page, WaitPage
from .models import Constants, Decision
from django.forms import modelformset_factory

from collections import OrderedDict
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


DecisionFormSet = modelformset_factory(Decision, fields=('player_decision', 'reason'), extra=0)


class MakeDecisionsPage(Page):
    def vars_for_template(self):
        # get decisions for this player
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


@login_required
def export_view_json(request):
    """
    Custom view function to export full results for this game as JSON file
    """

    def create_odict_from_object(obj, fieldnames):
        """
        Small helper function to create an OrderedDict from an object <obj> using <fieldnames>
        as attributes.
        """
        data = OrderedDict()
        for f in fieldnames:
            data[f] = getattr(obj, f)

        return data

    # get the complete result data from the database
    qs_results = models.Player.objects.select_related('subsession', 'subsession__session', 'group', 'participant')\
                                      .prefetch_related('decision_set')\
                                      .all()

    session_fieldnames = []  # will be defined by get_field_names_for_csv
    subsess_fieldnames = []  # will be defined by get_field_names_for_csv
    group_fieldnames = []    # will be defined by get_field_names_for_csv
    player_fieldnames = []   # will be defined by get_field_names_for_csv
    decision_fieldnames = ['value', 'player_decision', 'reason']

    # get all sessions, order them by label
    sessions = sorted(set([p.subsession.session for p in qs_results]), key=lambda x: x.label)

    # this will be a list that contains data of all sessions
    output = []

    # loop through all sessions
    for sess in sessions:
        session_fieldnames = session_fieldnames or get_field_names_for_csv(sess.__class__)
        sess_output = create_odict_from_object(sess, session_fieldnames)
        sess_output['subsessions'] = []

        # loop through all subsessions (i.e. rounds) ordered by round number
        subsessions = sorted(sess.get_subsessions(), key=lambda x: x.round_number)
        for subsess in subsessions:
            subsess_fieldnames = subsess_fieldnames or get_field_names_for_csv(subsess.__class__)
            subsess_output = create_odict_from_object(subsess, subsess_fieldnames)
            subsess_output['groups'] = []

            # loop through all groups ordered by ID
            groups = sorted(subsess.get_groups(), key=lambda x: x.id_in_subsession)
            for g in groups:
                group_fieldnames = group_fieldnames or get_field_names_for_csv(g.__class__)
                g_output = create_odict_from_object(g, group_fieldnames)
                g_output['players'] = []

                # loop through all players ordered by ID
                players = sorted(g.get_players(), key=lambda x: x.participant.id_in_session)
                for p in players:
                    player_fieldnames = player_fieldnames or get_field_names_for_csv(p.__class__)
                    p_output = create_odict_from_object(p, player_fieldnames)

                    # add some additional player information
                    p_output['participant_id_in_session'] = p.participant.id_in_session
                    p_output['decisions'] = []

                    # loop through all decisions ordered by ID
                    decisions = p.decision_set.order_by('id')
                    for dec in decisions:
                        dec_output = create_odict_from_object(dec, decision_fieldnames)
                        p_output['decisions'].append(dec_output)

                    g_output['players'].append(p_output)

                subsess_output['groups'].append(g_output)

            sess_output['subsessions'].append(subsess_output)

        output.append(sess_output)

    return JsonResponse(output, safe=False)

page_sequence = [
    MakeDecisionsPage,
]
