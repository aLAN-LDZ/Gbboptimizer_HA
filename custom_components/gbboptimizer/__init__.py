import asyncio
import logging
import ssl

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    DOMAIN,
    CONF_BROKER,
    CONF_PORT,
    CONF_PLANT_ID,
    CONF_PLANT_TOKEN,
    CONF_USE_TLS,
)

from asyncio_mqtt import Client, MqttError

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

    tls_context = None
    if use_tls:
        tls_context = ssl.create_default_context()
        # Jeśli chcesz wyłączyć weryfikację certyfikatu (niezalecane):
        # tls_context.check_hostname = False
        # tls_context.verify_mode = ssl.CERT_NONE

    client = Client(
        hostname=broker,
        port=port,
        username=plant_id,
        password=token,
        client_id=client_id,
        tls_context=tls_context,
    )

    # Task do odbierania wiadomości MQTT (będzie działał w tle)
    async def mqtt_message_handler():
        async with client.unfiltered_messages() as messages:
            await client.subscribe(f"{plant_id}/signals/data")
            _LOGGER.info(f"[{plant_id}] Subscribed to topic: {plant_id}/signals/data")

            async for message in messages:
                payload = message.payload.decode()
                topic = message.topic
                _LOGGER.info(f"[{plant_id}] Received MQTT message on {topic}: {payload}")
                # Tutaj możesz dodać dalsze przetwarzanie wiadomości

    # Start klienta MQTT i odbioru wiadomości w tle
    try:
        await client.connect()
    except MqttError as e:
        _LOGGER.error(f"[{plant_id}] Failed to connect to MQTT broker: {e}")
        raise ConfigEntryNotReady from e

    mqtt_task = hass.async_create_task(mqtt_message_handler())
    mqtt_clients[plant_id] = (client, mqtt_task)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    plant_id = entry.data[CONF_PLANT_ID]
    client_task = mqtt_clients.pop(plant_id, None)

    if client_task:
        client, task = client_task

        _LOGGER.info(f"[{plant_id}] Disconnecting MQTT client")

        await client.disconnect()

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    return True