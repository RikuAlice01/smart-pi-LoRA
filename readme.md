# smart-pi-LoRA - LoRa Data Sender

This project is a Python script for sending data via LoRa (Long Range) using the SX126x module. It is suitable for IoT applications and sensors that require long-range wireless data transmission.

## File Structure

- `send/lora_send.py` - The main script for sending data via LoRa
- `config.ini` - Configuration file containing settings such as frequency, transmission power, mock data, etc.
- `unsent_data.log` - Backup file for storing unsent data to retry sending later

---

## Key Features

- Reads configuration values from `config.ini`
- Generates a Device ID from the machine's MAC address with a configurable prefix
- Sends mock sensor data including temperature (temp), humidity (hum), and pH (ph)
- Backs up unsent data in `unsent_data.log`
- Attempts to resend backed-up data automatically when the script runs

---

## Installation and Usage

1. Install the required library (if any)
```bash
pip install LoRaRF
````

2. Edit the `config.ini` file to match your environment, for example:

```ini
[device]
id_prefix = node_

[lora]
tx_power = 14
frequency = 868.0
spreading_factor = 7
bandwidth = 125
coding_rate = 5
preamble_length = 8

[send]
mock_temp = 25.0
mock_hum = 50.0
mock_ph = 7.0
interval = 10
```

3. Run the script

```bash
python send/lora_send.py
```

---

## Example Operation

* When running the script, it starts sending payloads in the format:

  ```
  id:node_123456,temp:25.0,hum:50.0,ph:7.0,count:0
  ```

* If sending fails, the data will be saved to the backup file and retried in subsequent attempts.

---

## Cautions

* Ensure the LoRa SX126x hardware is connected to your machine before running
* Set frequency and other parameters correctly according to your hardware and country regulations
* The `LoRaRF` library is required to control the SX126x module

---

## Summary

This script makes it easy to send data over LoRa with backup and automatic retry features, suitable for IoT projects that require reliable data transmission in real-world conditions.

---
