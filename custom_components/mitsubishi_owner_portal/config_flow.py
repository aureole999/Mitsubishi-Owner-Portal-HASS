import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from . import MitsubishiOwnerPortalAccount, CONF_USER_ID, CONF_VERIFY_SSL
from .const import DOMAIN


class FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mitsubishi Owner Portal."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input:
            await self.async_set_unique_id(user_input.get(CONF_USERNAME))
            self._abort_if_unique_id_configured()
            account = MitsubishiOwnerPortalAccount(self.hass, {**user_input})
            login_valid = await account.async_login()
            if login_valid:
                vhs = await account.async_get_vehicles()
                acc = user_input | {CONF_USER_ID: account.uid}
                return self.async_create_entry(
                    title=user_input.get(CONF_USERNAME),
                    data={"account": acc, "vehicles": vhs}
                )
            else:
                errors["base"] = "auth_error"

        data_schema = {
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Optional(CONF_VERIFY_SSL, default=True): bool,
        }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=errors
        )

    async def async_step_reconfigure(self, user_input=None) -> FlowResult:
        """Handle reconfiguration of the integration."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if user_input is not None:
            errors = {}
            account = MitsubishiOwnerPortalAccount(self.hass, {**user_input})
            login_valid = await account.async_login()

            if login_valid:
                vhs = await account.async_get_vehicles()
                acc = user_input | {CONF_USER_ID: account.uid}
                return self.async_update_reload_and_abort(
                    entry,
                    data={"account": acc, "vehicles": vhs},
                    title=user_input.get(CONF_USERNAME)
                )
            else:
                errors["base"] = "auth_error"

            data_schema = {
                vol.Required(CONF_USERNAME, default=user_input.get(CONF_USERNAME)): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_VERIFY_SSL, default=user_input.get(CONF_VERIFY_SSL, True)): bool,
            }
            return self.async_show_form(
                step_id="reconfigure",
                data_schema=vol.Schema(data_schema),
                errors=errors
            )

        # Pre-fill with existing values
        current_account = entry.data.get("account", {})
        data_schema = {
            vol.Required(CONF_USERNAME, default=current_account.get(CONF_USERNAME)): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Optional(CONF_VERIFY_SSL, default=current_account.get(CONF_VERIFY_SSL, True)): bool,
        }
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(data_schema),
            description_placeholders={"username": current_account.get(CONF_USERNAME)}
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Mitsubishi Owner Portal."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            # If password is provided, validate credentials
            if user_input.get(CONF_PASSWORD):
                current_account = self.config_entry.data.get("account", {})
                test_account = {
                    CONF_USERNAME: current_account.get(CONF_USERNAME),
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                    CONF_VERIFY_SSL: user_input.get(CONF_VERIFY_SSL, True),
                }
                account = MitsubishiOwnerPortalAccount(self.hass, test_account)
                login_valid = await account.async_login()

                if login_valid:
                    # Update the config entry data with new password
                    vhs = await account.async_get_vehicles()
                    acc = test_account | {CONF_USER_ID: account.uid}
                    self.hass.config_entries.async_update_entry(
                        self.config_entry,
                        data={"account": acc, "vehicles": vhs}
                    )
                    # Reload the integration to apply new settings
                    await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                    return self.async_create_entry(title="", data={})
                else:
                    errors["base"] = "auth_error"
            else:
                # Just update verify_ssl without password change
                current_account = self.config_entry.data.get("account", {})
                current_account[CONF_VERIFY_SSL] = user_input.get(CONF_VERIFY_SSL, True)
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={"account": current_account, "vehicles": self.config_entry.data.get("vehicles")}
                )
                # Reload the integration to apply new SSL settings
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                return self.async_create_entry(title="", data={})

        current_account = self.config_entry.data.get("account", {})
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_PASSWORD, description={"suggested_value": ""}): str,
                vol.Optional(CONF_VERIFY_SSL, default=current_account.get(CONF_VERIFY_SSL, True)): bool,
            }),
            description_placeholders={
                "username": current_account.get(CONF_USERNAME),
            }
        )
