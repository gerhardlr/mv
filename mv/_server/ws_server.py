import asyncio
from queue import Queue
from websockets.server import serve

from mv.state_machine import state_server, AbstractPublisher,update_state

class Publisher(AbstractPublisher):
    def __init__(self) -> None:
        self._events = Queue[dict]()

    def publish(self, state):
        self._events.put_nowait(state)

    async def get_new_event(self):
        return await asyncio.to_thread(self._events.get)
    
def _set_state_on():
    with update_state() as state:
          state["state"] = "ON"

def _set_state_off():
    with update_state() as state:
          state["state"] = "OFF"
    
async def set_state_on():
    await asyncio.to_thread(_set_state_on)

async def set_state_off():
    await asyncio.to_thread(_set_state_off)
    

async def command_listener(websocket):
    async for command in websocket:
        if command == "ON":
            await set_state_on()
        elif command == "OFF":
            await set_state_off()

async def echo(websocket):
    async for message in websocket:
        await websocket.send(message)
        

async def state_machine(websocket):
    publisher = Publisher()
    with state_server(publisher):
        while (event := await publisher.get_new_event()):
            value = event["state"]
            await websocket.send(value)

async def server_routine(websocket):
    await asyncio.gather(state_machine(websocket),command_listener(websocket))



async def main():
    async with serve(server_routine, "localhost", 8000):
        await asyncio.Future()  # run forever

def server():
    asyncio.run(main())

if __name__ == "__main__":
    server()