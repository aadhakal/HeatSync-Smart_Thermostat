# -*- coding: utf-8 -*-
from kivy.config import Config
Config.set('graphics', 'width', '480')  # Set width to 480 pixels
Config.set('graphics', 'height', '320')  # Set height to 320 pixels
Config.set('graphics', 'resizable', False)  # Prevent window resizing
Config.set('graphics', 'borderless', False)
Config.set('graphics', 'fullscreen', 'auto')
Config.set('kivy', 'exit_on_escape', '0')  # Disable exit on escape key

import board
import adafruit_dht
import smbus2
import time as t
import sys
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from datetime import datetime
import logging
import pytz  # Import pytz for timezone handling

# Setup logging
logging.basicConfig(
    filename='thermostat.log',  # Logs will be saved to this file
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class ThermostatGUI(BoxLayout):
    # Define properties for dynamic updates
    current_temperature = NumericProperty(0.0)
    current_humidity = NumericProperty(0.0)
    threshold_celsius = NumericProperty(25.0)  # Internal threshold in Celsius
    system_status = StringProperty("Idle")
    fan_status = StringProperty("Fan: OFF")
    heater_status = StringProperty("Heater: OFF")
    temperature_unit = StringProperty("C")  # 'C' for Celsius, 'F' for Fahrenheit
    simulation_mode = BooleanProperty(False)  # Set to False when controlling hardware

    def __init__(self, **kwargs):
        super(ThermostatGUI, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)
        
        # Flag to prevent callback during unit toggle
        self.unit_toggle_in_progress = False

        # Define Central Time Zone
        self.central_tz = pytz.timezone('US/Central')

        # Print if in simulation mode
        if self.simulation_mode:
            logging.info("Running in Simulation Mode")
        else:
            logging.info("Running in Hardware Control Mode")

        # Sensor setup
        try:
            self.dhtDevice = adafruit_dht.DHT22(board.D4, use_pulseio=False)
            logging.info("DHT22 sensor initialized on GPIO4.")
        except Exception as e:
            logging.error(f"Failed to initialize DHT22 sensor: {e}")
            self.dhtDevice = None

        # Initialize SMBus for relay control
        self.DEVICE_BUS = 1  # Typically 1 for Raspberry Pi
        self.DEVICE_ADDR = 0x10  # Relay HAT's I2C address as per manufacturer
        try:
            self.bus = smbus2.SMBus(self.DEVICE_BUS)
            logging.info(f"SMBus initialized on bus {self.DEVICE_BUS} with address {hex(self.DEVICE_ADDR)}")
        except Exception as e:
            logging.error(f"Failed to initialize SMBus: {e}")
            self.bus = None

        # Define Relay Channels
        self.FAN_CHANNEL = 1    # Relay Channel 1 corresponds to the fan
        self.HEATER_CHANNEL = 4 # Relay Channel 4 corresponds to the heater

        # Window size (480x320)
        Window.size = (480, 320)
        Window.clearcolor = (1, 1, 1, 1)  # White background

        # Build the GUI
        self.build_gui()

        # Schedule the sensor reading to update every 2 seconds
        Clock.schedule_interval(self.update_sensor_readings, 2)

        # Schedule date and time update every second
        Clock.schedule_interval(self.update_date_time, 1)
        
    def build_gui(self):
        # Create a fixed-size AnchorLayout to hold the main layout
        anchor_layout = AnchorLayout(anchor_x='center', anchor_y='center')

        # Create a BoxLayout inside the AnchorLayout to keep content centered and fixed
        main_layout = BoxLayout(orientation='vertical', padding=dp(5), spacing=dp(5), size_hint=(1, None))
        main_layout.height = 320  # Set the height to match the display to avoid extra scrolling

        # Adjust font sizes for small display
        label_font_size = dp(18)
        button_font_size = dp(18)

        # Current Temperature Label
        self.current_temp_label = Label(
            text="Current Temperature: -- \u00b0C",
            font_size=label_font_size,
            color=(0, 0, 1, 1),  # Blue text
            size_hint=(1, None),
            height=dp(30)
        )
        main_layout.add_widget(self.current_temp_label)

        # Current Humidity Label
        self.current_humidity_label = Label(
            text="Humidity: -- %",
            font_size=label_font_size,
            color=(0, 0.5, 0, 1),  # Dark green text
            size_hint=(1, None),
            height=dp(30)
        )
        main_layout.add_widget(self.current_humidity_label)

        # Horizontal BoxLayout for "Switch to °F" button and Date & Time label
        switch_datetime_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(40),
            padding=[dp(10), 0, dp(10), 0]
        )

        # Temperature Unit Toggle (Regular Button)
        self.unit_toggle = Button(
            text='Switch to \u00b0F',
            font_size=button_font_size,
            size_hint=(0.4, 1)  # Allocate 40% width
        )
        self.unit_toggle.bind(on_press=self.toggle_temperature_unit)
        switch_datetime_layout.add_widget(self.unit_toggle)

        # Date and Time Label
        self.datetime_label = Label(
            text=self.get_current_datetime(),
            font_size=label_font_size,
            color=(0, 0, 0, 1),  # Black text for visibility
            halign='right',
            valign='middle',
            text_size=(Window.width * 0.6 - dp(20), None),  # Adjust text size to fit
            size_hint=(0.6, 1)
        )
        switch_datetime_layout.add_widget(self.datetime_label)

        main_layout.add_widget(switch_datetime_layout)

        # Temperature Threshold Slider and Label
        temp_control_layout = BoxLayout(orientation='vertical', size_hint=(1, None), spacing=dp(5), height=dp(80))

        # Label for Slider Value
        if self.temperature_unit == 'C':
            slider_label_text = f"Threshold: {self.threshold_celsius:.1f} \u00b0C"
            slider_min = 10
            slider_max = 40
            slider_value = self.threshold_celsius
        else:
            slider_label_text = f"Threshold: {self.celsius_to_fahrenheit(self.threshold_celsius):.1f} \u00b0F"
            slider_min = 50
            slider_max = 104
            slider_value = self.celsius_to_fahrenheit(self.threshold_celsius)

        self.slider_value_label = Label(
            text=slider_label_text,
            font_size=button_font_size,
            color=(0, 0, 0, 1),  # Black text color for visibility
            size_hint=(1, None),
            height=dp(30)
        )
        temp_control_layout.add_widget(self.slider_value_label)

        # Temperature Threshold Slider
        self.temp_slider = Slider(
            min=slider_min,
            max=slider_max,
            value=slider_value,
            step=0.5,
            size_hint=(1, None),
            height=dp(25)
        )
        self.temp_slider.bind(value=self.on_temp_slider_value_change)
        temp_control_layout.add_widget(self.temp_slider)

        main_layout.add_widget(temp_control_layout)

        # Fan Control Button (for manual mode using SMBus)
        manual_control_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(40))
        self.manual_fan_button = Button(
            text="Fan: OFF",
            font_size=button_font_size,
            size_hint=(0.5, 1)
        )
        self.manual_fan_button.bind(on_press=self.toggle_fan)
        self.manual_fan_button.disabled = True  # Disabled by default (Automatic Mode)
        manual_control_layout.add_widget(self.manual_fan_button)

        self.manual_heater_button = Button(
            text="Heater: OFF",
            font_size=button_font_size,
            size_hint=(0.5, 1)
        )
        self.manual_heater_button.bind(on_press=self.toggle_heater)
        self.manual_heater_button.disabled = True  # Disabled by default (Automatic Mode)
        manual_control_layout.add_widget(self.manual_heater_button)
        main_layout.add_widget(manual_control_layout)

        # Mode Selector
        mode_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(40))
        self.mode_label = Label(
            text="Mode:",
            font_size=label_font_size,
            size_hint=(0.3, 1)
        )
        mode_layout.add_widget(self.mode_label)

        self.mode_selector = Spinner(
            text='Automatic',
            values=['Automatic', 'Manual'],
            font_size=button_font_size,
            size_hint=(0.7, 1)
        )
        self.mode_selector.bind(text=self.on_mode_change)
        mode_layout.add_widget(self.mode_selector)
        main_layout.add_widget(mode_layout)

        # System Status Label
        self.status_label = Label(
            text="System Status: Idle",
            font_size=label_font_size,
            color=(1, 0.5, 0, 1),  # Orange text
            size_hint=(1, None),
            height=dp(30)
        )
        main_layout.add_widget(self.status_label)

        # Add main_layout to anchor_layout to keep it centered and fixed
        anchor_layout.add_widget(main_layout)
        self.add_widget(anchor_layout)

    def get_current_datetime(self):
        now_utc = datetime.utcnow()
        now_central = pytz.utc.localize(now_utc).astimezone(self.central_tz)
        return now_central.strftime("Date: %d/%m/%Y\nTime: %H:%M:%S")

    def update_date_time(self, dt):
        self.datetime_label.text = self.get_current_datetime()

    def on_temp_slider_value_change(self, instance, value):
        if self.unit_toggle_in_progress:
            return  # Do not update during unit toggle

        # Update the internal threshold based on the current unit
        if self.temperature_unit == 'F':
            self.threshold_celsius = self.fahrenheit_to_celsius(value)
            self.slider_value_label.text = f"Threshold: {value:.1f} \u00b0F"
        else:
            self.threshold_celsius = value
            self.slider_value_label.text = f"Threshold: {value:.1f} \u00b0C"
        
        logging.info(f"Slider value changed to {value:.1f} \u00b0{self.temperature_unit}")

        # Implement Debouncing: Schedule a delayed check
        Clock.unschedule(self.delayed_check)
        Clock.schedule_once(self.delayed_check, 0.5)  # 0.5-second delay

    def delayed_check(self, dt):
        logging.info("Delayed check initiated.")
        self.check_system_status(self.current_temperature)

    def toggle_temperature_unit(self, instance):
        if self.unit_toggle_in_progress:
            return  # Prevent re-entrancy

        self.unit_toggle_in_progress = True  # Start unit toggle process

        if self.temperature_unit == 'C':
            # Switch to Fahrenheit
            self.temperature_unit = 'F'
            instance.text = 'Switch to \u00b0C'

            # Convert internal threshold to Fahrenheit for display
            threshold_f = self.celsius_to_fahrenheit(self.threshold_celsius)

            # Update slider properties
            self.temp_slider.min = 50
            self.temp_slider.max = 104
            self.temp_slider.value = threshold_f

            self.slider_value_label.text = f"Threshold: {threshold_f:.1f} \u00b0F"
            logging.info(f"Threshold set to {threshold_f:.1f} \u00b0F")
        else:
            # Switch to Celsius
            self.temperature_unit = 'C'
            instance.text = 'Switch to \u00b0F'

            # Convert internal threshold to Celsius for display
            threshold_c = self.threshold_celsius  # Already in Celsius

            # Update slider properties
            self.temp_slider.min = 10
            self.temp_slider.max = 40
            self.temp_slider.value = threshold_c

            self.slider_value_label.text = f"Threshold: {threshold_c:.1f} \u00b0C"
            logging.info(f"Threshold set to {threshold_c:.1f} \u00b0C")

        self.unit_toggle_in_progress = False  # End unit toggle process

    def on_mode_change(self, spinner, text):
        if text == 'Manual':
            # Enable manual controls (fan and heater buttons)
            self.manual_fan_button.disabled = False
            self.manual_heater_button.disabled = False
            self.status_label.text = "System Status: Manual Control"
            self.status_label.color = (0.5, 0, 0.5, 1)  # Purple
            logging.info("Switched to Manual Mode")
        else:
            # Disable manual controls
            self.manual_fan_button.disabled = True
            self.manual_heater_button.disabled = True
            self.status_label.text = "System Status: Idle"
            self.status_label.color = (1, 0.5, 0, 1)  # Orange
            logging.info("Switched to Automatic Mode")
            # Ensure heaters and fans are controlled automatically
            self.check_system_status(self.current_temperature)

    def toggle_fan(self, instance):
        if self.fan_status == "Fan: OFF":
            self.turn_fan_on()
        else:
            self.turn_fan_off()

    def toggle_heater(self, instance):
        if self.heater_status == "Heater: OFF":
            self.turn_heater_on()
        else:
            self.turn_heater_off()

    def turn_fan_on(self):
        if self.bus and self.FAN_CHANNEL:
            try:
                self.bus.write_byte_data(self.DEVICE_ADDR, self.FAN_CHANNEL, 0xFF)
                logging.info("Fan turned ON via SMBus.")
                self.fan_status = "Fan: ON"
                self.manual_fan_button.text = "Fan: ON"
                self.manual_fan_button.background_color = (0, 1, 0, 1)  # Green
            except Exception as e:
                logging.error(f"Error turning fan ON: {e}")
        else:
            logging.warning("SMBus not initialized or FAN_CHANNEL not set. Cannot turn fan ON.")

    def turn_fan_off(self):
        if self.bus and self.FAN_CHANNEL:
            try:
                self.bus.write_byte_data(self.DEVICE_ADDR, self.FAN_CHANNEL, 0x00)
                logging.info("Fan turned OFF via SMBus.")
                self.fan_status = "Fan: OFF"
                self.manual_fan_button.text = "Fan: OFF"
                self.manual_fan_button.background_color = (1, 1, 1, 1)  # Reset to default
            except Exception as e:
                logging.error(f"Error turning fan OFF: {e}")
        else:
            logging.warning("SMBus not initialized or FAN_CHANNEL not set. Cannot turn fan OFF.")

    def turn_heater_on(self):
        if self.bus and self.HEATER_CHANNEL:
            try:
                self.bus.write_byte_data(self.DEVICE_ADDR, self.HEATER_CHANNEL, 0xFF)
                logging.info("Heater turned ON via SMBus.")
                self.heater_status = "Heater: ON"
                self.manual_heater_button.text = "Heater: ON"
                self.manual_heater_button.background_color = (1, 0, 0, 1)  # Red
            except Exception as e:
                logging.error(f"Error turning heater ON: {e}")
        else:
            logging.warning("SMBus not initialized or HEATER_CHANNEL not set. Cannot turn heater ON.")

    def turn_heater_off(self):
        if self.bus and self.HEATER_CHANNEL:
            try:
                self.bus.write_byte_data(self.DEVICE_ADDR, self.HEATER_CHANNEL, 0x00)
                logging.info("Heater turned OFF via SMBus.")
                self.heater_status = "Heater: OFF"
                self.manual_heater_button.text = "Heater: OFF"
                self.manual_heater_button.background_color = (1, 1, 1, 1)  # Reset to default
            except Exception as e:
                logging.error(f"Error turning heater OFF: {e}")
        else:
            logging.warning("SMBus not initialized or HEATER_CHANNEL not set. Cannot turn heater OFF.")

    def celsius_to_fahrenheit(self, celsius):
        return celsius * 9 / 5 + 32

    def fahrenheit_to_celsius(self, fahrenheit):
        return (fahrenheit - 32) * 5 / 9

    def update_sensor_readings(self, dt):
        if not self.dhtDevice:
            self.current_temp_label.text = "Sensor Not Initialized!"
            self.current_humidity_label.text = "Sensor Not Initialized!"
            logging.error("DHT22 sensor not initialized.")
            return

        try:
            temperature_c = self.dhtDevice.temperature
            humidity = self.dhtDevice.humidity

            if temperature_c is not None and humidity is not None:
                if self.temperature_unit == 'C':
                    display_temp = f"{temperature_c:.1f} \u00b0C"
                    current_temp = temperature_c
                else:
                    temperature_f = self.celsius_to_fahrenheit(temperature_c)
                    display_temp = f"{temperature_f:.1f} \u00b0F"
                    current_temp = temperature_f

                self.current_temperature = current_temp
                self.current_temp_label.text = f"Current Temperature: {display_temp}"
                self.current_humidity_label.text = f"Humidity: {humidity:.1f} %"

                logging.info(f"Temperature: {display_temp}, Humidity: {humidity:.1f} %")

                if self.mode_selector.text == 'Automatic':
                    self.check_system_status(current_temp)
            else:
                self.current_temp_label.text = "Sensor Error!"
                self.current_humidity_label.text = "Sensor Error!"
                logging.warning("Sensor returned None values.")
        except RuntimeError as error:
            # Handle common sensor reading errors
            self.current_temp_label.text = "Reading Error!"
            self.current_humidity_label.text = "Reading Error!"
            logging.error(f"Runtime Error: {error}")
            Clock.schedule_once(self.update_sensor_readings, 5)
        except Exception as error:
            self.dhtDevice.exit()
            logging.critical(f"Unhandled Exception: {error}")
            raise error

    def check_system_status(self, current_temp):
        if self.temperature_unit == 'C':
            threshold = self.threshold_celsius
            current = current_temp
        else:
            threshold = self.threshold_celsius
            current = self.fahrenheit_to_celsius(current_temp)

        logging.info(f"Checking system status with current_temp={current:.1f}C and threshold={threshold:.1f}C")

        hysteresis = 0.5  # Degrees Celsius

        if current > (threshold + hysteresis):
            logging.info("Temperature above threshold + hysteresis. Initiating cooling.")
            self.update_system_state(cooling=True)
        elif current < (threshold - hysteresis):
            logging.info("Temperature below threshold - hysteresis. Initiating heating.")
            self.update_system_state(heating=True)
        else:
            logging.info("Temperature within hysteresis band. System idle.")
            self.update_system_state(idle=True)

    def update_system_state(self, cooling=False, heating=False, idle=False):
        if cooling:
            self.fan_status = "Fan: ON"
            self.system_status = "System Status: Cooling"
            self.status_label.color = (0, 0, 1, 1)  # Blue
            if self.bus and self.FAN_CHANNEL:
                try:
                    self.bus.write_byte_data(self.DEVICE_ADDR, self.FAN_CHANNEL, 0xFF)
                    logging.info("Fan activated for cooling.")
                except Exception as e:
                    logging.error(f"Error in cooling state: {e}")
            else:
                logging.warning("Cannot activate Fan.")
            self.turn_heater_off()

        elif heating:
            self.heater_status = "Heater: ON"
            self.system_status = "System Status: Heating"
            self.status_label.color = (1, 0, 0, 1)  # Red
            if self.bus and self.HEATER_CHANNEL:
                try:
                    self.bus.write_byte_data(self.DEVICE_ADDR, self.HEATER_CHANNEL, 0xFF)
                    logging.info("Heater activated for heating.")
                except Exception as e:
                    logging.error(f"Error in heating state: {e}")
            else:
                logging.warning("Cannot activate Heater.")
            self.turn_fan_off()

        elif idle:
            self.fan_status = "Fan: OFF"
            self.heater_status = "Heater: OFF"
            self.system_status = "System Status: Idle"
            self.status_label.color = (1, 0.5, 0, 1)  # Orange
            if self.bus:
                try:
                    self.bus.write_byte_data(self.DEVICE_ADDR, self.FAN_CHANNEL, 0x00)
                    self.bus.write_byte_data(self.DEVICE_ADDR, self.HEATER_CHANNEL, 0x00)
                    logging.info("Fan and Heater deactivated for idle.")
                except Exception as e:
                    logging.error(f"Error in idle state: {e}")
            else:
                logging.warning("Cannot deactivate devices.")

        self.update_status_labels()

    def update_status_labels(self):
        self.status_label.text = self.system_status

    def on_stop(self):
        # Turn off both fan and heater before exiting
        self.turn_fan_off()
        self.turn_heater_off()

        # Clean up SMBus
        if self.bus:
            self.bus.close()
            logging.info("SMBus closed.")

class ThermostatApp(App):
    def build(self):
        return ThermostatGUI()

    def on_stop(self):
        self.root.on_stop()
