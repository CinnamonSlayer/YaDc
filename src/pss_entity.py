#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from abc import ABC, abstractstaticmethod
import discord
from typing import Callable, Dict, List, Optional, Tuple, Union

from cache import PssCache
import pss_core as core
import settings










# ---------- Typing definitions ----------

EntityDesignInfo = Dict[str, 'EntityDesignInfo']
EntitiesDesignsData = Dict[str, EntityDesignInfo]










# ---------- Classes ----------

class EntityDesignDetailProperty(object):
    def __init__(self, display_name: Union[str, Callable[[EntityDesignInfo, EntitiesDesignsData], str]], transform_function: Callable[[EntityDesignInfo, EntitiesDesignsData], str], force_display_name: bool):
        if isinstance(display_name, str):
            self.__display_name: str = display_name
            self.__display_name_function: Callable[[list], str] = None
        elif isinstance(display_name, Callable[[list], str]):
            self.__display_name: str = None
            self.__display_name_function: Callable[[list], str] = display_name
        else:
            raise TypeError('The display_name must either be of type \'str\' or \'Callable[[EntityDesignInfo], ]\'.')

        self.__transform_function: Callable[[EntityDesignInfo], str] = transform_function
        self.__force_display_name: bool = force_display_name


    @property
    def force_display_name(self) -> bool:
        return self.__force_display_name


    def get_full_property(self, entity_design_info: EntityDesignInfo, entities_designs_data: EntitiesDesignsData) -> Tuple[str, str]:
        if self.__force_display_name:
            display_name = self.__get_display_name(entity_design_info, entities_designs_data)
        else:
            display_name = None
        value = self.__get_value(entity_design_info, entities_designs_data)
        return (display_name, value)


    def __get_display_name(self, entity_design_info: EntityDesignInfo, entities_designs_data: EntitiesDesignsData) -> str:
        if self.__display_name:
            return self.__display_name
        elif self.__display_name_function:
            result = self.__display_name_function(entity_design_info, entities_designs_data)
            return result
        else:
            return ''


    def __get_value(self, entity_design_info: EntityDesignInfo, entities_designs_data: EntitiesDesignsData) -> str:
        if self.__transform_function:
            result = self.__transform_function(entity_design_info, entities_designs_data)
            return result
        else:
            return ''










class EntityDesignDetailEmbedProperty(EntityDesignDetailProperty):
    def __init__(self, display_name: Union[str, Callable[[EntityDesignInfo, EntitiesDesignsData], str]], transform_function: Callable[[EntityDesignInfo, EntitiesDesignsData], str]):
        super().__init__(display_name, transform_function, True)










class EntityDesignDetails(object):
    def __init__(self, entity_design_info: EntityDesignInfo, title: EntityDesignDetailProperty, description: EntityDesignDetailProperty, properties_long: List[EntityDesignDetailProperty], properties_short: List[EntityDesignDetailProperty], properties_embed: List[EntityDesignDetailProperty], entities_designs_data: Optional[EntitiesDesignsData] = None):
        """

        """
        self.__entities_designs_data: EntitiesDesignsData = entities_designs_data
        self.__entity_design_info: EntityDesignInfo = entity_design_info
        self.__title_property: EntityDesignDetailProperty = title
        self.__description_property: EntityDesignDetailProperty = description
        self.__properties_long: List[EntityDesignDetailProperty] = properties_long
        self.__properties_short: List[EntityDesignDetailProperty] = properties_short
        self.__properties_embed: List[EntityDesignDetailProperty] = properties_embed
        self.__title: str = None
        self.__description: str = None
        self.__details_embed: List[Tuple[str, str]] = None
        self.__details_long: List[Tuple[str, str]] = None
        self.__details_short: List[Tuple[str, str]] = None


    @property
    def title(self) -> str:
        if self.__title is None:
            self.__title = self.__title_property.get_full_property(self.__entity_design_info, self.__entities_designs_data)
        return self.__title

    @property
    def description(self) -> str:
        if self.__description is None:
            self.__description: str = self.__description_property.get_full_property(self.__entity_design_info, self.__entities_designs_data)
        return self.__description

    @property
    def details_embed(self) -> List[Tuple[str, str]]:
        if self.__details_embed is None:
            self.__details_embed = self._get_properties(self.__properties_embed)
        return self.__details_embed

    @property
    def details_long(self) -> List[Tuple[str, str]]:
        if self.__details_long is None:
            self.__details_long = self._get_properties(self.__properties_long)
        return self.__details_long

    @property
    def details_short(self) -> List[Tuple[str, str]]:
        if self.__details_short is None:
            self.__details_short = self._get_properties(self.__properties_short)
        return self.__details_short


    def get_details_as_embed(self) -> discord.Embed:
        result = discord.Embed(title=self.title, description=self.description)
        for detail in self.details_embed:
            result.add_field(name=detail.name, value=detail.value)
        return result


    def get_details_as_text_long(self) -> List[str]:
        result = []
        result.append(f'**{self.title}**')
        result.append(f'_{self.description}_')
        for detail in self.details_long:
            if detail.force_display_name:
                result.append(f'{detail.name} = {detail.value}')
            else:
                result.append(detail.value)
        return result


    def get_details_as_text_short(self) -> List[str]:
        details = []
        for detail in self.details_short:
            if detail.force_display_name:
                details.append(f'{detail.name} = {detail.value}')
            else:
                details.append(detail.value)
        result = f'{self.title} ({", ".join(details)})'
        return result


    def _get_properties(self, properties: List[EntityDesignDetailProperty]):
        result: List[Tuple[str, str]] = []
        entity_design_detail_property: EntityDesignDetailProperty = None
        for entity_design_detail_property in properties:
            result.append(entity_design_detail_property.get_full_property(self.__entity_design_info, self.__entities_designs_data))
        return result










