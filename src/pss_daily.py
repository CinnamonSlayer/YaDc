#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from datetime import datetime
import discord
from discord.ext import commands
import os
import random
from typing import Dict, List, Tuple

import pss_core as core
import server_settings
import utility as util










# ---------- Constants ----------

DAILY_INFO_FIELDS = [
    'CargoItems',
    'CargoPrices',
    'CommonCrewId',
    'DailyRewardArgument',
    'DailyItemRewards',
    'DailyRewardType',
    'HeroCrewId',
    'LimitedCatalogArgument',
    'LimitedCatalogCurrencyAmount',
    'LimitedCatalogCurrencyType',
    'LimitedCatalogMaxTotal',
    'LimitedCatalogType',
    'News',
    'SaleArgument',
    'SaleItemMask',
    'SaleQuantity',
    'SaleType'
]

DAILY_INFO_FIELDS_TO_CHECK = [
    'LimitedCatalogArgument',
    'LimitedCatalogCurrencyAmount',
    'LimitedCatalogCurrencyType',
    'LimitedCatalogMaxTotal',
    'LimitedCatalogType',
    'SaleArgument',
    'SaleItemMask',
    'SaleQuantity',
    'SaleType'
]










# ---------- ----------

async def try_store_daily_channel(guild_id: int, text_channel_id: int) -> bool:
    success = False
    rows = await server_settings.db_get_autodaily_settings(guild_id=guild_id, can_post=None)
    if len(rows) == 0:
        success = await insert_daily_channel(guild_id, text_channel_id)
        if success == False:
            print(f'[try_store_daily_channel] failed to insert new data row: {guild_id} ({text_channel_id})')
    else:
        if str(rows[0][1]) != str(text_channel_id):
            success = await update_daily_channel(guild_id, text_channel_id, None)
            if success == False:
                print(f'[try_store_daily_channel] failed to update data row: {guild_id} ({text_channel_id})')
        else:
            success = True
    return success


def has_daily_changed(daily_info: Dict[str, str], retrieved_date: datetime, db_daily_info: dict, db_modify_date: datetime) -> bool:
    if retrieved_date.hour >= 23:
        return False

    if db_modify_date is None:
        return True
    elif retrieved_date.day > db_modify_date.day:
        for daily_info_field in DAILY_INFO_FIELDS_TO_CHECK:
            if daily_info[daily_info_field] != db_daily_info[daily_info_field]:
                return True
        return False
    else:
        daily_info = daily_info.copy()
        daily_info.pop('News', None)
        db_daily_info = db_daily_info.copy()
        db_daily_info.pop('News', None)
        return not util.dicts_equal(daily_info, db_daily_info)










# ---------- Utilities ----------

def convert_to_daily_info(dropship_info: dict) -> dict:
    result = {}
    for field_name in DAILY_INFO_FIELDS:
        value = None
        if field_name in dropship_info.keys():
            value = dropship_info[field_name]
        result[field_name] = value
    return result


async def get_daily_channels(ctx: discord.ext.commands.Context, guild_id: int = None, can_post: bool = None) -> list:
    settings = await server_settings.db_get_autodaily_settings(guild_id, can_post)
    result = []
    at_least_one = False
    for (_, channel_id, can_post, _, _, _, _, _, _) in settings:
        if channel_id:
            at_least_one = True
            text_channel = ctx.bot.get_channel(int(channel_id))
            if text_channel:
                guild = text_channel.guild
                result.append(f'{guild.name}: #{text_channel.name} ({can_post})')
            else:
                result.append(f'Invalid channel id: {channel_id}')
    if not at_least_one:
        result.append('Auto-posting of the daily announcement is not configured for any server!')
    return result


async def get_daily_info():
    latest_settings = await core.get_latest_settings()
    result = convert_to_daily_info(latest_settings)
    return result


def get_daily_info_setting_name(field_name: str) -> str:
    return f'daily{field_name}'


async def insert_daily_channel(guild_id: int, channel_id: int) -> bool:
    success = await server_settings.db_create_server_settings(guild_id)
    if success:
        success = await update_daily_channel(guild_id, channel_id=channel_id, latest_message_id=None)
    return success


