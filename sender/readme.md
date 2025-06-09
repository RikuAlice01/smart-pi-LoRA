# LoRa AES Encrypted Sender

This project implements a LoRa node that sends encrypted sensor data using AES-256-CBC encryption. The payload is encrypted before transmission to ensure data confidentiality over the air.

---

## Features

* Uses AES-256-CBC encryption with PKCS#7 padding.
* Encryption key loaded securely from an external binary file (`keyfile.bin`).
* Encrypts payload data containing device ID, temperature, humidity, pH, and a counter.
* Retries sending any unsent payloads saved locally in a backup log file.
* Prints encryption timing for performance monitoring.
* Configurable LoRa parameters and mock sensor values via `config.ini`.

---

## Requirements

* Python 3.7+
* `cryptography` package
* LoRaRF library supporting `SX126x`
* A `keyfile.bin` containing a 32-byte (256-bit) AES key.
* A valid `config.ini` with device and LoRa settings.

---

## Setup

1. Install dependencies:

   ```bash
   pip install cryptography
   ```

2. Prepare a 32-byte AES key and save it as `keyfile.bin` in the same directory.

3. Create a `config.ini` file with the following example structure:

   ```ini
   [device]
   id_prefix = node_

   [lora]
   tx_power = 14
   frequency = 868.1
   spreading_factor = 7
   bandwidth = 125
   coding_rate = 5
   preamble_length = 8

   [send]
   mock_temp = 25.5
   mock_hum = 60.0
   mock_ph = 7.0
   interval = 10
   ```

4. Connect your LoRa SX126x device and ensure drivers are installed.

---

## Usage

Run the sender script:

```bash
python sender.py
```

It will:

* Initialize LoRa radio with settings from `config.ini`.
* Generate a unique device ID based on the MAC address.
* Periodically send encrypted payloads containing mock sensor data.
* Retry any unsent payloads saved in `unsent_data.log`.

---

## Backup and Retry

If sending fails (e.g., due to radio issues), the payload is saved to `unsent_data.log`. The system retries sending these backups on subsequent successful transmissions.

---

## Notes

* The receiver must use the same AES key and decryption logic to decode incoming messages.
* Modify the mock sensor values or integrate with real sensors as needed.
* Adjust LoRa parameters in `config.ini` based on your region and hardware.

---

## License

MIT License

---
