# HeatSync

A Raspberry Pi–based smart thermostat built with Kivy, using a DHT22 sensor for temperature & humidity readings and an I²C Relay HAT for heating/cooling control, displayed on a **3.5" 480×320 SPI touch screen**.

---

## Features

- **Real-time sensor display**: Shows current temperature and humidity.  
- **Automatic control**: Maintains a user-defined threshold with hysteresis to prevent relay chatter.  
- **Manual override**: Toggle fan and heater independently via buttons.  
- **Unit switching**: Convert between °C and °F on the fly.  
- **Date & time display**: Central Time Zone clock updates every second.  
- **Touchscreen interface**: All controls optimized for touch on a 3.5" display.  
- **Package structure**: Clear separation of sensor I/O, control logic, and GUI code.  
- **Logging**: All events and errors logged to `thermostat.log`.  

---

## Hardware & Display

- **Touchscreen**: [3.5 Inch 480×320 Touch Screen TFT LCD SPI Display Panel for Raspberry Pi A, B, A+, B+, 2B, 3B, 3B+, 4B, 5](https://shorturl.at/nfYJy)

---

## Detailed Resources

- **[Dropbox Folder with Resources:**](https://www.dropbox.com/scl/fo/hawpkmswazw5h7lv2p8vq/AExEUzKjs65iyBGKfmCeguk?rlkey=ev89s381ag053wue395hf4ueb&e=2&dl=0)
- [**Detailed Video Instructions for connecting Display:**](https://tinyurl.com/y9t89cs7)

---

## Setup Steps

1. **Format SD Card** : 
   [Download and run SD Card Formatter:](https://www.dropbox.com/scl/fo/hawpkmswazw5h7lv2p8vq/AGF_GZM-M6wJNhGVEjaxVv8/Software/SDFormatter?rlkey=ev89s381ag053wue395hf4ueb&subfolder_nav_tracking=1&st=a152d77x&dl=0)

3. **Write OS Image**: 
   [Download Win32DiskImager and write Raspberry Pi OS:](https://www.dropbox.com/scl/fo/hawpkmswazw5h7lv2p8vq/ACrkQeP2K4o2hN08QMK_YqQ/Software/Win32DiskImager?dl=0&rlkey=ev89s381ag053wue395hf4ueb)

   OR,[Download OS image:](https://www.dropbox.com/scl/fo/hawpkmswazw5h7lv2p8vq/AITdah50XhdL0PkGOfw8Gz4/Image?dl=0&preview=MPI3501-3.5inch--2023-12-05-raspios-bookworm-armhf.7z&rlkey=ev89s381ag053wue395hf4ueb)

4. **Enable SSH**  
   - Create an empty file named `ssh` (no extension) on the boot partition of the SD card.

5. **Hardware Setup**  
   - Insert the SD card into the Raspberry Pi.  
   - Connect the 3.5" touch display via the SPI header.  
   - Power on the Pi.

6. **Network & SSH**  
   ```bash
   # On Pi, find IP address:
   ifconfig
   ```
   - Connect using PuTTY or your SSH client (port 22).  
   - Login as `pi`, then change the default password when prompted.

---

## Development Environment

1. **Create Virtual Environment**  
   ```bash
   sudo apt-get update
   sudo apt-get install python3-venv
   mkdir ~/my_project && cd ~/my_project
   python3 -m venv env
   source env/bin/activate
   ```

2. **Install Dependencies**  
   ```bash
   pip install adafruit-blinka adafruit-circuitpython-dht kivy smbus2 pytz
   pip install pyqt5 Adafruit_DHT RPi.GPIO

   # If PyQt5 errors:
   sudo apt-get install qt5-qmake qtbase5-dev build-essential libgl1-mesa-dev
   ```

3. **Run the Application**  
   ```bash
   python main.py
   ```

---

## Project Structure

```plaintext
your_project/
├── thermostat/
│   ├── __init__.py
│   ├── sensors.py
│   ├── control_logic.py
│   └── GUI.py
└── main.py
```

---

## Requirements

- **Python** 3.7+  
- **Kivy**  
- **adafruit-circuitpython-dht**  
- **smbus2**  
- **pytz**  

Install via:  
```bash
pip install kivy adafruit-circuitpython-dht smbus2 pytz
```

---

## Usage

```bash
git clone <repo-url>
cd your_project
source env/bin/activate  # if using venv (recommended for external libraries)
python main.py
```

- **Touchscreen controls**:  
  - Slide threshold.  
  - Toggle Automatic/Manual.  
  - Manually toggle Fan/Heater.  
  - Switch °C/°F.

---

## Customization

- **Threshold & Hysteresis**: `thermostat/control_logic.py`  
- **I²C Addresses/Channels**: `thermostat/sensors.py`  
- **Display Settings**: `thermostat/GUI.py` or override in `main.py`

---

## License

MIT License
