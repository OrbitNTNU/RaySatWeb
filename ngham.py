START_BYTE = 0x24


def ngh_ext_decode_callsign(enc_callsign: list) -> dict:
    """
        Decode NGHAM spp rx callsign packet
        Input: callsign packet (list of bytes) containing only the 'Data' section
        Output: dictionary with decoded callsign and sequence number
    """
    # Extract first 6 bytes to decode the callsign
    temp = (enc_callsign[0] << 16) | (enc_callsign[1] << 8) | enc_callsign[2]
    callsign = [
        (temp >> 18) & 0x3F,
        (temp >> 12) & 0x3F,
        (temp >> 6) & 0x3F,
        temp & 0x3F,
    ]

    temp = (enc_callsign[3] << 16) | (enc_callsign[4] << 8) | enc_callsign[5]
    callsign.extend([
        (temp >> 18) & 0x3F,
        (temp >> 12) & 0x3F,
        (temp >> 6) & 0x3F,
    ])

    # Convert callsign values to characters
    callsign = ''.join(chr(c + 32) for c in callsign).strip()

    # Extract SSID (6 bits from last processed byte)
    ssid = temp & 0x3F
    if ssid:
        callsign += f"-{ssid}"

    # Extract sequence number (last byte)
    sequence_number = enc_callsign[6]  

    return {"callsign": callsign, "sequence_number": sequence_number}


def ngh_ext_decode_stat(stat: list) -> dict:
    """
        Decode NGHAM spp rx stat packet
        Input: stat packet (list of bytes)
        Output: decoded stat (dict)
    """
    # Hardware version 10b company, 6b product
    hw_ver = stat[0:2]
    hw_ver_value = (hw_ver[1] << 8) | hw_ver[0]  # little-endian
    company_id = (hw_ver_value >> 6) & 0x3FF
    product_id = hw_ver_value & 0x3F
    hw_ver_str = f"{company_id}/{product_id}"

    # Serial number
    serial = stat[2:4]
    serial_number = (serial[1] << 8) | serial[0]  # little-endian

    # Software version 4b major, 4b minor, 8b build
    sw_ver = stat[4:6]
    major_version = sw_ver[0] >> 4
    minor_version = sw_ver[1]
    build_version = sw_ver[0] & 0x0F
    sw_version_str = f"{major_version}.{minor_version}.{build_version}"

    # Uptime in seconds since startup
    uptime_s = stat[6:10]
    uptime_seconds = uptime_s[0] | (uptime_s[1] << 8) | (uptime_s[2] << 16) | (uptime_s[3] << 24)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours:02}:{minutes:02}:{seconds:02}"

    voltage = stat[10]
    voltage = voltage / 10

    temp = stat[11]

    # Signal offset by 200 in dBm
    signal = stat[12]
    signal = signal - 200

    # Noise offset by 200 in dBm
    noise = stat[13]
    noise = noise - 200

    cntr_rx_ok = int.from_bytes(stat[14:16], byteorder='little')
    cntr_rx_fix = int.from_bytes(stat[16:18], byteorder='little')
    cntr_rx_err = int.from_bytes(stat[18:20], byteorder='little')
    cntr_tx = int.from_bytes(stat[20:22], byteorder='little')

    return {
        "hw_ver": hw_ver_str,
        "serial": serial_number,
        "sw_ver": sw_version_str,
        "uptime H:M:S": uptime_str,
        "voltage V": voltage,
        "temp C": temp,
        "signal dBm": signal,
        "noise dBm": noise,
        "cntr_rx_ok": cntr_rx_ok,
        "cntr_rx_fix": cntr_rx_fix,
        "cntr_rx_err": cntr_rx_err,
        "cntr_tx": cntr_tx,
    }

def ngh_ext_decode_position(position: list) -> dict:
    """
        Decode NGHAM spp rx position packet
        Input: position packet (list of bytes)
        Output: decoded position (dict)
    """
    lat = position[0:4]
    lon = position[4:8]
    alt = position[8:12]

    sog = position[12:14] # hundreds of meters per second
    sog = sog * 100

    cog = position[14:16] # tenths of degrees
    cog = cog / 10

    hdop = position[16] # tenths
    hdop = hdop / 10

    return {
        "lat": lat,
        "lon": lon,
        "alt": alt,
        "sog m/s": sog,
        "cog deg": cog,
        "hdop deg": hdop
    }

def decode_time_of_hour(bytes_array: list) -> str:
    """
        Decode time of hour in microseconds. Wraps around after one hour.
        Input: bytes_array (list of bytes)
        Output: time_of_hour M:S.milliseconds (str) or None if invalid timestamp
    """
    toh_us = int.from_bytes(bytes_array, byteorder='little')

    if toh_us == 0xFFFFFFFF:
        print("Invalid timestamp (0xFFFFFFFF), skipping...")
        return None

    seconds_in_hour = toh_us // 1_000_000
    microseconds_in_hour = toh_us % 1_000_000
    
    minutes = seconds_in_hour // 60
    seconds = seconds_in_hour % 60
    
    time_of_hour = f"{minutes:02}:{seconds:02}.{microseconds_in_hour:06d}"

    return time_of_hour


