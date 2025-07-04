from homeassistant import config_entries
import voluptuous as vol
from homeassistant.const import CONF_NAME

from .const import (
    DOMAIN,
    CONF_PLANT_ID,
    CONF_PLANT_TOKEN,
    CONF_BROKER,
    CONF_PORT,
    CONF_USE_TLS,
    DEFAULT_PORT,
    DEFAULT_USE_TLS,
)

class GbbOptimizerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # TODO: Można dodać sprawdzenie poprawności danych (np. połączenie MQTT)
            return self.async_create_entry(
                title=f"GbbOptimizer {user_input[CONF_PLANT_ID]}",
                data=user_input,
            )

        schema = vol.Schema({
            vol.Required(CONF_PLANT_ID): str,
            vol.Required(CONF_PLANT_TOKEN): str,
            vol.Required(CONF_BROKER, default="mqtt.gbboptimizer.com"): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Optional(CONF_USE_TLS, default=DEFAULT_USE_TLS): bool,
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)