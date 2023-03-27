# Copyright (c) farm-ng, inc.
#
# Licensed under the Amiga Development Kit License (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://github.com/farm-ng/amiga-dev-kit/blob/main/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

import argparse
import asyncio
import logging
from multiprocessing import Process
from multiprocessing import Queue

import pygame
from farm_ng.canbus import canbus_pb2
from farm_ng.canbus.canbus_client import CanbusClient
from farm_ng.service.service_client import ClientConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class XboxController:
    """This class is used to get input from an xbox controller."""

    def __init__(self, device_id: int = 0) -> None:
        """Initialize the xbox controller.

        Args:
            device_id: the device id of the xbox controller. This is usually 0.
        """
        # the queue is used to share messages between the pygame process and the asyncio loop
        self.command_queue = Queue(maxsize=10)

        # start the pygame process
        self.process = Process(
            target=self.loop_pygame, args=(device_id, self.command_queue)
        )
        self.process.start()  # start the subprocess

    def loop_pygame(self, device_id: int, queue: Queue) -> None:
        """This function is run in a subprocess to get input from the xbox controller.

        Args:
            device_id: the device id of the xbox controller.  This is usually 0.
            queue: the queue to put the messages in.
        """
        # initialize the pygame joystick module
        pygame.init()

        clock = pygame.time.Clock()

        # make sure the xbox controller is detected, otherwise raise an error
        assert pygame.joystick.get_count() > 0, "No joysticks detected"

        # initialize the xbox controller with the given device id
        joystick = pygame.joystick.Joystick(device_id)
        joystick.init()

        logger.info(f"Detected joystick {joystick.get_name()}")

        while True:
            # NOTE: this seems to be necessary to keep the pygame event queue
            for _ in pygame.event.get():
                pass

            # axis 1 is left stick up/down
            axis_linear: float = joystick.get_axis(1)
            axis_angular: float = joystick.get_axis(3)

            # create a twist data structure from the joystick input
            # NOTE: the joystick input is inverted, so we need to invert the linear velocity
            twist_command = canbus_pb2.Twist2d(
                linear_velocity_x=-axis_linear,
                linear_velocity_y=0.0,
                angular_velocity=-axis_angular,
            )

            # put the twist command in the queue
            queue.put(twist_command)

            # tick the clock at 60hz
            clock.tick(60)


class AmigaXboxControllerClient:
    """This class is used to get input from an xbox controller and send it to the canbus service."""

    def __init__(self, host: str, port: int) -> None:
        """Initialize the xbox controller client and the canbus client.

        Args:
            host: the host of the canbus service.
            port: the port of the canbus service.
        """
        # this is used to get input from the xbox controller
        self.xbox_controller = XboxController()

        # this is used to send messages to the canbus service
        self.canbus_client = CanbusClient(ClientConfig(address=host, port=port))

    async def request_generator(
        self,
    ) -> iter[canbus_pb2.SendVehicleTwistCommandRequest]:
        """This function is used to generate the vehicle twist commands to send to the canbus service."""
        while True:
            twist_command: canbus_pb2.Twist2d = self.xbox_controller.command_queue.get()
            yield canbus_pb2.SendVehicleTwistCommandRequest(command=twist_command)

    async def run(self) -> None:
        """This function is used to run the asyncio loop to send the vehicle twist commands to the canbus
        service."""
        # generator function to send vehicle twist commands
        stream = self.canbus_client.stub.sendVehicleTwistCommand(
            self.request_generator()
        )

        # iterate over the stream to send the commands and receive the twist states
        twist_state: canbus_pb2.Twist2d
        async for twist_state in stream:
            # print(twist_state)
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="amiga-xbox-controller-client")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default=50060)
    args = parser.parse_args()

    # create the amiga controller client with the xbox controller input
    controller_client = AmigaXboxControllerClient(args.host, args.port)

    # run the asyncio loop
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(controller_client.run())
    except KeyboardInterrupt:
        logger.info("Exiting by KeyboardInterrupt ...")
    finally:
        loop.close()
