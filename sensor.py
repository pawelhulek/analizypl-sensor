"""Platform for sensor integration."""
from __future__ import annotations

from datetime import timedelta
import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from homeassistant.components.sensor import SensorEntity, PLATFORM_SCHEMA, SensorStateClass, SensorDeviceClass
from homeassistant.const import CONF_ID, CONF_COUNT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import Throttle

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ID): cv.string,
    vol.Required(CONF_COUNT): cv.string
})


def setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
) -> None:
    add_entities([AnalizySensor(hass, config)])


class AnalizySensor(SensorEntity):
    def __init__(self, hass, config: dict) -> None:
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._state = None
        self.hass = hass
        self.quotationId = config.get(CONF_ID)
        self.amount = config.get(CONF_COUNT)
        response = requests.get("https://www.analizy.pl/api/quotation/fio/" + self.quotationId).json()
        self.entity_name = response.get('label')
        self.update = Throttle(timedelta(minutes=(600)))(self._update)

    @property
    def name(self) -> str:
        return self.entity_name

    @property
    def state(self):
        return self._state

    def _update(self) -> None:
        response = requests.get("https://www.analizy.pl/api/quotation/fio/" + self.quotationId).json()
        result = max(response.get('series')[0].get('price'), key=lambda item: item.get('date')).get('value')
        self._state = float(result) * float(self.amount)
        self._attr_native_unit_of_measurement = response.get('currency')
