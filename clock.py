#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
import datetime
import requests
from hanover_flipdot_py3 import HanoverFlipDot  # Import from your main library

# Constants for FlipDot display
DISPLAY_COLUMNS = 84
DISPLAY_ROWS = 8
UART_PORT = "/dev/cu.usbserial-BG00Q8VA"  # Hardcoded port
DISPLAY_ADDR = 2  # Address of the display

# Coordinates for Bristol, UK
LATITUDE = 51.4545
LONGITUDE = -2.5879

# API call frequency - Open-Meteo has no limits
DAYTIME_UPDATE_INTERVAL = 1 * 60  # Update every 1 minute during day
NIGHTTIME_UPDATE_INTERVAL = 5 * 60  # Update every 5 minutes during night
DAYTIME_START_HOUR = 8  # 8 AM
DAYTIME_END_HOUR = 20  # 8 PM

# Global state variables
last_weather_update = 0
last_minute = -1
weather_temp = None
weather_condition = None
weather_code = None
weather_error = None


# Weather pictogram patterns
def draw_pictogram(display, x_offset, code):
    """Draw weather pictogram based on WMO code"""
    # Reset this part of display
    for y in range(DISPLAY_ROWS):
        for x in range(x_offset, x_offset + 10):
            if x < DISPLAY_COLUMNS:
                display.set_dot(x, y, False)

    # Clear skies (codes 0, 1)
    if code in [0, 1]:
        # Sun symbol
        # Center dot
        display.set_dot(x_offset + 4, 3, True)
        # Circle around center
        for x, y in [(3, 2), (5, 2), (3, 4), (5, 4), (2, 3), (6, 3)]:
            display.set_dot(x_offset + x, y, True)
        # Rays
        for x, y in [(4, 0), (4, 6), (1, 3), (7, 3), (2, 1), (6, 1), (2, 5), (6, 5)]:
            display.set_dot(x_offset + x, y, True)

    # Cloudy (codes 2, 3)
    elif code in [2, 3]:
        # Cloud shape
        for x, y in [(3, 2), (4, 2), (5, 2), (2, 3), (6, 3), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4)]:
            display.set_dot(x_offset + x, y, True)

    # Rain (codes 51-82 range for rain/showers)
    elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        # Cloud on top
        for x, y in [(3, 1), (4, 1), (5, 1), (2, 2), (6, 2), (2, 3), (3, 3), (4, 3), (5, 3), (6, 3)]:
            display.set_dot(x_offset + x, y, True)
        # Rain drops
        for x, y in [(3, 4), (5, 5), (2, 6), (4, 6), (6, 6)]:
            display.set_dot(x_offset + x, y, True)

    # Snow (codes for snow 71-77, 85-86)
    elif code in [71, 73, 75, 77, 85, 86]:
        # Snowflake
        for x, y in [(4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (2, 2), (6, 2), (3, 3), (5, 3), (2, 4), (6, 4),
                     (3, 5), (5, 5)]:
            display.set_dot(x_offset + x, y, True)

    # Thunderstorm (codes 95-99)
    elif code in [95, 96, 99]:
        # Lightning bolt
        for x, y in [(4, 1), (5, 2), (4, 3), (3, 4), (2, 5), (3, 6)]:
            display.set_dot(x_offset + x, y, True)

    # Fog (codes 45, 48)
    elif code in [45, 48]:
        # Fog lines
        for y in [2, 4, 6]:
            for x in range(x_offset + 2, x_offset + 8):
                display.set_dot(x, y, True)


def draw_digit(display, digit, x_offset):
    """Draw a large 8-pixel tall digit"""
    patterns = {
        '0': [
            [1, 1, 1, 1],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [1, 1, 1, 1]
        ],
        '1': [
            [0, 0, 1, 0],
            [0, 1, 1, 0],
            [1, 0, 1, 0],
            [0, 0, 1, 0],
            [0, 0, 1, 0],
            [0, 0, 1, 0],
            [0, 0, 1, 0],
            [1, 1, 1, 1]
        ],
        '2': [
            [1, 1, 1, 1],
            [0, 0, 0, 1],
            [0, 0, 0, 1],
            [1, 1, 1, 1],
            [1, 0, 0, 0],
            [1, 0, 0, 0],
            [1, 0, 0, 0],
            [1, 1, 1, 1]
        ],
        '3': [
            [1, 1, 1, 1],
            [0, 0, 0, 1],
            [0, 0, 0, 1],
            [1, 1, 1, 1],
            [0, 0, 0, 1],
            [0, 0, 0, 1],
            [0, 0, 0, 1],
            [1, 1, 1, 1]
        ],
        '4': [
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [1, 1, 1, 1],
            [0, 0, 0, 1],
            [0, 0, 0, 1],
            [0, 0, 0, 1],
            [0, 0, 0, 1]
        ],
        '5': [
            [1, 1, 1, 1],
            [1, 0, 0, 0],
            [1, 0, 0, 0],
            [1, 1, 1, 1],
            [0, 0, 0, 1],
            [0, 0, 0, 1],
            [0, 0, 0, 1],
            [1, 1, 1, 1]
        ],
        '6': [
            [1, 1, 1, 1],
            [1, 0, 0, 0],
            [1, 0, 0, 0],
            [1, 1, 1, 1],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [1, 1, 1, 1]
        ],
        '7': [
            [1, 1, 1, 1],
            [0, 0, 0, 1],
            [0, 0, 0, 1],
            [0, 0, 0, 1],
            [0, 0, 0, 1],
            [0, 0, 0, 1],
            [0, 0, 0, 1],
            [0, 0, 0, 1]
        ],
        '8': [
            [1, 1, 1, 1],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [1, 1, 1, 1],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [1, 1, 1, 1]
        ],
        '9': [
            [1, 1, 1, 1],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [1, 1, 1, 1],
            [0, 0, 0, 1],
            [0, 0, 0, 1],
            [0, 0, 0, 1],
            [1, 1, 1, 1]
        ],
        ':': [
            [0, 0, 0, 0],
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0]
        ]
    }

    if digit in patterns:
        pattern = patterns[digit]
        for y in range(8):
            for x in range(4):
                if pattern[y][x]:
                    display.set_dot(x_offset + x, y, True)