def remove_duplicate_autodaily_settings(autodaily_settings: list) -> list:
    if not autodaily_settings:
        return autodaily_settings
    result = {}
    for autodaily_setting in autodaily_settings:
        if autodaily_setting.guild.id not in result.keys():
            result[autodaily_setting.guild.id] = autodaily_setting
    return list(result.values())


async def update_daily_channel(guild_id: int, channel_id: int = None, latest_message_id: int = None) -> bool:
    success = True
    if channel_id is not None:
        success = success and await server_settings.db_update_daily_channel_id(guild_id, channel_id)
    if latest_message_id is not None:
        success = success and await server_settings.db_update_daily_latest_message(guild_id, latest_message_id)
    return success


async def db_get_daily_info() -> Tuple[Dict, datetime]:
    result = {}
    modify_dates = []
    for daily_info_field in DAILY_INFO_FIELDS:
        setting_name = get_daily_info_setting_name(daily_info_field)
        value, modify_date = await core.db_get_setting(setting_name)
        if modify_date:
            modify_dates.append(modify_date)
        if value:
            result[daily_info_field] = value
    if result and modify_dates:
        return (result, max(modify_dates))
    else:
        return (dict(), None)


async def db_set_daily_info(daily_info: dict, utc_now: datetime) -> bool:
    result = True
    for key, value in daily_info.items():
        setting_name = get_daily_info_setting_name(key)
        result = await core.db_set_setting(setting_name, value, utc_now=utc_now) and result
    return result










# ---------- Mocks ----------

def mock_get_daily_info():
    utc_now = util.get_utcnow()
    if utc_now.hour < 1:
        if utc_now.minute < 20:
            return __mock_get_daily_info_1()
        else:
            return __mock_get_daily_info_2()
    else:
        return __mock_get_daily_info_1()


def __mock_get_daily_info_1():
    result = {
        'CargoItems': f'{random.randint(0, 200)}x{random.randint(0, 10)}',
        'CargoPrices': f'starbux:{random.randint(0, 10)}',
        'CommonCrewId': f'{random.randint(0, 200)}',
        'DailyItemRewards': f'{random.randint(0, 200)}x1|{random.randint(0, 200)}x1',
        'DailyRewardArgument': f'{random.randint(0, 20)}',
        'DailyRewardType': 'Starbux',
        'HeroCrewId': f'{random.randint(0, 200)}',
        'LimitedCatalogArgument': '183',
        'LimitedCatalogCurrencyAmount': '650',
        'LimitedCatalogCurrencyType': 'Starbux',
        'LimitedCatalogMaxTotal': '100',
        'LimitedCatalogType': 'Item',
        'News': '...',
        'SaleArgument': '344',
        'SaleItemMask': '2',
        'SaleQuantity': '1',
        'SaleType': 'Character'
    }
    return result


def __mock_get_daily_info_2():
    result = {
        'CargoItems': f'{random.randint(0, 200)}x{random.randint(0, 10)}',
        'CargoPrices': f'starbux:{random.randint(0, 10)}',
        'CommonCrewId': f'{random.randint(0, 200)}',
        'DailyItemRewards': f'{random.randint(0, 200)}x1|{random.randint(0, 200)}x1',
        'DailyRewardArgument': f'{random.randint(0, 20)}',
        'DailyRewardType': 'Starbux',
        'HeroCrewId': f'{random.randint(0, 200)}',
        'LimitedCatalogArgument': f'{random.randint(0, 200)}',
        'LimitedCatalogCurrencyAmount': f'{random.randint(0, 20000)}',
        'LimitedCatalogCurrencyType': 'Starbux',
        'LimitedCatalogMaxTotal': '100',
        'LimitedCatalogType': random.choice(['Item', 'Character']),
        'News': '...',
        'SaleArgument': f'{random.randint(0, 200)}',
        'SaleItemMask': f'{random.randint(1, 31)}',
        'SaleQuantity': f'{random.randint(1, 31)}',
        'SaleType': random.choice(['Item', 'Character'])
    }
    return result

