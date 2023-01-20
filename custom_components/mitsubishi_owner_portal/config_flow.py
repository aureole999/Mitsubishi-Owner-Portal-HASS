import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from . import MitsubishiOwnerPortalAccount, CONF_USER_ID
from .const import DOMAIN

CONF_USERNAME = "username"
CONF_PASSWORD = "password"


class FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, user_input=None) -> FlowResult:

        errors = {}
        if user_input:
            await self.async_set_unique_id(user_input.get(CONF_USERNAME))
            self._abort_if_unique_id_configured()
            account = MitsubishiOwnerPortalAccount(self.hass, {**user_input})
            login_valid = await account.async_login()
            if login_valid:
                vhs = await account.async_get_vehicles()
                acc = user_input | {CONF_USER_ID: account.uid}
                return self.async_create_entry(title=user_input.get(CONF_USERNAME),
                                               data={"account": acc, "vehicles": vhs})
            else:
                errors["base"] = "auth_error"

        data_schema = {
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str
        }
        return self.async_show_form(step_id="user", data_schema=vol.Schema(data_schema), errors=errors)
