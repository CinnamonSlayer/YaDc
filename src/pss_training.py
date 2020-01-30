#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from datetime import timedelta
import discord
from typing import Callable, List, Tuple

from cache import PssCache
import emojis
import pss_assert
import pss_core as core
import pss_entity as entity
import pss_item as item
import pss_lookups as lookups
import pss_research as research
import settings
import utility as util

# ---------- Constants ----------

TRAINING_DESIGN_BASE_PATH = 'TrainingService/ListAllTrainingDesigns2?languageKey=en'
TRAINING_DESIGN_KEY_NAME = 'TrainingDesignId'
TRAINING_DESIGN_DESCRIPTION_PROPERTY_NAME = 'TrainingName'










# ---------- Classes ----------

class TrainingDetails(entity.EntityDesignDetails):
    def __init__(self, training_info: dict):
        required_room_level = training_info['RequiredRoomLevel']
        training_rank = int(training_info['Rank'])
        training_id = training_info[TRAINING_DESIGN_KEY_NAME]

        stats = []
        stats.extend(lookups.STATS_LEFT)
        stats.extend(lookups.STATS_RIGHT)
        training_item_details = item.get_item_details_short_by_training_id(training_id)
        room_name, _ = _get_room_names(training_rank)
        if room_name:
            room_name = f'{room_name} lvl {required_room_level}'
        stat_chances = _get_stat_chances(stats, training_info)
        xp_stat = _get_stat_chance_as_text(*_get_stat_chance('Xp', training_info, guaranteed=True))
        stat_chances.append(xp_stat)

        self.__chances: str = ' '.join(stat_chances)
        self.__cost: str = _get_cost_as_text(training_info)
        self.__duration: str = _get_duration_as_text(training_info)
        self.__fatigue: str = _get_fatigue_as_text(training_info)
        self.__required_research: str = research.get_research_name_from_id(training_info['RequiredResearchDesignId'])
        self.__room_name: str = room_name
        self.__training_item_details: str = ', '.join(training_item_details)

        details_long: List[Tuple[str, str]] = [
            ('Duration', self.__duration),
            ('Cost', self.__cost),
            ('Fatigue', self.__fatigue),
            ('Training room', self.__room_name),
            ('Research required', self.__required_research),
            ('Consumable', self.__training_item_details),
            ('Results', self.__chances)
        ]
        details_short: List[Tuple[str, str, bool]] = [
            (None, self.__chances, False)
        ]

        super().__init__(
            name=training_info[TRAINING_DESIGN_DESCRIPTION_PROPERTY_NAME],
            description=training_info['TrainingDescription'],
            details_long=details_long,
            details_short=details_short
        )


    @property
    def chances(self) -> str:
        return self.__chances

    @property
    def cost(self) -> str:
        return self.__cost

    @property
    def duration(self) -> str:
        return list(self.__duration)

    @property
    def fatigue(self) -> str:
        return self.__fatigue

    @property
    def required_research(self) -> str:
        return self.__required_research

    @property
    def room_name(self) -> str:
        return self.__room_name

    @property
    def training_item_details(self) -> str:
        return self.__training_item_details













# ---------- Training info ----------

def get_training_details_from_name(training_name: str, as_embed: bool = settings.USE_EMBEDS):
    pss_assert.valid_entity_name(training_name)

    training_infos = training_designs_retriever.get_entities_designs_infos_by_name(training_name)
    trainings_details = [TrainingDetails(training_info) for training_info in training_infos]

    if not training_infos:
        return [f'Could not find a training named **{training_name}**.'], False
    else:
        if as_embed:
            return _get_training_info_as_embed(training_name, trainings_details), True
        else:
            return _get_training_info_as_text(training_name, trainings_details), True


def _get_training_info_as_embed(training_name: str, trainings_details: List[TrainingDetails]) -> discord.Embed:
    result = [training_details.get_details_as_embed() for training_details in trainings_details]
    return result


