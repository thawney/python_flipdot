#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FlipDot Display Library Demo
===========================

This script demonstrates how to use the hanover_flipdot_py3 library.
It covers all the basic features and shows common usage patterns.

Run with: python3 demo.py
Or visually: python3 visual_simulator.py demo.py
"""

import time
import sys
from hanover_flipdot_py3 import HanoverFlipDot

# Display configuration - adjust these for your setup
UART_PORT = "/dev/cu.usbserial-BG00Q8VA"  # Change to your serial port
DISPLAY_ADDRESS = 2  # Change to your display's address
DISPLAY_COLUMNS = 84  # Width of your display
DISPLAY_ROWS = 8  # Height of your display


def demo_basic_setup():
    """Demo 1: Basic setup and connection"""
    print("\n" + "=" * 50)
    print("DEMO 1: Basic Setup and Connection")
    print("=" * 50)

    print("Creating display instance...")
    display = HanoverFlipDot(
        port=UART_PORT,
        address=DISPLAY_ADDRESS,
        columns=DISPLAY_COLUMNS,
        rows=DISPLAY_ROWS,
        flip_orientation=False,  # Set to True if your display is upside down
        debug=True,  # Enable debug output
        speed_factor=1.0  # 1.0 = normal speed, higher = slower, lower = faster
    )

    print("✓ Display connected!")
    print(f"  - Port: {display.port}")
    print(f"  - Address: {display.address}")
    print(f"  - Size: {display.columns}x{display.rows}")
    print(f"  - Orientation: {'Flipped' if display.flip_orientation else 'Normal'}")

    return display


def demo_basic_operations(display):
    """Demo 2: Basic display operations"""
    print("\n" + "=" * 50)
    print("DEMO 2: Basic Display Operations")
    print("=" * 50)

    print("Clearing display...")
    display.erase_all()  # Turn off all dots
    display.send()  # Send to hardware
    time.sleep(1)

    print("Filling display...")
    display.fill_all()  # Turn on all dots
    display.send()
    time.sleep(1)

    print("Clearing again...")
    display.erase_all()
    display.send()
    time.sleep(1)


def demo_individual_dots(display):
    """Demo 3: Individual dot control"""
    print("\n" + "=" * 50)
    print("DEMO 3: Individual Dot Control")
    print("=" * 50)

    display.erase_all()

    print("Drawing individual dots...")
    # Draw a simple pattern
    for x in range(0, display.columns, 4):
        for y in range(0, display.rows, 2):
            display.set_dot(x, y, True)  # Turn on dot at (x, y)

    display.send()
    time.sleep(2)

    print("Drawing a border...")
    display.erase_all()

    # Top and bottom borders
    for x in range(display.columns):
        display.set_dot(x, 0, True)  # Top row
        display.set_dot(x, display.rows - 1, True)  # Bottom row

    # Left and right borders
    for y in range(display.rows):
        display.set_dot(0, y, True)  # Left column
        display.set_dot(display.columns - 1, y, True)  # Right column

    display.send()
    time.sleep(2)


def demo_text_display(display):
    """Demo 4: Text display"""
    print("\n" + "=" * 50)
    print("DEMO 4: Text Display")
    print("=" * 50)

    # Simple text
    print("Displaying 'HELLO WORLD'...")
    display.write_text("HELLO WORLD", col=5, row=0)
    display.send()
    time.sleep(2)

    # Numbers and symbols
    print("Displaying numbers and symbols...")
    display.write_text("123 + 456 = 579", col=2, row=0)
    display.send()
    time.sleep(2)

    # Multiple lines (manual positioning)
    print("Displaying multiple lines...")
    display.erase_all()
    # Note: write_text clears the display, so we need to draw manually for multiple lines

    # We'll use individual character drawing for multiple lines
    display.erase_all()

    # Draw "LINE 1" at top
    for i, char in enumerate("LINE 1"):
        if char == ' ':
            continue
        # This is a simplified approach - in practice you'd use the font data
        # For now, let's just show positioning
        x_pos = 5 + i * 6
        y_pos = 1
        if x_pos < display.columns - 5:
            # Draw a simple pattern for each character position
            for dy in range(5):
                display.set_dot(x_pos, y_pos + dy, True)
                display.set_dot(x_pos + 1, y_pos + dy, True)

    # Draw "LINE 2" at bottom
    for i, char in enumerate("LINE 2"):
        if char == ' ':
            continue
        x_pos = 5 + i * 6
        y_pos = 6
        if x_pos < display.columns - 5:
            for dy in range(2):
                display.set_dot(x_pos, y_pos + dy, True)
                display.set_dot(x_pos + 1, y_pos + dy, True)

    display.send()
    time.sleep(2)


def demo_dot_queries(display):
    """Demo 5: Reading dot states"""
    print("\n" + "=" * 50)
    print("DEMO 5: Reading Dot States")
    print("=" * 50)

    # Set some dots
    display.erase_all()
    display.set_dot(10, 3, True)
    display.set_dot(20, 4, True)
    display.set_dot(30, 5, False)  # Explicitly off

    # Check dot states
    print("Checking dot states:")
    print(f"  Dot at (10, 3): {'ON' if display.get_dot(10, 3) else 'OFF'}")
    print(f"  Dot at (20, 4): {'ON' if display.get_dot(20, 4) else 'OFF'}")
    print(f"  Dot at (30, 5): {'ON' if display.get_dot(30, 5) else 'OFF'}")
    print(f"  Dot at (0, 0): {'ON' if display.get_dot(0, 0) else 'OFF'}")

    display.send()
    time.sleep(2)


def demo_dot_manipulation(display):
    """Demo 6: Dot manipulation functions"""
    print("\n" + "=" * 50)
    print("DEMO 6: Dot Manipulation")
    print("=" * 50)

    # Start with some dots
    display.erase_all()
    for x in range(10, 30, 3):
        display.set_dot(x, 3, True)

    print("Initial pattern...")
    display.send()
    time.sleep(1)

    # Invert some dots
    print("Inverting dots...")
    for x in range(10, 30, 6):
        display.invert_dot(x, 3)  # This will turn them off
        display.invert_dot(x, 4)  # This will turn them on

    display.send()
    time.sleep(2)


def demo_orientation_control(display):
    """Demo 7: Orientation control"""
    print("\n" + "=" * 50)
    print("DEMO 7: Orientation Control")
    print("=" * 50)

    # Show text in normal orientation
    print("Normal orientation...")
    display.write_text("NORMAL", col=25, row=0)
    display.send()
    time.sleep(2)

    # Flip orientation
    print("Flipping orientation...")
    display.toggle_orientation()
    display.write_text("FLIPPED", col=25, row=0)
    display.send()
    time.sleep(2)

    # Flip back
    print("Back to normal...")
    display.toggle_orientation()
    display.write_text("NORMAL", col=25, row=0)
    display.send()
    time.sleep(2)


def demo_speed_control(display):
    """Demo 8: Speed control"""
    print("\n" + "=" * 50)
    print("DEMO 8: Speed Control")
    print("=" * 50)

    print("Testing different speeds...")

    # Normal speed
    print("Normal speed (1.0x)...")
    display.set_speed_factor(1.0)
    for i in range(3):
        display.write_text(f"NORMAL {i + 1}", col=20, row=0)
        display.send()
        time.sleep(display.adjust_delay(0.5))

    # Slower
    print("Slower speed (2.0x)...")
    display.set_speed_factor(2.0)
    for i in range(3):
        display.write_text(f"SLOW {i + 1}", col=22, row=0)
        display.send()
        time.sleep(display.adjust_delay(0.5))

    # Faster
    print("Faster speed (0.5x)...")
    display.set_speed_factor(0.5)
    for i in range(3):
        display.write_text(f"FAST {i + 1}", col=22, row=0)
        display.send()
        time.sleep(display.adjust_delay(0.5))

    # Reset to normal
    display.set_speed_factor(1.0)


def demo_animation(display):
    """Demo 9: Simple animation"""
    print("\n" + "=" * 50)
    print("DEMO 9: Simple Animation")
    print("=" * 50)

    print("Running moving dot animation...")

    # Moving dot across the screen
    for x in range(display.columns):
        display.erase_all()

        # Draw a moving dot with a trail
        display.set_dot(x, 3, True)  # Main dot
        if x > 0:
            display.set_dot(x - 1, 3, True)  # Trail
        if x > 1:
            display.set_dot(x - 2, 3, True)  # Longer trail

        display.send()
        time.sleep(0.05)

    print("Running bouncing dot animation...")

    # Bouncing dot
    x, y = 0, 0
    dx, dy = 1, 1

    for frame in range(100):
        display.erase_all()
        display.set_dot(x, y, True)
        display.send()

        # Update position
        x += dx
        y += dy

        # Bounce off edges
        if x <= 0 or x >= display.columns - 1:
            dx = -dx
        if y <= 0 or y >= display.rows - 1:
            dy = -dy

        time.sleep(0.1)


def demo_practical_patterns(display):
    """Demo 10: Practical usage patterns"""
    print("\n" + "=" * 50)
    print("DEMO 10: Practical Usage Patterns")
    print("=" * 50)

    print("Pattern 1: Status display...")
    display.erase_all()

    # Simulate a status display
    # Title area
    display.write_text("SYSTEM STATUS", col=15, row=0)
    display.send()
    time.sleep(1)

    # Add some "status indicators" manually
    display.erase_all()

    # Status dots (like LEDs)
    colors = ["GREEN", "RED", "YELLOW"]
    for i, color in enumerate(colors):
        x = 10 + i * 20
        # Draw a "status indicator"
        for dx in range(3):
            for dy in range(3):
                display.set_dot(x + dx, 2 + dy, True)

    display.send()
    time.sleep(2)

    print("Pattern 2: Progress bar...")
    display.erase_all()

    # Animated progress bar
    for progress in range(0, display.columns - 10, 3):
        display.erase_all()

        # Progress bar outline
        for x in range(5, display.columns - 5):
            display.set_dot(x, 2, True)  # Top
            display.set_dot(x, 5, True)  # Bottom
        for y in range(2, 6):
            display.set_dot(5, y, True)  # Left
            display.set_dot(display.columns - 6, y, True)  # Right

        # Progress fill
        for x in range(6, 6 + progress):
            for y in range(3, 5):
                display.set_dot(x, y, True)

        display.send()
        time.sleep(0.1)

    time.sleep(1)


def demo_pause(message="", delay=2):
    """Pause between demo sections with a message"""
    if message:
        print(f"\n{message}")
    print(f"Continuing in {delay} seconds...")
    time.sleep(delay)


def main():
    """Main demo function"""
    print("FlipDot Display Library Demo")
    print("===========================")
    print()
    print("This demo will show you how to use all the features of the library.")
    print("Each demo section will be clearly labeled.")
    print()
    print("Hardware setup:")
    print(f"  Port: {UART_PORT}")
    print(f"  Address: {DISPLAY_ADDRESS}")
    print(f"  Size: {DISPLAY_COLUMNS}x{DISPLAY_ROWS}")
    print()
    print("🚀 Starting demo automatically...")
    demo_pause("", 2)

    try:
        # Initialize display
        display = demo_basic_setup()

        # Run all demos
        demo_basic_operations(display)
        demo_pause("Demo 1 complete! Moving to next demo...", 3)

        demo_individual_dots(display)
        demo_pause("Demo 2 complete! Moving to next demo...", 3)

        demo_text_display(display)
        demo_pause("Demo 3 complete! Moving to next demo...", 3)

        demo_dot_queries(display)
        demo_pause("Demo 4 complete! Moving to next demo...", 3)

        demo_dot_manipulation(display)
        demo_pause("Demo 5 complete! Moving to next demo...", 3)

        demo_orientation_control(display)
        demo_pause("Demo 6 complete! Moving to next demo...", 3)

        demo_speed_control(display)
        demo_pause("Demo 7 complete! Moving to next demo...", 3)

        demo_animation(display)
        demo_pause("Demo 8 complete! Moving to next demo...", 3)

        demo_practical_patterns(display)
        demo_pause("Demo 9 complete! Demo finished!", 3)

        # Final message
        print("\n" + "=" * 50)
        print("DEMO COMPLETE!")
        print("=" * 50)
        print()
        print("You've seen all the main features of the library:")
        print("  ✓ Basic setup and connection")
        print("  ✓ Display clearing and filling")
        print("  ✓ Individual dot control")
        print("  ✓ Text display")
        print("  ✓ Reading dot states")
        print("  ✓ Dot manipulation")
        print("  ✓ Orientation control")
        print("  ✓ Speed control")
        print("  ✓ Animation techniques")
        print("  ✓ Practical usage patterns")
        print()
        print("Key concepts to remember:")
        print("  - Always call display.send() to update the hardware")
        print("  - write_text() clears the display first")
        print("  - Use set_dot() for precise control")
        print("  - Coordinates are (column, row) starting from (0, 0)")
        print("  - Check your display's address and port settings")
        print()
        print("Happy coding with your FlipDot display!")

        # Clear display before exit
        display.erase_all()
        display.send()

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        print("Clearing display...")
        try:
            display.erase_all()
            display.send()
        except:
            pass

    except Exception as e:
        print(f"\nDemo error: {e}")
        print("Make sure your display is connected and the settings are correct.")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()