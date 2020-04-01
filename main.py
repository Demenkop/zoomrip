import json
import logging
import re
from base64 import b64encode

import trio
from halo import Halo
from loguru import logger

from constants import url_re
from exceptions import WrongPasswordError
from zoom import Zoom

logging.disable(logging.CRITICAL)
logger.add("file_{time}.log", enqueue=True)


async def spam(meeting_id: int, password: str, username: str, message: str, url: str):
    """
    Спамит сообщениями в чат

    :param meeting_id: номер конфернции
    :param password: пароль конфы
    :param username: ник бота
    :param message: сообщение
    :param url: ссылка на конференцию
    """
    zoom = Zoom(url, username)
    logger.debug(f"Joining conference {meeting_id} with password {password}")

    meeting = await zoom.join_meeting(meeting_id, password)

    async with meeting as ws:
        logger.info(f"{username}: Started sending messages...")
        while True:
            try:
                await ws.get_message()
                text = b64encode(message.encode()).decode()
                await ws.send_message(
                    json.dumps(
                        {"evt": 4135, "body": {"text": text, "destNodeID": 0}, "seq": 0}
                    )
                )
            except WrongPasswordError:
                logger.warning("Server says wrong password, ignoring...")
                pass



async def main():
    url = "https://us04web.zoom.us/j/9911729346?pwd=VGEvcnBUcHMrcTR3ZUVGeVFHa3ZOZz09"

    username = "AXAXAXSSSSSS"
    bot_count = 15
    message = "AXAXAXAAXX"

    url_parsed = re.findall(url_re, url)
    if len(url_parsed) == 0:
        logger.error("Неверная ссылка!")
        return

    meeting_id = url_parsed[0][1]
    if url_parsed[0][2] == "":
        password = ""
    else:
        password = url_parsed[0][3]

    logger.debug(repr(url_parsed))

    spinner = Halo(text="бомбим...", spinner="dots")
    spinner.start()

    async with trio.open_nursery() as nur:
        for i in range(1, bot_count + 1):
            nur.start_soon(spam, int(meeting_id), password, username + str(i), message, url)


trio.run(main)