def draw_clock(display, time_str):
    """Draw large clock using direct pixel plotting"""
    # Clock starts at left side of display (x=2)
    x_pos = 2

    for char in time_str:
        draw_digit(display, char, x_pos)
        x_pos += 5  # Each digit is 4 pixels wide + 1 pixel space


def draw_temperature(display, temp):
    """Draw temperature in the middle part of display using manual character drawing"""
    temp_str = f"{temp}C"

    # Simple 5x7 font for temperature (same as in write_text but without erase_all)
    font = {
        '0': [0x3E, 0x51, 0x49, 0x45, 0x3E],
        '1': [0x00, 0x42, 0x7F, 0x40, 0x00],
        '2': [0x42, 0x61, 0x51, 0x49, 0x46],
        '3': [0x21, 0x41, 0x45, 0x4B, 0x31],
        '4': [0x18, 0x14, 0x12, 0x7F, 0x10],
        '5': [0x27, 0x45, 0x45, 0x45, 0x39],
        '6': [0x3C, 0x4A, 0x49, 0x49, 0x30],
        '7': [0x01, 0x71, 0x09, 0x05, 0x03],
        '8': [0x36, 0x49, 0x49, 0x49, 0x36],
        '9': [0x06, 0x49, 0x49, 0x29, 0x1E],
        'C': [0x3E, 0x41, 0x41, 0x41, 0x22],
        '-': [0x08, 0x08, 0x08, 0x08, 0x08],
        ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
    }

    # Starting position for temperature (middle-right area)
    start_col = 45
    current_col = start_col

    # First clear the temperature area only (not the whole display)
    for y in range(7):  # 7 rows for font height
        for x in range(len(temp_str) * 6):  # 6 pixels per character (5 + 1 space)
            if start_col + x < display.columns:
                display.set_dot(start_col + x, y, False)

    # Draw each character
    current_col = start_col
    for char in temp_str:
        if char in font:
            char_pattern = font[char]
            for i, pattern in enumerate(char_pattern):
                if current_col < display.columns:
                    # Draw this column of the character
                    for row_idx in range(7):  # 7 rows in font
                        if pattern & (1 << row_idx):
                            display.set_dot(current_col, row_idx, True)
                current_col += 1
            # Add space between characters
            current_col += 1
        else:
            # Skip unknown characters
            current_col += 6


def get_update_interval():
    """Determine the appropriate update interval based on time of day"""
    current_hour = datetime.datetime.now().hour

    # Check if we're in daytime hours
    if DAYTIME_START_HOUR <= current_hour < DAYTIME_END_HOUR:
        return DAYTIME_UPDATE_INTERVAL
    else:
        return NIGHTTIME_UPDATE_INTERVAL


