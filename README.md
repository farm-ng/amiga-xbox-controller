# amiga-xbox-controller

## Prerequisites

- You need to have a Farm-ng Amiga Intellegince Kit: https://farm-ng.com/products/la-maquina-amiga
- Xbox Wireless Controller: https://www.amazon.es/Microsoft-Inal%C3%A1mbrico-Adaptador-inal%C3%A1mbrico-Windows/dp/B08JW5DR79

## Installation

1. Install system dependencies:

```bash
sudo apt install libusb-1.0-0-dev
```

2. Install xow: https://github.com/medusalix/xow#installation

3. Install amiga-xbox-controller:

```bash
python3 -m venv venv
source venv/bin/activate
```

4. Install python dependencies:

```bash
pip install -r requirements.txt
```

## Run the script

Make sure the xbox controller is connected to the computer and the amiga is connected to the same network.

```bash
python main.py --host 192.168.1.98 --port 50060
```

To finally drive tha amiga, for security reasons, you need to enable the auto control mode from the Amiga Dashboard interface.

Learn more about the Amiga Control States here: https://amiga.farm-ng.com/docs/dashboard/control-states#amiga-control-states
