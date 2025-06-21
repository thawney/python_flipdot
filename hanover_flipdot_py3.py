import serial
import time


class HanoverFlipDot:
    """
    Python 3 compatible driver for Hanover Flip Dot displays.
    This implementation is based on the protocol described in the original library
    but rewritten to work with Python 3.
    """

    def __init__(self, port, address=2, columns=84, rows=8, flip_orientation=False, debug=False, speed_factor=1.0):
        self.port = port
        self.address = address + 16  # Address offset
        self.columns = columns
        self.rows = rows
        self.flip_orientation = flip_orientation
        self.debug = debug
        self.speed_factor = speed_factor  # Speed factor (higher = slower, lower = faster)

        # Calculate data size and bytes per column
        if rows % 8:
            self.rows = rows + (8 - (rows % 8))

        self.data_size = (self.rows * columns) // 8
        self.byte_per_column = self.rows // 8

        # Prepare header
        res1, res2 = self.byte_to_ascii(self.data_size & 0xff)
        add1, add2 = self.byte_to_ascii(self.address)
        self.header = [0x02, add1, add2, res1, res2]

        # Prepare footer (checksum will be calculated during send)
        self.footer = [0x03, 0x00, 0x00]

        # Initialize data buffer
        self.buf = [0] * (self.data_size // self.byte_per_column)

        if self.debug:
            print(f"Initialized {columns}x{rows} flip dot display")
            print(f"Address: {address}")
            print(f"Orientation: {'Flipped' if flip_orientation else 'Normal'}")
            print(f"Speed factor: {speed_factor}")
            print(f"Data size: {self.data_size}")
            print(f"Buffer size: {len(self.buf)}")

        # Connect to serial port
        self.connect()

    def connect(self):
        """Connect to the serial device"""
        try:
            self.ser = serial.Serial(port=self.port, baudrate=4800)
            if self.debug:
                print(f"Connected to serial port: {self.port}")
        except Exception as e:
            print(f"Error opening serial port: {e}")
            self.ser = None

    def byte_to_ascii(self, byte):
        """
        Convert a byte to its ASCII representation.
        The protocol represents each byte by their ASCII representation.
        For example, 0x67 is represented by 0x36 0x37 (ASCII '6' and '7')
        """
        b1 = byte >> 4
        if b1 > 9:
            b1 += 0x37  # ASCII 'A'-'F'
        else:
            b1 += 0x30  # ASCII '0'-'9'

        b2 = byte % 16
        if b2 > 9:
            b2 += 0x37  # ASCII 'A'-'F'
        else:
            b2 += 0x30  # ASCII '0'-'9'

        return (b1, b2)

    def calculate_checksum(self, crc):
        """Compute the checksum of the data frame"""
        sum_value = 0

        # Sum all bytes of the header
        for byte in self.header:
            sum_value += byte

        # Add the data CRC
        sum_value += crc

        # Add 1 (protocol requirement)
        sum_value += 1

        # Cast to 8 bits
        sum_value = sum_value & 0xFF

        # Checksum is sum XOR 255 + 1
        crc = (sum_value ^ 255) + 1

        # Transform to ASCII
        crc1, crc2 = self.byte_to_ascii(crc)

        # Update footer
        self.footer[1] = crc1
        self.footer[2] = crc2

        if self.debug:
            print(f"SUM: {sum_value}, CRC: {crc}, SUM + CRC: {sum_value + crc}")

    def erase_all(self):
        """Erase the entire display (set all dots to 0)"""
        if self.debug:
            print("Erasing display")
        for i in range(len(self.buf)):
            self.buf[i] = 0

    def fill_all(self):
        """Fill the entire display (set all dots to 1)"""
        if self.debug:
            print("Filling display")
        for i in range(len(self.buf)):
            # Calculate the value that sets all bits in this column
            self.buf[i] = (1 << self.rows) - 1

    def set_dot(self, col, row, state):
        """Set the state of a specific dot"""
        # Handle flipped orientation
        if self.flip_orientation:
            col = self.columns - 1 - col
            row = self.rows - 1 - row

        if col < 0 or col >= self.columns or row < 0 or row >= self.rows:
            return False

        if state:
            # Set the bit
            self.buf[col] |= (1 << row)
        else:
            # Clear the bit
            self.buf[col] &= ~(1 << row)

        return True

    def invert_dot(self, col, row):
        """Invert the state of a specific dot"""
        # Handle flipped orientation
        if self.flip_orientation:
            col = self.columns - 1 - col
            row = self.rows - 1 - row

        if col < 0 or col >= self.columns or row < 0 or row >= self.rows:
            return False

        # XOR the bit to invert it
        self.buf[col] ^= (1 << row)

        return True

    def get_dot(self, col, row):
        """Get the state of a specific dot"""
        # Handle flipped orientation
        if self.flip_orientation:
            col = self.columns - 1 - col
            row = self.rows - 1 - row

        if col < 0 or col >= self.columns or row < 0 or row >= self.rows:
            return False

        # Check if the bit is set
        return bool(self.buf[col] & (1 << row))

    def send(self):
        """Send the frame via the serial port"""
        if self.debug:
            print("Sending data to display")
            print(f"Header: {self.header}")

        if not self.ser:
            print("Serial connection not established")
            return -1

        try:
            # Send the header
            for byte in self.header:
                self.ser.write(bytes([byte]))

            # Send the data
            crc = 0
            for col in self.buf:
                for i in range(self.byte_per_column):
                    # Get the byte for this part of the column
                    byte_val = (col >> (8 * i)) & 0xFF
                    b1, b2 = self.byte_to_ascii(byte_val)

                    # Add to CRC
                    crc += b1
                    crc += b2

                    # Send the ASCII representation
                    self.ser.write(bytes([b1]))
                    self.ser.write(bytes([b2]))

            # Calculate and send the checksum
            self.calculate_checksum(crc)

            # Send the footer
            for byte in self.footer:
                self.ser.write(bytes([byte]))

            return 0
        except Exception as e:
            print(f"Error sending data: {e}")
            return -1

    def write_text(self, text, col=0, row=0):
        """
        Write simple text to the display.
        This is a basic implementation that only supports ASCII characters
        and uses a simple 5x7 font.
        """
        # Simple ASCII 5x7 font (limited character set - just uppercase + numbers)
        # Each character is represented as an array of 5 bytes, each byte is a column
        font = {
            ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
            '!': [0x00, 0x00, 0x5F, 0x00, 0x00],
            '"': [0x00, 0x07, 0x00, 0x07, 0x00],
            '#': [0x14, 0x7F, 0x14, 0x7F, 0x14],
            '$': [0x24, 0x2A, 0x7F, 0x2A, 0x12],
            '%': [0x23, 0x13, 0x08, 0x64, 0x62],
            '&': [0x36, 0x49, 0x56, 0x20, 0x50],
            "'": [0x00, 0x08, 0x07, 0x03, 0x00],
            '(': [0x00, 0x1C, 0x22, 0x41, 0x00],
            ')': [0x00, 0x41, 0x22, 0x1C, 0x00],
            '*': [0x14, 0x08, 0x3E, 0x08, 0x14],
            '+': [0x08, 0x08, 0x3E, 0x08, 0x08],
            ',': [0x00, 0x50, 0x30, 0x00, 0x00],
            '-': [0x08, 0x08, 0x08, 0x08, 0x08],
            '.': [0x00, 0x60, 0x60, 0x00, 0x00],
            '/': [0x20, 0x10, 0x08, 0x04, 0x02],
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
            ':': [0x00, 0x36, 0x36, 0x00, 0x00],
            ';': [0x00, 0x56, 0x36, 0x00, 0x00],
            '<': [0x08, 0x14, 0x22, 0x41, 0x00],
            '=': [0x14, 0x14, 0x14, 0x14, 0x14],
            '>': [0x00, 0x41, 0x22, 0x14, 0x08],
            '?': [0x02, 0x01, 0x51, 0x09, 0x06],
            '@': [0x3E, 0x41, 0x5D, 0x55, 0x5E],
            'A': [0x7C, 0x12, 0x11, 0x12, 0x7C],
            'B': [0x7F, 0x49, 0x49, 0x49, 0x36],
            'C': [0x3E, 0x41, 0x41, 0x41, 0x22],
            'D': [0x7F, 0x41, 0x41, 0x22, 0x1C],
            'E': [0x7F, 0x49, 0x49, 0x49, 0x41],
            'F': [0x7F, 0x09, 0x09, 0x09, 0x01],
            'G': [0x3E, 0x41, 0x49, 0x49, 0x3A],
            'H': [0x7F, 0x08, 0x08, 0x08, 0x7F],
            'I': [0x00, 0x41, 0x7F, 0x41, 0x00],
            'J': [0x20, 0x40, 0x41, 0x3F, 0x01],
            'K': [0x7F, 0x08, 0x14, 0x22, 0x41],
            'L': [0x7F, 0x40, 0x40, 0x40, 0x40],
            'M': [0x7F, 0x02, 0x0C, 0x02, 0x7F],
            'N': [0x7F, 0x04, 0x08, 0x10, 0x7F],
            'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],
            'P': [0x7F, 0x09, 0x09, 0x09, 0x06],
            'Q': [0x3E, 0x41, 0x51, 0x21, 0x5E],
            'R': [0x7F, 0x09, 0x19, 0x29, 0x46],
            'S': [0x26, 0x49, 0x49, 0x49, 0x32],
            'T': [0x01, 0x01, 0x7F, 0x01, 0x01],
            'U': [0x3F, 0x40, 0x40, 0x40, 0x3F],
            'V': [0x1F, 0x20, 0x40, 0x20, 0x1F],
            'W': [0x3F, 0x40, 0x30, 0x40, 0x3F],
            'X': [0x63, 0x14, 0x08, 0x14, 0x63],
            'Y': [0x07, 0x08, 0x70, 0x08, 0x07],
            'Z': [0x61, 0x51, 0x49, 0x45, 0x43],
            '[': [0x00, 0x7F, 0x41, 0x41, 0x00],
            '\\': [0x02, 0x04, 0x08, 0x10, 0x20],
            ']': [0x00, 0x41, 0x41, 0x7F, 0x00],
            '^': [0x04, 0x02, 0x01, 0x02, 0x04],
            '_': [0x40, 0x40, 0x40, 0x40, 0x40],
            '`': [0x00, 0x01, 0x02, 0x04, 0x00],
            'a': [0x20, 0x54, 0x54, 0x54, 0x78],
            'b': [0x7F, 0x48, 0x44, 0x44, 0x38],
            'c': [0x38, 0x44, 0x44, 0x44, 0x20],
            'd': [0x38, 0x44, 0x44, 0x48, 0x7F],
            'e': [0x38, 0x54, 0x54, 0x54, 0x18],
            'f': [0x08, 0x7E, 0x09, 0x01, 0x02],
            'g': [0x0C, 0x52, 0x52, 0x52, 0x3E],
            'h': [0x7F, 0x08, 0x04, 0x04, 0x78],
            'i': [0x00, 0x44, 0x7D, 0x40, 0x00],
            'j': [0x20, 0x40, 0x44, 0x3D, 0x00],
            'k': [0x7F, 0x10, 0x28, 0x44, 0x00],
            'l': [0x00, 0x41, 0x7F, 0x40, 0x00],
            'm': [0x7C, 0x04, 0x18, 0x04, 0x78],
            'n': [0x7C, 0x08, 0x04, 0x04, 0x78],
            'o': [0x38, 0x44, 0x44, 0x44, 0x38],
            'p': [0x7C, 0x14, 0x14, 0x14, 0x08],
            'q': [0x08, 0x14, 0x14, 0x18, 0x7C],
            'r': [0x7C, 0x08, 0x04, 0x04, 0x08],
            's': [0x48, 0x54, 0x54, 0x54, 0x20],
            't': [0x04, 0x3F, 0x44, 0x40, 0x20],
            'u': [0x3C, 0x40, 0x40, 0x20, 0x7C],
            'v': [0x1C, 0x20, 0x40, 0x20, 0x1C],
            'w': [0x3C, 0x40, 0x30, 0x40, 0x3C],
            'x': [0x44, 0x28, 0x10, 0x28, 0x44],
            'y': [0x0C, 0x50, 0x50, 0x50, 0x3C],
            'z': [0x44, 0x64, 0x54, 0x4C, 0x44],
        }

        # Clear the buffer
        self.erase_all()

        # Go through each character in the text
        current_col = col
        for char in text:
            if char in font:
                char_pattern = font[char]
                for i, pattern in enumerate(char_pattern):
                    if current_col < self.columns:
                        # Each font character is 5 columns wide
                        # Each column is a byte where each bit represents a row
                        for row_idx in range(7):  # 7 rows in font
                            if pattern & (1 << row_idx):
                                self.set_dot(current_col, row + row_idx, True)
                    current_col += 1

                # Add a space between characters
                current_col += 1
            else:
                # Skip unknown characters
                current_col += 6

    def toggle_orientation(self):
        """Toggle the display orientation between normal and flipped"""
        self.flip_orientation = not self.flip_orientation
        if self.debug:
            print(f"Orientation flipped: {self.flip_orientation}")

        # The changes will be applied on next set_dot, write_text, etc.

    def set_speed_factor(self, speed_factor):
        """Set the speed factor for animations"""
        if speed_factor <= 0:
            print("Speed factor must be positive, using 0.05")
            self.speed_factor = 0.05
        else:
            self.speed_factor = speed_factor
        if self.debug:
            print(f"Speed factor set to {self.speed_factor:.2f}")

    def get_speed_factor(self):
        """Get the current speed factor"""
        return self.speed_factor

    def adjust_delay(self, delay):
        """Adjust a delay value based on the current speed factor"""
        return delay * self.speed_factor