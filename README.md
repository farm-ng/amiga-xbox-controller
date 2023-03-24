# amiga-xbox-controller

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

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Run the script:

```bash
python main.py --host 192.168.1.98 --port 50060
```
