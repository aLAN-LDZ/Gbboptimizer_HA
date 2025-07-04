import logging
import ssl

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, CONF_BROKER, CONF_PORT, CONF_PLANT_ID, CONF_PLANT_TOKEN, CONF_USE_TLS

import paho.mqtt.client as mqtt

_LOGGER = logging.getLogger(__name__)

mqtt_clients = {}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Setting up GbbOptimizer MQTT integration")

    plant_id = entry.data[CONF_PLANT_ID]
    token = entry.data[CONF_PLANT_TOKEN]
    broker = entry.data[CONF_BROKER]
    port = entry.data[CONF_PORT]
    use_tls = entry.data.get(CONF_USE_TLS, True)

    client_id = f"ha_{plant_id}"

    def on_connect(client, userdata, flags, rc):
        _LOGGER.debug(f"[{plant_id}] on_connect called with rc={rc}")
        if rc == 0:
            _LOGGER.info(
                f"[{plant_id}] Successfully connected to MQTT broker at {broker}:{port} with client_id '{client_id}'"
            )
            if use_tls:
                _LOGGER.debug(f"[{plant_id}] TLS is enabled")

            topic = f"{plant_id}/signals/data"
            client.subscribe(topic)
            _LOGGER.info(f"[{plant_id}] Subscribed to topic: {topic}")
        else:
            _LOGGER.error(f"[{plant_id}] MQTT connection failed with code {rc}")

    def on_message(client, userdata, msg):
        _LOGGER.info(f"[{plant_id}] Received MQTT message on {msg.topic}: {msg.payload.decode()}")

    def setup_mqtt_client():
        client = mqtt.Client(client_id=client_id)
        client.username_pw_set(plant_id, token)
        client.on_connect = on_connect
        client.on_message = on_message

        if use_tls:
            client.tls_set(cert_reqs=ssl.CERT_NONE)
            client.tls_insecure_set(True)

        client.connect(broker, port)
        client.loop_start()
        mqtt_clients[plant_id] = client

    try:
        await hass.async_add_executor_job(setup_mqtt_client)
    except Exception as e:
        _LOGGER.error(f"Failed to connect to MQTT broker: {e}")
        raise ConfigEntryNotReady from e

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    plant_id = entry.data[CONF_PLANT_ID]
    client = mqtt_clients.pop(plant_id, None)
    if client:
        _LOGGER.info(f"[{plant_id}] Disconnecting MQTT client")
        client.loop_stop()
        client.disconnect()
    return True