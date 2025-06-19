# Arrowhead Overlay for Raspberry Pi

This application serves as an Arrowhead overlay for the **Optic barrier** of [f1tenth-scoreapp](https://github.com/CTU-IIG/f1tenth-scoreapp) race measuring system.

It works in three modes:


a. **Scoreapp compatible mode**, "FindServer"

In this mode the overlay establishes a communication with the Arrowhead Core to find an active `scoreapp` provider (which is created by the backend's Arrowhead overlay).

The `scoreapp` Service has following metadata:
- `authorization` -- secret keyphrase for authorizing the barrier (it is used by the barrier to authorize itself with the scoreapp)
- `endpoint_X` -- available endpoint for the barrier to connect to

_Note: The amount of endpoints is not limited. Each parameter starting with `endpoint_` should be treated as an endpoint option._


b. **Lap time provider**, "ProvideLap"

In this mode the overlay register itself to the Arrowhead Core as a `laptime` provider. Any authorized consumers may then receive the current lap time from this barrier.

The `laptime` Service has following metadata:
- `address` -- preferred IP address of the barrier


c. **Offline mode**, "Local only"

In this mode the overlay does not communicate with the Arrowhead Core and starts the barrier software without any external communication.


## Requirements
- `f1tenth-scoreapp` cloned to `~/f1tenth-scoreapp`
  - GitHub: [https://github.com/CTU-IIG/f1tenth-scoreapp](https://github.com/CTU-IIG/f1tenth-scoreapp)
- `adafruit_circuitpython_ssd1305`
  - `python3 -m pip install adafruit_circuitpython_ssd1305`
- `aclpy >= 0.2.0`
  - GitHub: [https://github.com/CTU-IIG/ah-acl-py](https://github.com/CTU-IIG/ah-acl-py)
  - Wheel: [v0.2.0](https://github.com/jara001/ah-acl-py/releases/download/v0.2.0/aclpy-0.2.0-py3-none-any.whl)
- `python3-pil`
  - `sudo apt install python3-pil`
- `RPi.GPIO`
  - `python3 -m pip install RPi.GPIO`

_Note: For generating the screen images, you can install only `python3-pil` and `adafruit_circuitpython_framebuf`._


## Starting up

1. Compile the barrier software in `~/f1tenth-scoreapp/barrier/optic_barrier_sw/`.
2. Copy the binary to `~/optic_barrier_sw_ah`.
3. Obtain certificates (`.p12`, `.pub`) for your system from your local Arrowhead Core.
4. Obtain also the certificate authority `.ca` for your cloud.
5. Create a configuration file `ahconf.py`.
6. Run the `overlay.py3`.


### Configuration example

```python
Server = ArrowheadServer(
    address = "192.168.1.22",
)

Interface = ArrowheadInterface(
    name = "HTTP-INSECURE-JSON",
)

Service = ArrowheadService(
    name = "scoreapp",
)

ProvidedService = ArrowheadService(
    name = "laptime",
    metadata = {
        "address": "192.168.12.22",
    },
)

Client = ArrowheadClient(
    name = "raspberry",
    address = "192.168.12.22",
    port = 10110,
    p12file = "raspberry.p12",
    p12pass = "SomeSecurePassword",
    cafile = "authority.ca",
    server = Server,
    interfaces = [Interface],
)
```

### Systemd service definition

The overlay is meant to run all the time on the Raspberry Pi. This can be acheived by creating a systemd service. An example of such configuration is shown below:

_Note: In the overlay we expect that the service restarts itself upon exiting the overlay. This behaviour is used for updating the code._

```
[Unit]
Description=Arrowhead Overlay for Optic Barrier
Wants=network-online.target
After=network.target network-online.target

[Service]
Type=simple
WorkingDirectory=/home/pi/ah-overlay
ExecStart=python3 overlay.py3
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=basic.target
```


## Controls

The overlay is controlled by three buttons:
- `OK` connected to GPIO 21,
- `LEFT` connected to GPIO 19,
- `RIGHT` connected to GPIO 26.


## Modes

The overlay currently works in three modes (selected by the user):
1. "FindServer" -- where it looks for a provider of `scoreapp` service,
2. "ProvideLap" -- where it register itself as a provider of `laptime` service,
3. "Local only" -- where it skips Arrowhead related stuff and runs without an active connection.


## Application behaviour

### Loading
Upon starting, the overlay loads all required libraries and creates necessary variables. During this, the screen shows loading status:

![Arrowhead Overlay Loading...](./doc/screen_loading.bmp)

### Updating overlay
At first the overlay checks this repository for updates of the overlay. When changes are found, the repository is pulled and the overlay is restarted:

![Arrowhead Overlay Updating...](./doc/screen_updating.bmp)
![Arrowhead Overlay Restarting...](./doc/screen_restarting.bmp)

_Note: Actually, the application exits. We expect that it is restarted by the system itself._

### Updating barrier software
The same applies for repository of the barrier software. Upon finding new commits, the barrier application is rebuilt and the resulting binary is moved to an appropriate location:

![Arrowhead Overlay Updating SW...](./doc/screen_updating_sw.bmp)
![Arrowhead Overlay Building...](./doc/screen_building.bmp)
![Arrowhead Overlay Updating binary...](./doc/screen_updating_binary.bmp)
![Arrowhead Overlay Restarting...](./doc/screen_restarting.bmp)

_Note: In case that anything fails, following screen is shown before restart. As a design by-product, the building phase is not attempted again unless a new update is found._

![Arrowhead Overlay Building failed...](./doc/screen_building_failed.bmp)

### Arrowhead Discovery
Afterwards the overlay tries to communicate with Arrowhead Core, obtaining its system ID:

![Arrowhead Overlay Obtaining ID...](./doc/screen_obtaining_id.bmp)

Upon success, received system ID is briefly shown:

![Arrowhead Overlay ID: 7](./doc/screen_discovery_success.bmp)

On the other hand, when this step fails, it is displayed to the user and the overlay switches to a limited operation mode.

![Arrowhead Overlay << Failed >>](./doc/screen__failed_.bmp)

### Main Menu
In case that ID is successfully received from Arrowhead Core, main menu is shown. Here, the user can select operation mode using `LEFT` and `RIGHT` buttons, confirming the choice with `OK` button:

![Arrowhead Overlay Select mode: 5 < FindServer >...](./doc/screen_findserver_with_countdown.bmp)
![Arrowhead Overlay Select mode: 5 < ProvideLap >...](./doc/screen__providelap_.bmp)
![Arrowhead Overlay Select mode: 5 < Local only >...](./doc/screen__local_only_.bmp)
![Arrowhead Overlay Select mode: 5 <  bfed32c   >...](./doc/screen_githash.bmp)

_Note: The last menu item shows the short hash of current git commit._

_Note: When Arrowhead Core is not available, "FindServer" is not available._

In its default state the overlay automatically selects the first displayed menu item in 5 seconds. This countdown is stopped upon pressing one of the buttons, hiding the remaining time:

![Arrowhead Overlay Select mode: < FindServer >...](./doc/screen__findserver_.bmp)

#### Find Server
When "FindServer" mode is selected, the overlay tries to find appropriate providers using orchestration mechanism in the Arrowhead Core. This is indicated by the following screen:

![Arrowhead Overlay Finding host...](./doc/screen_finding_host.bmp)

Orchestration is repeated every 5 seconds. In case that orchestration fails (i.e., the overlay is unable to communicate with Orchestrator), a screen with overlay's system ID and 'O.fail' is shown:

![Arrowhead Overlay ID: 7 O.fail](./doc/screen_orch_failed.bmp)

Upon receiving valid provider, barrier software is launched with websocat that sends lap time to the remote server.

_Note: It is possible to turn into the "Local only" mode by holding the `RIGHT` button._

##### Multiple providers
When multiple providers are received using orchestration a small menu is shown for the user to select one:

![Arrowhead Overlay Use provider: <  scoreapp  >](./doc/screen_select_provider.bmp)

The controls are the same as for the main menu.

##### Multiple endpoints
When multiple endpoints on the selected provider are found, another menu is shown:

![Arrowhead Overlay Select endp: < barrier/1  >](./doc/screen_select_endpoint.bmp)

The controls are again the same as for the main menu.

#### Provide Lap time
When "ProvideLap" mode is selected, the overlay register itself to the Arrowhead Core as service provider:

![Arrowhead Overlay Provider mode](./doc/screen_provider_mode.bmp)

When successful, IDs of the overlay, service and selected interface are shown:

![Arrowhead Overlay P:7 I:2 S:16](./doc/screen_provider_ids.bmp)

In contrast, when "ProvideLap" is selected without the Arrowhead Core available, port of the created websocket is shown:

![Arrowhead Overlay Port: 1234](./doc/screen_provider_port.bmp)

Upon pressing `OK` button, the barrier software is launched. As an active connection is required to start the software, it is temporarily launched locally. Meantime, the following screen is shown:

![Arrowhead Overlay Awaiting conn](./doc/screen_awaiting_conn.bmp)

_Note: This active connection is a limitation of the used websocat. It is not possible to launch the application right away._

### Exiting the overlay
When the overlay exits, it removes itself from the Arrowhead service providers (if registered). Before turning self off, the overlay shows a simple bye:

![Arrowhead Overlay Bye!](./doc/screen_bye.bmp)

Afterwards, the screen is cleared.
