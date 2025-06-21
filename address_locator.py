#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial.tools.list_ports
import time
import sys
from hanover_flipdot_py3 import HanoverFlipDot  # Import from your main library

UART_PORT = "/dev/cu.usbserial-BG00Q8VA"  # Your hardcoded port
DISPLAY_COLUMNS = 84
DISPLAY_ROWS = 8
CYCLE_DELAY = 3  # Seconds to wait at each address


def test_address_fill_clear(port, address):
    """Test an address by filling then clearing the display"""
    try:
        # Create display instance for this address
        display = HanoverFlipDot(
            port,
            address=address,
            columns=DISPLAY_COLUMNS,
            rows=DISPLAY_ROWS,
            flip_orientation=False,
            debug=False  # Keep quiet during testing
        )

        print(f"Testing address {address} - FILL")
        # Fill display (all dots on)
        display.fill_all()
        display.send()
        time.sleep(CYCLE_DELAY)

        print(f"Testing address {address} - CLEAR")
        # Clear display (all dots off)
        display.erase_all()
        display.send()
        time.sleep(CYCLE_DELAY)

        return True

    except Exception as e:
        print(f"  Error testing address {address}: {e}")
        return False


def run_address_cycle(port, start_addr=1, end_addr=16):
    """Cycle through addresses automatically"""
    print(f"\nCycling through addresses {start_addr} to {end_addr}...")
    print(f"Each address will FILL for {CYCLE_DELAY} seconds, then CLEAR for {CYCLE_DELAY} seconds.")
    print("WATCH YOUR DISPLAY to see which address causes a change.")
    print("Press Ctrl+C to stop the test.")
    print("-" * 50)

    try:
        # Cycle through each address twice for confirmation
        for cycle in range(2):
            print(f"\nStarting cycle {cycle + 1}...")

            for addr in range(start_addr, end_addr + 1):
                print(f"\n--- ADDRESS {addr} ---")
                test_address_fill_clear(port, addr)

            print(f"Cycle {cycle + 1} complete.")

        print("\nTest completed. If your display responded to an address, that's your display address.")

    except KeyboardInterrupt:
        print("\nTest stopped by user.")

    # Final clear attempt on default address
    try:
        display = HanoverFlipDot(port, address=2, columns=DISPLAY_COLUMNS, rows=DISPLAY_ROWS, debug=False)
        display.erase_all()
        display.send()
    except:
        pass


def show_available_ports():
    """Show available serial ports"""
    print("\nAvailable serial ports:")
    ports = list(serial.tools.list_ports.comports())

    if not ports:
        print("No serial ports found!")
        return []

    for i, port in enumerate(ports):
        print(f"{i + 1}. {port.device} - {port.description}")

    return ports


def main():
    print("=" * 60)
    print(" FlipDot Display Address Finder")
    print("=" * 60)
    print("This utility cycles through addresses to find your display.")
    print("")
    print(f"Default serial port: {UART_PORT}")
    print(f"Default display size: {DISPLAY_COLUMNS}x{DISPLAY_ROWS}")

    # Ask user about serial port
    use_default = input("\nUse default serial port? (Y/n): ").strip().lower()

    if use_default != 'n':
        port = UART_PORT
    else:
        ports = show_available_ports()
        if ports:
            try:
                choice = int(input("\nEnter port number: ")) - 1
                if 0 <= choice < len(ports):
                    port = ports[choice].device
                else:
                    print("Invalid choice, using default")
                    port = UART_PORT
            except ValueError:
                port_choice = input("\nOr enter port name manually: ").strip()
                port = port_choice if port_choice else UART_PORT
        else:
            port = UART_PORT

    # Ask for address range
    print("\nThe standard address range for Hanover displays is 1-16")
    custom_range = input("Use custom address range? (y/N): ").strip().lower()

    if custom_range == 'y':
        try:
            start_addr = int(input("Enter start address: "))
            end_addr = int(input("Enter end address: "))
        except ValueError:
            print("Invalid input, using default range 1-16")
            start_addr, end_addr = 1, 16
    else:
        start_addr, end_addr = 1, 16

    # Final confirmation
    input(f"\nReady to test addresses {start_addr}-{end_addr} on {port}.\nPress Enter to start...")

    # Run the test
    run_address_cycle(port, start_addr, end_addr)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        print("\nAddress test completed.")