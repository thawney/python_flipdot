#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FlipDot Visual Simulator - Enhanced with Input Handling
Run any of your existing scripts with visual simulation - no code changes needed!

NEW: Automatically handles input() prompts with smart defaults!

Usage:
    python3 visual_simulator.py clock.py           # Run clock.py visually
    python3 visual_simulator.py live_captions.py   # Run live_captions.py visually
    python3 visual_simulator.py                    # Run demo

This patches your main library to show output visually instead of sending to hardware.
Your scripts run completely unchanged - they still import hanover_flipdot_py3 normally!
"""

import sys
import os
import pygame
import time
import threading
import queue

# Import the real library first
try:
    import hanover_flipdot_py3

    REAL_LIBRARY_AVAILABLE = True
    print("✓ Found hanover_flipdot_py3.py - will use real logic with visual output")
except ImportError:
    REAL_LIBRARY_AVAILABLE = False
    print("✗ hanover_flipdot_py3.py not found!")
    print("Make sure hanover_flipdot_py3.py is in the same directory")
    sys.exit(1)


def is_main_thread():
    """Check if we're running on the main thread"""
    return threading.current_thread() is threading.main_thread()


class WindowClosedException(Exception):
    """Exception raised when the pygame window is closed by the user"""
    pass


class SmartInputHandler:
    """Handles input() calls automatically with smart defaults"""

    def __init__(self, debug=False):
        self.debug = debug
        self.input_responses = {
            # Common prompts and their smart defaults

            # Speech recognition test prompts
            "test speech recognition": "n",
            "test recognition": "n",
            "🧪 test speech recognition first": "n",

            # General confirmation prompts
            "continue": "y",
            "start": "y",
            "ready": "y",
            "🚀 start live captioning": "y",
            "press enter": "",

            # Port/connection prompts
            "use default": "y",
            "default port": "y",
            "default serial port": "y",

            # Demo/test prompts
            "demo": "n",
            "custom": "n",
            "custom range": "n",

            # Address range prompts
            "address range": "n",

            # Common y/n patterns
            "(y/n)": "y",
            "(y/N)": "y",
            "(Y/n)": "y",
            "(n/Y)": "y",
        }

        # Track prompts for learning
        self.seen_prompts = []

    def smart_input(self, prompt=""):
        """Smart input replacement that provides sensible defaults"""
        original_prompt = prompt
        prompt_lower = prompt.lower().strip()

        if self.debug:
            print(f"🤖 INPUT HANDLER: '{prompt}'")

        # Track this prompt
        self.seen_prompts.append(original_prompt)

        # Find matching response
        response = None
        for pattern, default_response in self.input_responses.items():
            if pattern in prompt_lower:
                response = default_response
                break

        # Fallback patterns
        if response is None:
            if "(y/n)" in prompt_lower or "(y/N)" in prompt_lower or "(Y/n)" in prompt_lower:
                # Default to yes for most y/n prompts in demo mode
                response = "y"
            elif "press enter" in prompt_lower or "continue" in prompt_lower:
                response = ""
            elif "port" in prompt_lower or "address" in prompt_lower:
                response = "y"  # Use defaults
            elif "test" in prompt_lower and ("y/n" in prompt_lower):
                response = "n"  # Skip tests in visual mode
            else:
                # Generic fallback - empty string (like pressing Enter)
                response = ""

        # Show what we're doing
        if response == "":
            print(f"📝 AUTO-INPUT: '{prompt}' → [Enter]")
        else:
            print(f"📝 AUTO-INPUT: '{prompt}' → '{response}'")

        return response

    def get_input_summary(self):
        """Get a summary of all input prompts handled"""
        if self.seen_prompts:
            print("\n📋 Input prompts handled automatically:")
            for i, prompt in enumerate(self.seen_prompts, 1):
                print(f"   {i}. {prompt}")
        else:
            print("\n📋 No input prompts were encountered")


