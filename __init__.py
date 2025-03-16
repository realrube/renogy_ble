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
import asyncio
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
import configparser

from .RoverClient import RoverClient
from .Utils import *

logging = logging.getLogger(__name__)

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

async def async_setup_entry(hass, entry):
    if DOMAIN in hass.data:
        logging.warning("Renogy BLE already set up. Skipping duplicate setup.")
        return False  # Prevent reloading

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]['entities'] = []
    logging.info("Setting up Renogy BLE component...")
    return True

async def async_setup(hass: HomeAssistant, haconfig: dict):
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
        hass.data[DOMAIN]['entities'] = []

    config = configparser.ConfigParser()
    config['device'] = {
        'adapter': 'hci0',
        'mac_addr': 'F8:55:48:17:EE:26',	#MODIFY THIS 
        'alias': 'BT-TH-4817EE26',		#MODIFY THIS
        'type': 'RNG_CTRL',
        'device_id': '255'			#USE 255 OR 96
    }
    config['data'] = {
        'enable_polling': 'true',
        'poll_interval': '5',
        'temperature_unit': 'C'
    }

    def on_data_received(client, data):
        filtered_data = Utils.filter_fields(data, config['data'].get('fields', []))
        logging.info(f"{client.ble_manager.device.name} => {filtered_data}")
        if not config['data'].getboolean('enable_polling'):
            client.stop()
        update_sensors(hass, filtered_data)

    def on_error(client, error):
        logging.error(f"RoverClient failed: {error}")
        set_sensors_unavailable(hass)

    async def connect_client():
        client = RoverClient(config, on_data_received, on_error)
        while True:
            try:
                await client.connect()
                break
            except Exception as e:
                logging.error(f"RoverClient failed: {e}. Retrying in 5 seconds...")
                set_sensors_unavailable(hass)
                await asyncio.sleep(5)

    hass.loop.create_task(connect_client())

    sensors = []
    for sensor_type in SENSOR_TYPES:
        sensors.append(RenogyBLESensor(sensor_type, config['device']['alias'], config['device']['mac_addr']))

    hass.data[DOMAIN]['entities'] = sensors
    for sensor in sensors:
        hass.states.async_set(sensor.entity_id, sensor.state, sensor.attributes)
    logging.info("Renogy BLE sensors set up successfully.")

    return True

def set_sensors_unavailable(hass):
    """Set all sensors to unavailable."""
    for entity in hass.data[DOMAIN]['entities']:
        entity._state = "unavailable"
        hass.states.async_set(entity.entity_id, entity.state, entity.attributes)
        logging.info(f"Set sensor: {entity._name} to unavailable")

def update_sensors(hass, data):
    """Update the sensors with new data."""
    for entity in hass.data[DOMAIN]['entities']:
        entity._state = data.get(entity._sensor_type)
        hass.states.async_set(entity.entity_id, entity.state, entity.attributes)
        logging.info(f"Updated sensor: {entity._name} with state: {entity._state}")

class RenogyBLESensor(Entity):
    """Representation of a Renogy BLE sensor."""

    def __init__(self, sensor_type, device_name, mac_addr):
        """Initialize the sensor."""
        self._sensor_type = sensor_type
        self._name = f"{device_name} {SENSOR_TYPES[sensor_type][0]}"
        self._unit_of_measurement = SENSOR_TYPES[sensor_type][1]
        self._state = "unavailable"
        self._mac_addr = mac_addr
        self.entity_id = f"sensor.{device_name.lower().replace('-', '').replace(' ', '_')}_{sensor_type}"
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

    @property
    def attributes(self):
        """Return the state attributes."""
        return {
            "unit_of_measurement": self._unit_of_measurement,
            "mac_address": self._mac_addr,
        }

    def update(self):
        """Update the sensor state."""
        pass
