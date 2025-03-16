"""
This file is part of renogy_ble.

renogy_ble is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

renogy_ble is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with renogy_ble. If not, see <https://www.gnu.org/licenses/>.
"""

import logging
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import async_add_entities

DOMAIN = "renogy_ble"

SENSOR_TYPES = {
    'battery_percentage': ['Battery Percentage', '%'],
    'battery_voltage': ['Battery Voltage', 'V'],
    'battery_current': ['Battery Current', 'A'],
    'battery_temperature': ['Battery Temperature', '°C'],
    'controller_temperature': ['Controller Temperature', '°C'],
    'load_status': ['Load Status', None],
    'load_voltage': ['Load Voltage', 'V'],
    'load_current': ['Load Current', 'A'],
    'load_power': ['Load Power', 'W'],
    'pv_voltage': ['PV Voltage', 'V'],
    'pv_current': ['PV Current', 'A'],
    'pv_power': ['PV Power', 'W'],
    'max_charging_power_today': ['Max Charging Power Today', 'W'],
    'max_discharging_power_today': ['Max Discharging Power Today', 'W'],
    'charging_amp_hours_today': ['Charging Amp Hours Today', 'Ah'],
    'discharging_amp_hours_today': ['Discharging Amp Hours Today', 'Ah'],
    'power_generation_today': ['Power Generation Today', 'Wh'],
    'power_consumption_today': ['Power Consumption Today', 'Wh'],
    'power_generation_total': ['Power Generation Total', 'Wh'],
    'charging_status': ['Charging Status', None],
    'battery_type': ['Battery Type', None]
}

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Renogy BLE sensors."""
    if discovery_info is None:
        logging.error("No discovery information provided.")
        return

    sensors = []
    for sensor_type in SENSOR_TYPES:
        sensors.append(RenogyBLESensor(sensor_type, discovery_info))

    async_add_entities(sensors, True)
    hass.data[DOMAIN]['entities'] = sensors
    logging.info("Renogy BLE sensors set up successfully.")

class RenogyBLESensor(Entity):
    """Representation of a Renogy BLE sensor."""

    def __init__(self, sensor_type, data):
        """Initialize the sensor."""
        self._sensor_type = sensor_type
        self._name = f"{data['__device']} {SENSOR_TYPES[sensor_type][0]}"
        self._unit_of_measurement = SENSOR_TYPES[sensor_type][1]
        self._state = "unavailable"
        logging.info(f"Initialized sensor: {self._name}")

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    def update(self):
        """Update the sensor state."""
        pass

def update_sensors(hass, data):
    """Update the sensors with new data."""
    for entity in hass.data[DOMAIN]['entities']:
        entity._state = data.get(entity._sensor_type)
        entity.async_write_ha_state()
        logging.info(f"Updated sensor: {entity._name} with state: {entity._state}")
