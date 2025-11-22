# Mitsubishi Owner Portal for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

Home Assistant custom integration for Mitsubishi Owner Portal (Japan).

This integration allows you to monitor your Mitsubishi electric vehicle through the official Mitsubishi Owner Portal API.

[日本語ドキュメント](README_JP.md) | [简体中文文档](README_CN.md)

## Features

- Battery level monitoring
- Charging status
- Charging mode
- Plug connection status
- Charging readiness
- Time to full charge
- Ignition state
- Event timestamp tracking

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/aureole999/Mitsubishi-Owner-Portal-HASS`
6. Select "Integration" as the category
7. Click "Add"
8. Find "Mitsubishi Owner Portal" in the list and click "Download"
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page][releases]
2. Extract the `custom_components/mitsubishi_owner_portal` folder
3. Copy it to your Home Assistant's `custom_components` directory
4. Restart Home Assistant

## Configuration

This integration is configured through the UI:

1. Go to Settings → Devices & Services
2. Click "+ Add Integration"
3. Search for "Mitsubishi Owner Portal"
4. Enter your Mitsubishi Owner Portal credentials (email and password)
5. Click "Submit"

Your vehicle will be automatically discovered and added to Home Assistant.

## Supported Sensors

The integration creates the following sensors for each vehicle:

| Sensor | Description | Unit |
|--------|-------------|------|
| Current Battery Level | Battery state of charge | % |
| Charging Status | Current charging status | - |
| Charging Plug Status | Plug connection status | - |
| Charging Mode | Charging mode | - |
| Charging Ready | Charging readiness | - |
| Ignition State | Vehicle ignition state | - |
| Time To Full Charge | Time remaining to full charge | minutes |
| Event Timestamp | Last update timestamp | - |

## Requirements

- Home Assistant 2024.1.0 or newer
- Valid Mitsubishi Owner Portal account (Japan)
- Mitsubishi electric vehicle registered to your account

## Troubleshooting

### Authentication Fails

- Verify your credentials are correct
- Ensure your account works on the official Mitsubishi Owner Portal website
- Check that your vehicle is properly registered to your account

### Sensors Not Updating

- Check your internet connection
- Verify the vehicle has recent data in the Mitsubishi Owner Portal
- Check Home Assistant logs for error messages

## Support

If you encounter any issues or have questions:

1. Check the [existing issues][issues]
2. Create a new issue with detailed information about your problem
3. Include relevant logs from Home Assistant

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

This integration is not affiliated with or endorsed by Mitsubishi Motors Corporation.

---

[releases-shield]: https://img.shields.io/github/release/aureole999/Mitsubishi-Owner-Portal-HASS.svg?style=for-the-badge
[releases]: https://github.com/aureole999/Mitsubishi-Owner-Portal-HASS/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/aureole999/Mitsubishi-Owner-Portal-HASS.svg?style=for-the-badge
[commits]: https://github.com/aureole999/Mitsubishi-Owner-Portal-HASS/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/aureole999/Mitsubishi-Owner-Portal-HASS.svg?style=for-the-badge
[issues]: https://github.com/aureole999/Mitsubishi-Owner-Portal-HASS/issues