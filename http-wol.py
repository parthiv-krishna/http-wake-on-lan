import argparse
import json
import logging
import re
import socket

import flask
import requests

app = flask.Flask(__name__)
logging.basicConfig(level=logging.INFO)

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


def check_service_awake(status_url: str) -> bool:
    try:
        _ = requests.get(status_url, timeout=1)
        # return true if we get any response
        return True
    except requests.exceptions.Timeout:
        # return false if timed out
        return False

def get_machine_from_host(host: str) -> str:
    for service, machine in app.config["services"].items():
        if re.match(f"^{service}$", host):
            return machine
    return None


@app.route("/wol", methods=["GET", "POST"])
def wol():
    # ensure we have a valid host header
    if "Host" not in flask.request.headers:
        errmsg = "No Host header found. Not sending WOL packet."
        logging.warning(errmsg)
        return errmsg, 400

    # determine the machine to wake up
    machine = get_machine_from_host(flask.request.headers["Host"])
    if machine is None:
        errmsg = f"Host {flask.request.headers['Host']} not in services. Not sending WOL packet."
        logging.warning(errmsg)
        return errmsg, 404

    # send the WOL packet until the service is awake
    awake = False
    while not awake:
        logging.info(f"Sending WOL packet to {machine}")
        send_wake_on_lan(
            app.config["machines"][machine]["mac"],
            app.config["machines"][machine]["broadcast_ip"],
        )
        awake = check_service_awake(app.config["machines"][machine]["status_url"])

    logging.info(f"Woke up {machine}")
    return f"Woke up {machine}", 200


def main():
    args = argparse.ArgumentParser()
    args.add_argument(
        "--config",
        type=str,
        required=False,
        default="config.json",
        help="Path to the configuration file",
    )
    args = args.parse_args()

    with open(args.config, "r") as f:
        config = json.load(f)
        app.config.update(config)

    app.run(host="0.0.0.0", port=301)


if __name__ == "__main__":
    main()
