# LoRa Encrypted Communication

This project demonstrates a secure communication system using LoRa SX126x modules with AES-256 encryption. It includes both transmitter and receiver Python scripts that send and receive encrypted payloads.

## Features

- Encrypts payload data with AES-256-CBC using a 32-byte key.
- Secure key loading from a binary file (`keyfile.bin`).
- Automatic retry and backup of unsent messages on the transmitter side.
- Decrypts received messages on the receiver side.
- Uses base64 encoding to transmit encrypted data as strings.
- Configurable LoRa parameters via `config.ini`.
- Measures encryption time for performance insight.

## Requirements

- Python 3.7+
- [`cryptography`](https://pypi.org/project/cryptography/) library
- `LoRaRF` Python library for SX126x (make sure to install or provide your own)
  
Install dependencies using:

```bash
pip install cryptography LoRaRF
````

## Setup

1. Prepare your AES key file `keyfile.bin` with exactly 32 bytes (256 bits).

2. Create or modify `config.ini` with your LoRa settings, for example:

```ini
[lora]
frequency = 915.0
spreading_factor = 7
bandwidth = 125
coding_rate = 5
preamble_length = 8

[device]
id_prefix = node_

[send]
mock_temp = 25.5
mock_hum = 60.0
mock_ph = 6.5
interval = 10
```

3. Run the transmitter script to start sending encrypted data.

4. Run the receiver script to listen and decrypt incoming messages.

## Usage

* **Transmitter**: continuously sends encrypted sensor data (mocked temperature, humidity, pH).
* **Receiver**: listens for incoming encrypted payloads, decrypts, and prints the plaintext.

## Notes

* The transmitter retries sending any unsent payloads from a backup log.
* Both transmitter and receiver share the same AES key file for encryption/decryption.
* Ensure LoRa hardware is connected and configured properly.

## License

MIT License

---