def decode_ngham_spp_packet_rx_payloads(payload: list) -> list:
    """
        Decodes NGHAM SPP RX packet payloads
        Input: spp rx payloads (list of bytes)
        Output: decoded spp rx payloads (list of dicts)
    """
    decoded_payloads = []
    i = 0
    while i < len(payload):
        packet_type = payload[i]
        payload_length = payload[i + 1]
        
        packet_data = payload[i + 2 : i + 2 + payload_length]

        if packet_type == 0:
            decoded_payloads.append({"type": "Data", "data": packet_data})
        elif packet_type == 1:
            decoded_callsign = ngh_ext_decode_callsign(packet_data)
            decoded_payloads.append({"type": "SRC", "data": decoded_callsign})
        elif packet_type == 2:
            decoded_stat = ngh_ext_decode_stat(packet_data)
            decoded_payloads.append({"type": "Stat", "data": decoded_stat})
        elif packet_type == 3:
            decoded_payloads.append({"type": "Simple Digi", "data": packet_data})
        elif packet_type == 4:
            decoded_position = ngh_ext_decode_position(packet_data)
            decoded_payloads.append({"type": "Position", "data": decoded_position})
        elif packet_type == 5:
            decoded_payloads.append({"type": "Time of Hour", "data": packet_data})
        elif packet_type == 6:
            decoded_payloads.append({"type": "Destination", "data": packet_data})
        elif packet_type == 7:
            decoded_payloads.append({"type": "Command Request", "data": packet_data})
        elif packet_type == 8:
            decoded_payloads.append({"type": "Command Reply", "data": packet_data})
        elif packet_type == 9:
            decoded_payloads.append({"type": "Request", "data": packet_data})
        else:
            decoded_payloads.append({"type": "Unknown", "data": packet_data})

        i += 2 + payload_length
    return decoded_payloads

def decode_ngham_spp_packet_rx_sensor_data(payload: list) -> dict:
    """
        Decodes NGHAM SPP RX packet sensor data (as defined by SO 2025)
        Input: spp rx sensor data (list of bytes)
        Output: decoded spp rx sensor data (dict)
    """
    payload_txt = ''.join(chr(c) for c in payload)

    fields = payload_txt.strip().split(';')

    if len(fields) < 1:
        return {"type": "text", "len": len(payload), "msg": payload_txt}
    elif len(fields) == 1:
        return {"type": "text", "len": len(payload), "msg": fields[0]}
    else:
        return {
            "type": "text",
            "len": len(payload),
            "data": payload_txt,
            "msg": fields[0],
            "sensor_data": fields[1:]
        }


def decode_ngham_spp_packet_rx(payload: list) -> dict:
    """
        Decodes NGHAM SPP RX packet
        Input: spp payload (list of bytes)
        Output: decoded spp payload packet (dict)
    """
    decoded_packet = {}

    # timestamp_toh_us uint32_t 
    timestamp_toh_us = payload[0:4]
    decoded_timestamp = decode_time_of_hour(timestamp_toh_us)
    decoded_packet['timestamp_toh_us'] = decoded_timestamp

    # noise uint8_t
    noise = payload[4]
    decoded_packet['noise dBm'] = noise - 200

    # rssi uint8_t
    rssi = payload[5]
    decoded_packet['rssi dBm'] = rssi - 200

    # errors uint8_t
    errors = payload[6]
    decoded_packet['errors'] = errors

    # ngham_flags uint8_t
    ngham_flags = payload[7]
    decoded_packet['ngham_flags'] = hex(ngham_flags)

    payload = payload[8:]

    # payloads
    if ngham_flags == 0x01:
        decoded_packet['rx_payloads'] = decode_ngham_spp_packet_rx_payloads(payload)
    else:
        decoded_packet['rx_payloads'] = decode_ngham_spp_packet_rx_sensor_data(payload)

    return decoded_packet


def decode_ngham_spp_packet_tx(payload):
    # TODO: Implement
    return


def decode_ngham_spp_header_only(header):
    """
        Decodes NGHAM SPP header
        Input: header (list of bytes)
        Output: decoded header
    """
    start_byte = header[0]
    if start_byte != START_BYTE:
        print("Invalid start byte!")
        return None
    crc = int.from_bytes(header[1:3], byteorder='big') # TODO: Check CRC
    spp_pl_type = header[3]
    pl_len = header[4]

    return start_byte, crc, spp_pl_type, pl_len


def decode_ngham_spp_header(packet: list):
    """
        Decodes NGHAM SPP header including payload separation
        Input: whole packet (list of bytes)
        Output: decoded header
    """
    header = packet[0:5]
    start_byte, crc, spp_pl_type, pl_len = decode_ngham_spp_header_only(header)
    
    payload = packet[5:5+pl_len]

    return start_byte, crc, spp_pl_type, pl_len, payload


def decode_ngham_spp_packet(packet: list) -> dict:
    """
        Decodes NGHAM SPP packet
        Input: whole packet (list of bytes)
        Output: decoded packet (dict)
    """
    decoded_packet = {}
    
    spp_start, spp_crc, spp_pl_type, spp_pl_len, payload = decode_ngham_spp_header(packet)

    decoded_packet["header"] = {
        "start_byte": hex(spp_start),
        "crc": hex(spp_crc),
        "pl_type": spp_pl_type,
        "pl_len": spp_pl_len
    }

    if spp_pl_type == 0x00:
        decoded_packet["spp_payload"] = {"type": "RX", "data": decode_ngham_spp_packet_rx(payload)}
    elif spp_pl_type == 0x01:
        decoded_packet["spp_payload"] = {"type": "TX", "data": payload}
    elif spp_pl_type == 0x02:
        decoded_packet["spp_payload"] = {"type": "LOCAL", "data": payload}
    elif spp_pl_type == 0x03:
        decoded_packet["spp_payload"] = {"type": "CMD", "data": payload}
    else:
        print("Unknown packet type")

    return decoded_packet