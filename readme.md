# LoRa Encrypted Communication - Overview

This project demonstrates secure wireless communication using LoRa SX126x modules combined with AES-256 encryption. It aims to provide a reliable and confidential data transfer method over long-range radio frequencies.

## Project Overview

- **Secure Transmission**  
  Data is encrypted using AES-256 in CBC mode before being transmitted via LoRa. This ensures confidentiality and prevents eavesdropping.

- **Key Management**  
  The encryption key is securely loaded from an external binary file (`keyfile.bin`), keeping keys separate from the source code.

- **LoRa Configuration**  
  All radio parameters (frequency, spreading factor, bandwidth, coding rate, etc.) are configurable through a `config.ini` file, allowing flexible adaptation to different environments and requirements.

- **Resilience**  
  The transmitter implements a retry mechanism that stores unsent messages in a backup file and attempts to resend them later, increasing reliability.

- **Decryption and Reception**  
  The receiver listens for incoming encrypted payloads, decrypts them, and outputs the original plaintext data.

- **Performance Monitoring**  
  The encryption process is timed to provide insight into processing overhead.

## Use Cases

- Secure IoT sensor data transmission over long distances
- Encrypted telemetry in remote or sensitive environments
- Applications requiring lightweight and secure wireless communication

## Components

- **Transmitter Script**  
  Prepares sensor data, encrypts it, and sends it via LoRa.

- **Receiver Script**  
  Receives encrypted data, decrypts, and processes it.

## Requirements

- Python 3.7+
- `cryptography` library for AES encryption
- `LoRaRF` library for SX126x hardware interface
- LoRa SX126x radio modules connected to the system

---

This project serves as a foundation for building secure, encrypted LoRa networks suitable for various IoT applications.
