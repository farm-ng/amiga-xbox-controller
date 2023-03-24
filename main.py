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
import argparse
import asyncio
import logging
from multiprocessing import Process, Queue

import pygame

from farm_ng.canbus import canbus_pb2
from farm_ng.canbus.canbus_client import CanbusClient
from farm_ng.service.service_client import ClientConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class XboxController:
    def __init__(self, host: str, port: int, device_id: int = 0) -> None:
        # the canbus client is used to send messages to the canbus service
        self.canbus_client = CanbusClient(ClientConfig(address=host, port=port))

        self.queue = Queue(10)

        self.process = Process(target=self.run_pygame, args=(device_id, self.queue))
        self.process.start()

    
    def run_pygame(self, device_id: int, queue: Queue) -> None:
        # initialize the pygame joystick module
        pygame.init()
        clock = pygame.time.Clock()

        assert pygame.joystick.get_count() > 0, "No joysticks detected"
        joystick = pygame.joystick.Joystick(device_id)
        joystick.init()
        print("Detected joystick '", joystick.get_name(), "'")

        scale_factor = 1.0

        while True:
            # NOTE: this seems to be necessary to keep the pygame event queue
            for _ in pygame.event.get():
                pass

            # axis 1 is left stick up/down
            axis_linear = joystick.get_axis(1)
            #print(f"left stick up/down: {axis_linear}")

            axis_angular = joystick.get_axis(3)
            #print(f"right stick left/right: {axis_angular}")

            twist_command=canbus_pb2.Twist2d(
                linear_velocity_x=-axis_linear * scale_factor,
                linear_velocity_y=0.0,
                angular_velocity=-axis_angular * scale_factor,
            )
            #print(f"run_pygame {twist_command}")
            #print(f"run_pygame {count}")
            #print("------------------------")
            queue.put(twist_command)

            # tick the clock at 60hz
            clock.tick(60)
    
    async def request_generator(self) -> None:
        while True:
            twist_command: canbus_pb2.Twist2d = self.queue.get()
            yield canbus_pb2.SendVehicleTwistCommandRequest(command=twist_command)

    async def run(self) -> None:
        # generator function to send vehicle twist commands
        stream = self.canbus_client.stub.sendVehicleTwistCommand(self.request_generator())

        async for twist_state in stream:
            #print(twist_state)
            pass

async def main(host: str, port: int) -> None:
    controller = XboxController(host=host, port=port)
    await asyncio.gather(controller.run())
    
    #await asyncio.gather(controller.run_pygame(), controller.run())
    #await asyncio.gather(controller.run_pygame())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="amiga-xbox-controller-client")
    #parser.add_argument('--host', default='localhost')
    parser.add_argument('--host', default='192.168.1.98')
    parser.add_argument('--port', default=50060)
    args = parser.parse_args()

    asyncio.run(main(args.host, args.port))