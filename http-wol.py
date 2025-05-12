import argparse
import flask
import json
import socket

app = flask.Flask(__name__)

def send_wake_on_lan(mac: str, broadcast_ip: str, port: int = 9) -> None:
    """
    Send a Wake-on-LAN (WOL) magic packet to the specified MAC address.

    Args:
        mac: MAC address in any common format (xx:xx:xx:xx:xx:xx, xx-xx-xx-xx-xx-xx, etc.)
        broadcast_ip: Broadcast IP address for the target network (e.g., '255.255.255.255')
        port: Port to send the WOL packet to (default is 9)

    Raises:
        ValueError: If invalid MAC address format is provided
    """
    # Normalize MAC address format
    mac_bytes = mac.strip().replace(":", "").replace("-", "").replace(".", "")

    # Validate MAC address length
    if len(mac_bytes) != 12:
        raise ValueError(f"Invalid MAC address: {mac}")

    try:
        # Convert MAC to bytes and construct magic packet
        mac_data = bytes.fromhex(mac_bytes)
        magic_packet = b"\xff" * 6 + mac_data * 16

        # Create and configure UDP socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(magic_packet, (broadcast_ip, port))

    except ValueError as e:
        raise ValueError(f"Invalid MAC address format: {mac}") from e

@app.route("/wol", methods=["GET", "POST"])
def wol():
    # testing
    print(app.config)
    print("Host: ", flask.request.headers["Host"])
    
    # For ForwardAuth middleware, return 2xx status to allow the request to proceed
    return "", 200


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--config", type=str, required=False, default="config.json", help="Path to the configuration file")
    args = args.parse_args()

    with open(args.config, "r") as f:
        config = json.load(f)
        app.config.update(config)

    app.run(host="0.0.0.0", port=301)


if __name__ == "__main__":
    main()
