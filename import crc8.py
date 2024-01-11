def generate_crc8_table():
    crc8_lut = [0] * 256
    polynomial = 0x07  # CRC8 polynomial (0x07 for CRC-8-CCITT)
    for dividend in range(256):
        remainder = dividend << 8
        for _ in range(8):
            if remainder & 0x8000:
                remainder = (remainder << 1) ^ polynomial
            else:
                remainder = (remainder << 1)
        crc8_lut[dividend] = remainder & 0xFF
    return crc8_lut

def calculate_crc8(data, crc_table):
    crc = 0xFF
    for byte in data:
        crc = crc_table[byte ^ crc]
    return crc ^ 0x70  # Final XOR value

# Usage example:
crc_table = generate_crc8_table()
input_data = bytes([0xe6, 0xf6, 0xfe, 0xff, 0x14])  # Input your sequence of bytes here

crc8_result = calculate_crc8(input_data, crc_table)
print(f"CRC8 checksum: 0x{crc8_result:02X}")
