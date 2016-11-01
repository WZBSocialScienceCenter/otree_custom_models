from django.db.models import BinaryField

from otree.models.participant import Participant
from otree.models.session import Session
from otree.models.subsession import BaseSubsession
from otree.models.group import BaseGroup
from otree.models.player import BasePlayer

"""
This file contains several functions copy'n'pasted from oTrees's core code in order to retain compatibility with
future oTree versions.
"""


def inspect_field_names(Model):
    # filter out BinaryField, because it's not useful for CSV export or
    # live results. could be very big, and causes problems with utf-8 export

    # I tried .get_fields() instead of .fields, but that method returns
    # fields that cause problems, like saying group has an attribute 'player'
    return [f.name for f in Model._meta.fields
            if not isinstance(f, BinaryField)]


def get_field_names_for_csv(Model):
    return _get_table_fields(Model, for_export=True)


def _get_table_fields(Model, for_export=False):
    if Model is Session:
        # only data export
        return [
            'code',
            'label',
            'experimenter_name',
            'time_scheduled',
            'time_started',
            'mturk_HITId',
            'mturk_HITGroupId',
            'comment',
            'is_demo',
        ]

    if Model is Participant:
        if for_export:
            return [
                'id_in_session',
                'code',
                'label',
                '_is_bot',
                '_index_in_pages',
                '_max_page_index',
                '_current_app_name',
                '_round_number',
                '_current_page_name',
                'ip_address',
                'time_started',
                'exclude_from_data_analysis',
                'visited',
                'mturk_worker_id',
                'mturk_assignment_id',
            ]
        else:
            return [
                '_id_in_session',
                'code',
                'label',
                '_current_page',
                '_current_app_name',
                '_round_number',
                '_current_page_name',
                'status',
                '_last_page_timestamp',
            ]

    if issubclass(Model, BasePlayer):
        subclass_fields = [
            f for f in inspect_field_names(Model)
            if f not in inspect_field_names(BasePlayer)
            and f not in ['id', 'group', 'subsession']
            ]

        if for_export:
            return ['id_in_group'] + subclass_fields + ['payoff']
        else:
            return ['id_in_group', 'role'] + subclass_fields + ['payoff']

    if issubclass(Model, BaseGroup):
        subclass_fields = [
            f for f in inspect_field_names(Model)
            if f not in inspect_field_names(BaseGroup)
            and f not in ['id', 'subsession']
            ]

        return ['id_in_subsession'] + subclass_fields

    if issubclass(Model, BaseSubsession):
        subclass_fields = [
            f for f in inspect_field_names(Model)
            if f not in inspect_field_names(BaseGroup)
            and f != 'id'
            ]

        return ['round_number'] + subclass_fields
