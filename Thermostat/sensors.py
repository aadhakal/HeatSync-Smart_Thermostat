import board
import adafruit_dht
import smbus2
import logging

class SensorManager:
    """Initialize and wrap the DHT22 + Relay‐HAT SMBus calls."""

    def __init__(self,
                 dht_pin=board.D4,
                 bus_num=1,
                 device_addr=0x10,
                 fan_channel=1,
                 heater_channel=4):
        # DHT22
        try:
            self.dhtDevice = adafruit_dht.DHT22(dht_pin, use_pulseio=False)
            logging.info("DHT22 sensor initialized on %s", dht_pin)
        except Exception as e:
            logging.error("Failed to initialize DHT22 sensor: %s", e)
            self.dhtDevice = None

        # SMBus for Relay HAT
        try:
            self.bus = smbus2.SMBus(bus_num)
            self.addr = device_addr
            logging.info("SMBus initialized on bus %d addr %s", bus_num, hex(device_addr))
        except Exception as e:
            logging.error("Failed to initialize SMBus: %s", e)
            self.bus = None

        # Relay channels
        self.FAN_CHANNEL = fan_channel
        self.HEATER_CHANNEL = heater_channel

    def read_temp_humidity(self):
        if not self.dhtDevice:
            raise RuntimeError("DHT22 not initialized")
        t = self.dhtDevice.temperature
        h = self.dhtDevice.humidity
        if t is None or h is None:
            raise RuntimeError("Sensor read returned None")
        return t, h

    def set_fan(self, on: bool):
        if not self.bus:
            logging.warning("Cannot set fan: SMBus not initialized")
            return
        val = 0xFF if on else 0x00
        self.bus.write_byte_data(self.addr, self.FAN_CHANNEL, val)
        logging.info("Fan turned %s", "ON" if on else "OFF")

    def set_heater(self, on: bool):
        if not self.bus:
            logging.warning("Cannot set heater: SMBus not initialized")
            return
        val = 0xFF if on else 0x00
        self.bus.write_byte_data(self.addr, self.HEATER_CHANNEL, val)
        logging.info("Heater turned %s", "ON" if on else "OFF")
