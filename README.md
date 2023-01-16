# Mitsubishi Owner Portal (Japan) for HomeAssistant

## Installing

> copy `custom_components/mitsubishi_owner_portal` folder to `custom_components` folder in your HomeAssistant config folder

## Config

```yaml
# configuration.yaml

mitsubishi_owner_portal:
  # Single account
  username: 86-18866668888 # Username of Mitsubishi Owner Portal
  password: abcdefghijklmn # MD5 or Raw password
  scan_interval:  # Optional, default is 01:00:00

  # Multiple accounts
  accounts:
    - username: email1@domain.com
      password: password1
    - username: email2@domain.com
      password: password2
```