import re
from typing import Optional, Tuple

import httpx
import websockets

from constants import auth_re, ts_re
from exceptions import WrongPasswordError

from loguru import logger


class Zoom:
    def __init__(self, url, username: str):
        self.username = username
        self.host = "/".join(url.split("/")[:3])

        self.client = httpx.AsyncClient(verify=False)

    async def join_meeting(
        self, meeting_id: int, password: Optional[str] = ""
    ) -> Optional[websockets.client.Connect]:
        logger.enable("zoomrip")
        logger.debug("Joining a meeting")
        self.client.cookies.set("wc_join", f"{meeting_id}*{self.username}")
        self.client.cookies.set("wc_dn", self.username)

        configuration = await self._get_configuration(meeting_id, password)

        if configuration is None:
            logger.error("Wrong password")
            raise WrongPasswordError("Wrong password")

        best_server = await self._find_best_server(meeting_id)
        connection = await self._connect(
            meeting_id, best_server, configuration, password
        )

        logger.disable("zoomrip")
        return await self._websocket_connect(connection)

    async def _get_configuration(self, meeting_id: int, password: str) -> Optional[str]:
        join_request = await self.client.get(
            f"{self.host}/wc/{meeting_id}/join",
            params={
                "pwd": password,
                "track_id": "",
                "jmf_code": "",
                "meeting_result": "",
            },
        )
        if ">Meeting password is wrong. Please re-enter." not in join_request.text:
            return join_request.text
        else:
            logger.error("Wrong password")
            raise WrongPasswordError("Wrong password")

    async def _find_best_server(self, meeting_id: int) -> dict:
        best_server = await self.client.get(
            f"https://rwcff.zoom.us/wc/ping/{meeting_id}"
        )
        return best_server.json()

    async def _connect(
        self,
        meeting_id: int,
        best_server: dict,
        configuration: str,
        password: Optional[str] = "",
    ):
        auth, ts = self._extract_config_variables(configuration)

        return await self.client.get(
            f"https://{best_server['rwg']}/webclient/{meeting_id}",
            params={
                "dn": self.username,
                "ts": ts,
                "auth": auth,
                "mpwd": password or "",
                "rwcAuth": best_server["rwcAuth"],
            },
        )

    @staticmethod
    async def _websocket_connect(connection) -> websockets.client.Connect:
        return websockets.connect(str(connection.url).replace("https", "wss"))

    @staticmethod
    def _extract_config_variables(configuration: str) -> Tuple[str, str]:
        auth = re.search(auth_re, configuration).group(1)
        ts = re.search(ts_re, configuration).group(1)
        return auth, ts