class EntityDesignDetailsCollection():
    def __init__(self, entity_ids: List[str], big_set_threshold: int = 3):
        entities_designs_data = None
        self.__entities_designs_details: List[EntityDesignDetails] = [entity_design_data for entity_design_data in entity_ids if entity_design_data in entities_designs_data.keys()]
        self.__big_set_threshold: int = big_set_threshold
        pass


    def get_entity_details_as_embed(self) -> List[discord.Embed]:
        return []


    def get_entity_details_as_text(self) -> List[str]:
        result = []
        set_size = len(self.__entities_designs_details)
        entity_design_details: EntityDesignDetails
        for i, entity_design_details in enumerate(self.__entities_designs_details, start=1):
            if set_size > self.__big_set_threshold:
                result.extend(entity_design_details.get_details_as_text_short())
            else:
                result.extend(entity_design_details.get_details_as_text_long())
                if i < set_size:
                    result.append(settings.EMPTY_LINE)
        return result










class EntityDesignsRetriever:
    def __init__(self, entity_design_base_path: str, entity_design_key_name: str, entity_design_description_property_name: str, cache_name: str = None, sorted_key_function: Callable[[dict, dict], str] = None, fix_data_delegate: Callable[[str], str] = None, cache_update_interval: int = 10):
        self.__cache_name: str = cache_name or ''
        self.__base_path: str = entity_design_base_path
        self.__key_name: str = entity_design_key_name or None
        self.__description_property_name: str = entity_design_description_property_name
        self.__sorted_key_function: Callable[[dict, dict], str] = sorted_key_function
        self.__fix_data_delegate: Callable[[str], str] = fix_data_delegate

        self.__cache = PssCache(
            self.__base_path,
            self.__cache_name,
            key_name=self.__key_name,
            update_interval=cache_update_interval
        )


    def get_data_dict3(self) -> Dict[str, Dict[str, object]]:
        return self.__cache.get_data_dict3()


    def get_entity_design_details_by_id(self, entity_id: str, entity_designs_data: Dict[str, Dict[str, object]] = None) -> EntityDesignDetails:
        pass


    def get_entity_design_info_by_id(self, entity_design_id: str, entity_designs_data: Dict[str, Dict[str, object]] = None) -> Dict[str, object]:
        entity_designs_data = entity_designs_data or self.get_data_dict3()
        if entity_design_id in entity_designs_data.keys():
            return entity_designs_data[entity_design_id]
        else:
            return None


    def get_entity_design_info_by_name(self, entity_name: str, entity_designs_data: Dict[str, Dict[str, object]] = None) -> Dict[str, object]:
        entity_designs_data = entity_designs_data or self.get_data_dict3()
        entity_design_id = self.get_entity_design_id_by_name(entity_name, entity_designs_data=entity_designs_data)

        if entity_design_id and entity_design_id in entity_designs_data.keys():
            return entity_designs_data[entity_design_id]
        else:
            return None


    def get_entities_designs_infos_by_name(self, entity_name: str, entity_designs_data: Dict[str, Dict[str, object]] = None, sorted_key_function: Callable[[dict, dict], str] = None) -> List[Dict[str, object]]:
        entity_designs_data = entity_designs_data or self.get_data_dict3()
        sorted_key_function = sorted_key_function or self.__sorted_key_function

        entity_design_ids = self.get_entities_designs_ids_by_name(entity_name, entity_designs_data=entity_designs_data)
        entity_designs_data_keys = entity_designs_data.keys()
        result = [entity_designs_data[entity_design_id] for entity_design_id in entity_design_ids if entity_design_id in entity_designs_data_keys]
        if sorted_key_function is not None:
            result = sorted(result, key=lambda entity_info: (
                sorted_key_function(entity_info, entity_designs_data)
            ))

        return result


    def get_entity_design_id_by_name(self, entity_name: str, entity_designs_data: Dict[str, Dict[str, object]] = None) -> str:
        results = self.get_entities_designs_ids_by_name(entity_name, entity_designs_data)
        if len(results) > 0:
            return results[0]
        else:
            return None


    def get_entities_designs_ids_by_name(self, entity_name: str, entity_designs_data: Dict[str, Dict[str, object]] = None) -> List[str]:
        entity_designs_data = entity_designs_data or self.get_data_dict3()
        results = core.get_ids_from_property_value(entity_designs_data, self.__description_property_name, entity_name, fix_data_delegate=self.__fix_data_delegate)
        return results


    def update_cache(self) -> None:
        self.__cache.update_data()
