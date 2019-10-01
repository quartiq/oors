import asyncio
import enum
import sys
import os
import logging

from oors.menlosystemcore import MenloSystemCore

logger = logging.getLogger(__name__)


class OORS(MenloSystemCore):
    def get(self, path):
        v = self
        for elem in path.split("."):
            v = getattr(v, elem)
        return v

    def set(self, path, value):
        path, elem = path.rsplit(".", 1)
        return setattr(self.get(path), elem, value)

    async def call(self, path, *args, **kwargs):
        return await self.get(path)(*args, **kwargs)

    async def misc(self):
        logger.info("identity %s", self.identity)
        # for i in await self.log.readLog(10):
        #     self._cb_log(i)
        self.log.logMessageReceived.connect(self._cb_log)

    def _cb_log(self, msg):
        logger.info("log message: %s", msg)
