import logging

class ThermostatLogic:
    """Encapsulates threshold, hysteresis, unit conversion, and on/off logic."""

    def __init__(self, sensor_mgr):
        self.sensor = sensor_mgr

        # Default threshold + hysteresis
        self.threshold_celsius = 25.0
        self.hysteresis = 0.5

        # Track unit for GUI slider/display
        self.temperature_unit = 'C'  # 'C' or 'F'

    def celsius_to_fahrenheit(self, c):
        return c * 9/5 + 32

    def fahrenheit_to_celsius(self, f):
        return (f - 32) * 5/9

    def set_threshold_from_slider(self, slider_value):
        """Called by GUI when slider moves."""
        if self.temperature_unit == 'C':
            self.threshold_celsius = slider_value
        else:
            self.threshold_celsius = self.fahrenheit_to_celsius(slider_value)
        logging.info("Threshold updated to %.2f°C", self.threshold_celsius)

    def evaluate(self):
        """Read sensors, apply hysteresis, return one of 'cool','heat','idle'."""
        temp_c, hum = self.sensor.read_temp_humidity()
        upper = self.threshold_celsius + self.hysteresis
        lower = self.threshold_celsius - self.hysteresis

        if temp_c > upper:
            return 'cool', temp_c, hum
        elif temp_c < lower:
            return 'heat', temp_c, hum
        else:
            return 'idle', temp_c, hum

    def apply(self, mode):
        """Send commands out to relays based on the evaluation."""
        if mode == 'cool':
            self.sensor.set_fan(True)
            self.sensor.set_heater(False)
        elif mode == 'heat':
            self.sensor.set_heater(True)
            self.sensor.set_fan(False)
        else:  # idle
            self.sensor.set_fan(False)
            self.sensor.set_heater(False)