def get_weather():
    """Fetch weather data for Bristol, UK using Open-Meteo API (free, no key required)"""
    global weather_temp, weather_condition, weather_code, weather_error

    try:
        # API call to Open-Meteo - completely free, no API key needed
        url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&current=temperature_2m,weather_code&forecast_days=1"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # Extract current temperature and weather code
            temp = round(data['current']['temperature_2m'])  # Round to nearest degree
            code = data['current']['weather_code']

            # Convert weather code to readable text
            condition = get_weather_condition_text(code)

            weather_temp = temp
            weather_condition = condition
            weather_code = code
            weather_error = None
            print(f"Weather updated: {temp}°C, {condition} (code: {code})")
            return True
        else:
            weather_error = "API Err"
            print(f"API Error: {response.status_code}")
            return False

    except Exception as e:
        weather_error = "Conn Err"
        print(f"Weather error: {e}")
        return False


def get_weather_condition_text(wmo_code):
    """Convert WMO weather code to readable text"""
    # WMO Weather interpretation codes
    wmo_codes = {
        0: "Clear",
        1: "Clear",
        2: "Fair",
        3: "Cloudy",
        45: "Fog",
        48: "Fog",
        51: "Drizzle",
        53: "Drizzle",
        55: "Drizzle",
        56: "Frz Drzl",
        57: "Frz Drzl",
        61: "Rain",
        63: "Rain",
        65: "Rain",
        66: "Frz Rain",
        67: "Frz Rain",
        71: "Snow",
        73: "Snow",
        75: "Snow",
        77: "Snow",
        80: "Showers",
        81: "Showers",
        82: "Showers",
        85: "Snow Shr",
        86: "Snow Shr",
        95: "Storm",
        96: "Storm",
        99: "Storm"
    }

    return wmo_codes.get(wmo_code, "Unknown")


def update_display(display):
    """Update the flip dot display with clock and weather"""
    global last_minute, last_weather_update

    # Get current time
    now = datetime.datetime.now()
    time_str = now.strftime("%H:%M")  # 24-hour format

    # Check if we need to update the weather
    current_time = time.time()
    update_interval = get_update_interval()

    if current_time - last_weather_update > update_interval:
        get_weather()
        last_weather_update = current_time

    # Only update display if minute has changed (to reduce flicker)
    if now.minute != last_minute:
        last_minute = now.minute

        # Clear display
        display.erase_all()

        # Draw clock using large 8-pixel digits
        draw_clock(display, time_str)

        # Draw temperature if available
        if weather_temp is not None:
            draw_temperature(display, weather_temp)

        # Draw weather pictogram if we have a weather code
        if weather_code is not None:
            draw_pictogram(display, 65, weather_code)

        # Send to display
        display.send()

        print(f"Display updated with time={time_str}, temp={weather_temp}°C, weather code={weather_code}")


def main():
    """Main program - run the clock and weather display"""
    print("FlipDot Clock and Weather Display")
    print(f"Display size: {DISPLAY_COLUMNS}x{DISPLAY_ROWS}")

    try:
        # Initialize the display
        display = HanoverFlipDot(
            UART_PORT,
            address=DISPLAY_ADDR,
            columns=DISPLAY_COLUMNS,
            rows=DISPLAY_ROWS,
            flip_orientation=False,
            debug=True
        )

        # Test - show each element separately
        print("Testing display components...")

        # Test 1: Large clock digits
        display.erase_all()
        draw_clock(display, "12:34")
        display.send()
        print("Testing large clock digits - 12:34")
        time.sleep(2)

        # Test 2: Temperature
        display.erase_all()
        draw_temperature(display, 15)
        display.send()
        print("Testing temperature - 15°C")
        time.sleep(2)

        # Test 3: Weather pictograms
        display.erase_all()
        # Test each pictogram type
        x = 5
        for code in [0, 3, 61, 71, 95, 45]:
            draw_pictogram(display, x, code)
            x += 12
        display.send()
        print("Testing weather pictograms")
        time.sleep(2)

        # Test 4: Full layout
        display.erase_all()
        draw_clock(display, "12:34")
        draw_temperature(display, 15)
        draw_pictogram(display, 65, 0)  # Clear sky
        display.send()
        print("Testing full layout")
        time.sleep(2)

        # Initial weather fetch
        print("Fetching initial weather data...")
        get_weather()
        last_weather_update = time.time()

        # Main loop
        print("Starting main display loop...")
        while True:
            update_display(display)

            # Sleep until next minute to save resources
            now = datetime.datetime.now()
            seconds_to_next_minute = 60 - now.second
            time.sleep(max(0.5, seconds_to_next_minute - 0.5))

    except KeyboardInterrupt:
        print("\nExiting...")
        # Clear display before exit
        display.erase_all()
        display.send()
    except Exception as e:
        print(f"Error: {e}")
        # More detailed error info
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()