class VisualHanoverFlipDot:
    """
    Visual version that wraps the real HanoverFlipDot class
    Uses all the real logic but shows output in pygame window
    """

    def __init__(self, port, address=2, columns=84, rows=8, flip_orientation=False, debug=False, speed_factor=1.0):
        print(f"🖥️  Visual mode: Creating {columns}x{rows} display simulation")

        # Store display parameters
        self.columns = columns
        self.rows = rows
        self.debug = debug

        # Create the real HanoverFlipDot instance normally
        self.real_display = hanover_flipdot_py3._OriginalHanoverFlipDot(
            port=port,
            address=address,
            columns=columns,
            rows=rows,
            flip_orientation=flip_orientation,
            debug=debug,
            speed_factor=speed_factor
        )

        # Override the ser attribute with a convincing fake
        class FakeSerial:
            def __init__(self):
                self.is_open = True
                self.port = port
                self.baudrate = 4800

            def write(self, data):
                return len(data)  # Return bytes written

            def flush(self):
                pass

            def reset_input_buffer(self):
                pass

            def reset_output_buffer(self):
                pass

            def close(self):
                self.is_open = False

            def __bool__(self):
                return True  # Important: makes if self.ser: return True

        # Replace the serial connection with our fake
        self.real_display.ser = FakeSerial()

        # Make sure we can access all the real display's attributes directly
        self.address = self.real_display.address
        self.port = self.real_display.port
        self.flip_orientation = self.real_display.flip_orientation
        self.speed_factor = self.real_display.speed_factor
        self.data_size = self.real_display.data_size
        self.byte_per_column = self.real_display.byte_per_column
        self.buf = self.real_display.buf
        self.header = self.real_display.header
        self.footer = self.real_display.footer

        # Initialize pygame display (only if we're on the main thread)
        if is_main_thread():
            self.setup_pygame()
        else:
            print("⚠️  Pygame setup skipped (not on main thread)")
            # Set dummy values so the object still works
            self.screen = None
            self.font = None
            self.small_font = None
            self.update_count = 0

        if debug:
            print(f"✓ Visual simulator ready: {columns}x{rows}")
            print(f"✓ Real display buffer size: {len(self.real_display.buf)}")
            print(f"✓ Real display has write_text: {hasattr(self.real_display, 'write_text')}")
            print(f"✓ Main thread: {is_main_thread()}")

    def setup_pygame(self):
        """Initialize pygame display"""
        print("🎮 Initializing pygame display...")
        pygame.init()

        # Display settings
        self.dot_size = 8
        self.dot_gap = 2
        self.margin = 30

        # Calculate window size
        self.window_width = self.columns * (self.dot_size + self.dot_gap) - self.dot_gap + 2 * self.margin
        self.window_height = self.rows * (self.dot_size + self.dot_gap) - self.dot_gap + 2 * self.margin + 100

        print(f"🖼️  Creating window: {self.window_width}x{self.window_height}")

        # Create window
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption(f"FlipDot Visual Simulation - {self.columns}x{self.rows}")

        # Colors
        self.COLOR_BG = (25, 25, 25)
        self.COLOR_DOT_OFF = (50, 50, 50)
        self.COLOR_DOT_ON = (255, 255, 0)
        self.COLOR_BORDER = (100, 100, 100)
        self.COLOR_TEXT = (255, 255, 255)
        self.COLOR_ACCENT = (255, 221, 68)
        self.COLOR_INFO = (150, 150, 255)

        # Font for info text
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

        # Status info
        self.last_update_time = time.time()
        self.update_count = 0

        # Initial display
        self.update_pygame_display()
        print("✅ Pygame window created and ready")

    def update_pygame_display(self):
        """Update the pygame window with current display state - main thread only"""
        # CRITICAL: Only do pygame operations on the main thread (macOS requirement)
        if not is_main_thread():
            if self.debug:
                print("📺 Visual: Skipping pygame update (not on main thread)")
            return

        try:
            # Handle pygame events to keep window responsive
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("🚪 Closing visual simulation...")
                    pygame.quit()
                    sys.exit(0)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        print("🚪 ESC pressed - closing visual simulation...")
                        pygame.quit()
                        sys.exit(0)

            # Fill background
            self.screen.fill(self.COLOR_BG)

            # Draw title
            title_text = f"FlipDot Visual Simulation - {self.columns}x{self.rows}"
            title_surface = self.font.render(title_text, True, self.COLOR_ACCENT)
            title_rect = title_surface.get_rect()
            title_rect.centerx = self.window_width // 2
            title_rect.y = 5
            self.screen.blit(title_surface, title_rect)

            # Draw subtitle
            subtitle_text = "Using real hanover_flipdot_py3.py logic with visual output + smart input handling"
            subtitle_surface = self.small_font.render(subtitle_text, True, self.COLOR_INFO)
            subtitle_rect = subtitle_surface.get_rect()
            subtitle_rect.centerx = self.window_width // 2
            subtitle_rect.y = 25
            self.screen.blit(subtitle_surface, subtitle_rect)

            # Count active dots for debugging
            active_dots = 0

            # Draw dots
            for row in range(self.rows):
                for col in range(self.columns):
                    # Get dot state from real library
                    is_on = self.real_display.get_dot(col, row)
                    if is_on:
                        active_dots += 1

                    # Calculate dot position
                    x = self.margin + col * (self.dot_size + self.dot_gap)
                    y = self.margin + 50 + row * (self.dot_size + self.dot_gap)

                    # Choose color
                    color = self.COLOR_DOT_ON if is_on else self.COLOR_DOT_OFF

                    # Draw dot
                    center_x = x + self.dot_size // 2
                    center_y = y + self.dot_size // 2
                    pygame.draw.circle(self.screen, color, (center_x, center_y), self.dot_size // 2)
                    pygame.draw.circle(self.screen, self.COLOR_BORDER, (center_x, center_y), self.dot_size // 2, 1)

            # Draw status info
            status_y = self.window_height - 45

            # Update count
            self.update_count += 1
            update_text = f"Updates: {self.update_count}"
            update_surface = self.small_font.render(update_text, True, self.COLOR_TEXT)
            self.screen.blit(update_surface, (10, status_y))

            # Active dots count
            dots_text = f"Active dots: {active_dots}"
            dots_surface = self.small_font.render(dots_text, True, self.COLOR_TEXT)
            self.screen.blit(dots_surface, (120, status_y))

            # Thread status
            thread_name = threading.current_thread().name
            thread_text = f"Thread: {thread_name}"
            thread_surface = self.small_font.render(thread_text, True, self.COLOR_TEXT)
            self.screen.blit(thread_surface, (250, status_y))

            # Speed factor if available
            if hasattr(self.real_display, 'speed_factor'):
                speed_text = f"Speed: {self.real_display.speed_factor:.1f}x"
                speed_surface = self.small_font.render(speed_text, True, self.COLOR_TEXT)
                self.screen.blit(speed_surface, (380, status_y))

            # Orientation if flipped
            if hasattr(self.real_display, 'flip_orientation') and self.real_display.flip_orientation:
                orient_text = "Orientation: FLIPPED"
                orient_surface = self.small_font.render(orient_text, True, self.COLOR_ACCENT)
                self.screen.blit(orient_surface, (480, status_y))

            # Controls
            controls_y = self.window_height - 25
            controls_text = "ESC or close window to exit • Worker threads safe on macOS"
            controls_surface = self.small_font.render(controls_text, True, self.COLOR_TEXT)
            controls_rect = controls_surface.get_rect()
            controls_rect.centerx = self.window_width // 2
            controls_rect.y = controls_y
            self.screen.blit(controls_surface, controls_rect)

            # Update display
            pygame.display.flip()

        except Exception as e:
            if self.debug:
                print(f"⚠️  Pygame update error: {e}")
            # Don't crash on pygame errors

    def __getattr__(self, name):
        """Delegate any remaining methods to the real display"""
        if hasattr(self.real_display, name):
            return getattr(self.real_display, name)
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def send(self):
        """Completely override send() - only do pygame operations on main thread"""
        if self.debug:
            thread_name = threading.current_thread().name
            print(f"📺 Visual: Sending to display from thread '{thread_name}'")

        # CRITICAL: Only update pygame display if we're on the main thread
        # On macOS, calling pygame from worker threads causes crashes
        if is_main_thread():
            try:
                self.update_pygame_display()
            except Exception as e:
                if self.debug:
                    print(f"⚠️  Display update error: {e}")
        else:
            if self.debug:
                print("📺 Visual: Skipping pygame update (worker thread - safe on macOS)")

        # Always return success (0) to make scripts happy
        return 0

    def connect(self):
        """Override connect - already handled in __init__"""
        return True

    # Explicitly delegate core methods to ensure they work
    def write_text(self, *args, **kwargs):
        if self.debug:
            print(f"📺 Visual: write_text called with args={args}")
        return self.real_display.write_text(*args, **kwargs)

    def set_dot(self, *args, **kwargs):
        return self.real_display.set_dot(*args, **kwargs)

    def get_dot(self, *args, **kwargs):
        return self.real_display.get_dot(*args, **kwargs)

    def erase_all(self):
        if self.debug:
            print("📺 Visual: erase_all called")
        return self.real_display.erase_all()

    def fill_all(self):
        if self.debug:
            print("📺 Visual: fill_all called")
        return self.real_display.fill_all()

    def invert_dot(self, *args, **kwargs):
        return self.real_display.invert_dot(*args, **kwargs)

    def toggle_orientation(self):
        result = self.real_display.toggle_orientation()
        # Update our local copy
        self.flip_orientation = self.real_display.flip_orientation
        return result

    def set_speed_factor(self, *args, **kwargs):
        result = self.real_display.set_speed_factor(*args, **kwargs)
        # Update our local copy
        self.speed_factor = self.real_display.speed_factor
        return result

    def get_speed_factor(self):
        return self.real_display.get_speed_factor()

    def adjust_delay(self, *args, **kwargs):
        return self.real_display.adjust_delay(*args, **kwargs)

    def close(self):
        """Close the pygame display"""
        try:
            pygame.quit()
        except:
            pass


def patch_library():
    """Replace the HanoverFlipDot class in the main library with our visual version"""
    print("🔧 Patching hanover_flipdot_py3.HanoverFlipDot with visual version...")

    # Store the original class FIRST (before replacing it)
    hanover_flipdot_py3._OriginalHanoverFlipDot = hanover_flipdot_py3.HanoverFlipDot

    # Replace with our visual version
    hanover_flipdot_py3.HanoverFlipDot = VisualHanoverFlipDot

    print("✓ Library patched - all scripts will now show visual output!")


def patch_input(input_handler):
    """Replace the built-in input function with our smart handler"""
    return input_handler.smart_input


def run_script(script_path):
    """Run a Python script with the patched library and smart input handling"""
    if not os.path.exists(script_path):
        print(f"✗ Script not found: {script_path}")
        return False

    print(f"🚀 Running {script_path} with visual simulation...")
    print("🤖 Smart input handling enabled - no prompts will block!")
    print("=" * 70)

    try:
        print(f"📂 Loading script: {script_path}")

        # Add the script's directory to Python path so imports work
        script_dir = os.path.dirname(os.path.abspath(script_path))
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        # Create smart input handler
        input_handler = SmartInputHandler(debug=True)

        # Make sure the script can import the patched library
        sys.modules['hanover_flipdot_py3'] = hanover_flipdot_py3

        print(f"▶️  Executing script with smart input handling...")

        # Read the script file and execute it directly to preserve __name__ == "__main__"
        with open(script_path, 'r') as f:
            script_code = f.read()

        # Create a proper execution environment with patched input
        script_globals = {
            '__name__': '__main__',
            '__file__': script_path,
            '__builtins__': __builtins__,
            'hanover_flipdot_py3': hanover_flipdot_py3,  # Make sure our patched lib is available
            'input': patch_input(input_handler),  # Replace input with our smart handler
        }

        # Execute the script as if it was run directly
        exec(script_code, script_globals)

        # Show input handling summary
        input_handler.get_input_summary()

        print(f"✅ Script execution completed normally")
        print("🖼️  Script finished - close window or press ESC to exit")

        # Keep the pygame window open after script completes
        try:
            clock = pygame.time.Clock()
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        print("🚪 Window closed by user")
                        return
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            print("🚪 ESC pressed - exiting")
                            return

                # Update any existing displays that might still be active
                try:
                    pygame.display.flip()
                except:
                    pass

                clock.tick(60)  # 60 FPS
        except:
            # If pygame fails, just exit gracefully
            pass

    except KeyboardInterrupt:
        print("\n⏹️  Script interrupted by user (Ctrl+C)")
    except SystemExit as e:
        print(f"🚪 Script exited (window closed or script finished) with code: {e.code}")
        # Don't try to keep pygame window open if it was closed by user
        print("🏁 Simulation ended")

    except WindowClosedException as e:
        print(f"🚪 {e}")
        print("🏁 Simulation ended")

    except Exception as e:
        print(f"✗ Error running script: {e}")
        print(f"✗ Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        print("🏁 Simulation ended due to error")

    finally:
        # Clean up pygame
        try:
            pygame.quit()
        except:
            pass
        print("🧹 Cleanup completed")


def run_demo():
    """Run a built-in demo if no script is provided"""
    print("🎮 Running FlipDot visual simulator demo...")
    print("=" * 50)

    # Patch the library
    patch_library()

    # Create a demo display
    display = hanover_flipdot_py3.HanoverFlipDot(
        port="DEMO",
        address=2,
        columns=84,
        rows=8,
        debug=True
    )

    print("🎯 Demo starting - watch the pygame window!")

    try:
        # Demo 1: Text rendering
        print("Demo 1: Text with real fonts...")
        display.erase_all()
        display.write_text("FlipDot Simulator!", col=3, row=0)
        display.send()
        time.sleep(3)

        # Demo 2: Individual dots
        print("Demo 2: Individual dot control...")
        display.erase_all()
        for i in range(0, 80, 4):
            display.set_dot(i, 3, True)
            display.set_dot(i + 1, 4, True)
        display.send()
        time.sleep(2)

        # Demo 3: Fill pattern
        print("Demo 3: Fill and clear...")
        display.fill_all()
        display.send()
        time.sleep(1)

        display.erase_all()
        display.send()
        time.sleep(1)

        # Demo 4: Special characters (if available)
        print("Demo 4: Special characters...")
        display.erase_all()
        display.write_text("Temp: 25°C ±1", col=8, row=0)
        display.send()
        time.sleep(3)

        # Demo 5: Animation
        print("Demo 5: Simple animation...")
        for frame in range(20):
            display.erase_all()
            x = frame * 4 % display.columns
            display.set_dot(x, 3, True)
            display.set_dot((x - 4) % display.columns, 3, True)
            display.set_dot((x - 8) % display.columns, 3, True)
            display.send()
            time.sleep(0.1)

        # Demo 6: Speed control (if available)
        if hasattr(display, 'set_speed_factor'):
            print("Demo 6: Speed control...")
            display.set_speed_factor(2.0)
            display.erase_all()
            display.write_text("Slow speed", col=10, row=0)
            display.send()
            time.sleep(2)

            display.set_speed_factor(0.5)
            display.erase_all()
            display.write_text("Fast speed", col=10, row=0)
            display.send()
            time.sleep(1)

        # Demo 7: Orientation (if available)
        if hasattr(display, 'toggle_orientation'):
            print("Demo 7: Orientation flip...")
            display.toggle_orientation()
            display.erase_all()
            display.write_text("Flipped!", col=15, row=0)
            display.send()
            time.sleep(2)

            display.toggle_orientation()  # Back to normal

        # Final message
        display.erase_all()
        display.write_text("Demo Complete!", col=8, row=0)
        display.send()

        print("\n" + "=" * 50)
        print("✅ Demo complete!")
        print("✅ Close the pygame window or press ESC to exit")
        print("✅ Use: python3 visual_simulator.py yourscript.py")
        print("=" * 50)

        # Keep the window open
        clock = pygame.time.Clock()
        while True:
            # Update display to handle events
            display.update_pygame_display()
            clock.tick(60)  # 60 FPS

    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except SystemExit:
        pass
    except Exception as e:
        print(f"✗ Demo error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            display.close()
        except:
            pass


def show_help():
    """Show usage help"""
    print("🎯 FlipDot Visual Simulator - Enhanced Edition")
    print("=" * 55)
    print("NEW: Automatically handles input() prompts!")
    print("")
    print("Usage:")
    print("  python3 visual_simulator.py                # Run demo")
    print("  python3 visual_simulator.py <script.py>    # Run script visually")
    print("")
    print("Examples:")
    print("  python3 visual_simulator.py clock.py")
    print("  python3 visual_simulator.py live_captions.py")
    print("  python3 visual_simulator.py address_locator.py")
    print("  python3 visual_simulator.py demo.py")
    print("")
    print("Features:")
    print("  ✓ No code changes needed in your scripts")
    print("  ✓ Uses your real hanover_flipdot_py3.py logic")
    print("  ✓ Visual output in pygame window")
    print("  ✓ Smart input handling - no more blocking prompts!")
    print("  ✓ Real fonts, speed control, orientation - everything!")
    print("")
    print("Smart Input Handling:")
    print("  • Automatically answers y/n prompts with sensible defaults")
    print("  • Skips speech recognition tests (says 'n')")
    print("  • Uses default ports and addresses (says 'y')")
    print("  • Auto-continues through setup prompts")
    print("  • Shows what inputs it's handling automatically")
    print("")
    print("Requirements:")
    print("  pip install pygame")


def main():
    """Main function"""
    print("🎯 FlipDot Visual Simulator - Enhanced Edition")
    print("=" * 55)

    # Check pygame
    try:
        import pygame
    except ImportError:
        print("✗ pygame not found!")
        print("Install with: pip install pygame")
        sys.exit(1)

    # Parse arguments
    if len(sys.argv) == 1:
        # No arguments - run demo
        run_demo()
    elif len(sys.argv) == 2:
        script_path = sys.argv[1]

        # Check for help
        if script_path in ['-h', '--help', 'help']:
            show_help()
            return

        # Patch the library
        patch_library()

        # Test that patching worked by creating a simple instance
        print("🧪 Testing patched library...")
        try:
            test_display = hanover_flipdot_py3.HanoverFlipDot("TEST", address=2, columns=84, rows=8, debug=True)
            print("✅ Patched library test successful")
            print("🖼️  Visual window should be visible now")

            # Test basic functionality
            test_display.erase_all()
            test_display.write_text("READY", col=30, row=0)
            test_display.send()
            print("📺 Test message displayed")

            # Give user a moment to see the window
            time.sleep(2)

        except Exception as e:
            print(f"✗ Patched library test failed: {e}")
            import traceback
            traceback.print_exc()
            return

        # Run the user's script
        run_script(script_path)
    else:
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()