def _get_training_info_as_text(training_name: str, trainings_details: List[TrainingDetails]) -> List[str]:
    trainings_details_count = len(trainings_details)

    lines = [f'Training stats for **{training_name}**']
    for i, training_details in enumerate(trainings_details):
        if trainings_details_count > 2:
            lines.extend(training_details.get_details_as_text_short())
        else:
            lines.extend(training_details.get_details_as_text_long())
            if i < trainings_details_count - 1:
                lines.append(settings.EMPTY_LINE)

    return lines










# ---------- Helper functions ----------

def _get_cost_as_text(training_info: dict) -> str:
    cost = int(training_info['MineralCost'])
    if cost > 0:
        cost_compact = util.get_reduced_number_compact(cost)
        result = f'{cost_compact} {emojis.pss_min_big}'
    else:
        result = None
    return result


def _get_duration_as_text(training_info: dict) -> str:
    seconds = int(training_info['Duration'])
    if seconds > 0:
        result = util.get_formatted_duration(seconds, include_relative_indicator=False)
    else:
        result = 'Instant'
    return result


def _get_fatigue_as_text(training_info: dict) -> str:
    fatigue = int(training_info['Fatigue'])
    if fatigue > 0:
        result = f'{fatigue}h'
    else:
        result = None
    return result


def _get_key_for_training_sort(training_info: dict, training_designs_data: dict) -> str:
    result = ''
    parent_infos = _get_parents(training_info, training_designs_data)
    if parent_infos:
        for parent_info in parent_infos:
            result += parent_info[TRAINING_DESIGN_KEY_NAME].zfill(4)
    result += training_info[TRAINING_DESIGN_KEY_NAME].zfill(4)
    return result


def _get_parents(training_info: dict, training_designs_data: dict) -> list:
    parent_training_design_id = training_info['RequiredTrainingDesignId']
    if parent_training_design_id == '0':
        parent_training_design_id = None

    if parent_training_design_id is not None:
        parent_info = training_designs_data[parent_training_design_id]
        result = _get_parents(parent_info, training_designs_data)
        result.append(parent_info)
        return result
    else:
        return []


def _get_stat_chances(stat_names: list, training_info: dict) -> list:
    chances = []
    max_chance_value = 0
    result = []
    for stat_name in stat_names:
        stat_chance = _get_stat_chance(stat_name, training_info)
        if stat_chance is not None:
            chances.append(stat_chance)

    if chances:
        chance_values = [stat_chance[2] for stat_chance in chances]
        max_chance_value = max(chance_values)
        result = [_get_stat_chance_as_text(*stat_chance) for stat_chance in chances if stat_chance[2] == max_chance_value]
        result.extend([_get_stat_chance_as_text(*stat_chance) for stat_chance in chances if stat_chance[2] != max_chance_value])

    return result


def _get_stat_chance(stat_name: str, training_info: dict, guaranteed: bool = False) -> (str, str, str, str):
    if stat_name and training_info:
        chance_name = f'{stat_name}Chance'
        if chance_name in training_info.keys():
            stat_chance = int(training_info[chance_name])
            if stat_chance > 0:
                stat_emoji = lookups.STAT_EMOJI_LOOKUP[stat_name]
                stat_unit = lookups.STAT_UNITS_LOOKUP[stat_name]
                operator = '' if guaranteed else '\u2264'
                return (stat_emoji, operator, stat_chance, stat_unit)
    return None


def _get_stat_chance_as_text(stat_emoji: str, operator: str, stat_chance: str, stat_unit: str) -> str:
    return f'{stat_emoji} {operator}{stat_chance}{stat_unit}'


def _get_room_names(rank: int) -> Tuple[str, str]:
    if rank in lookups.TRAINING_RANK_ROOM_LOOKUP.keys():
        return lookups.TRAINING_RANK_ROOM_LOOKUP[rank]
    else:
        return (None, None)










# ---------- Initilization ----------

training_designs_retriever = entity.EntityDesignsRetriever(
    TRAINING_DESIGN_BASE_PATH,
    TRAINING_DESIGN_KEY_NAME,
    TRAINING_DESIGN_DESCRIPTION_PROPERTY_NAME,
    cache_name='TrainingDesigns',
    sorted_key_function=_get_key_for_training_sort
)