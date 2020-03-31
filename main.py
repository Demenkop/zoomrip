import asyncio
import json
import logging
import re
from base64 import b64encode

from halo import Halo

from constants import url_re
from zoom import Zoom

logging.disable(logging.CRITICAL)


async def spam(meeting_id: int, password: str, username: str, message: str):
    zoom = Zoom("https://us04web.zoom.us", username)
    meeting = await zoom.join_meeting(meeting_id, password)

    async with meeting as websocket:
        while True:
            await websocket.recv()
            text = b64encode(message.encode()).decode()
            await websocket.send(
                json.dumps(
                    {"evt": 4135, "body": {"text": text, "destNodeID": 0}, "seq": 0}
                )
            )


async def main():
    url = input("Введите ссылку на конференцию Zoom: ")

    username = input(
        "Введите юзернейм, который будет использован ботами (без русских букв): "
    )
    bot_count = int(input("Введите количество ботов: "))
    message = input("Введите сообщение, которое будут отправлять боты: ")

    url_parsed = re.findall(url_re, url)
    if len(url_parsed) == 0:
        print("Неверная ссылка!")
        return

    meeting_id = url_parsed[0][0]
    if url_parsed[0][1] == "":
        password = ""
    else:
        password = url_parsed[0][2]

    spinner = Halo(text="", spinner="dots")
    spinner.start()

    while True:
        try:
            joins = {
                spam(int(meeting_id), password, username, message)
                for _ in range(1, bot_count)
            }
            await asyncio.gather(*joins)
        except:
            pass


asyncio.get_event_loop().run_until_complete(main())
