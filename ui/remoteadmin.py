import asyncio
import json
import jsonpatch
import websockets

from server.network.proto import admin_pb2

class RemoteAdmin:
    def __init__(self, log_handler=None):
        self.conn = None
        self.future: asyncio.Future = None
        self.log_handler = log_handler

    async def _handler(self):
        async for msg in self.conn:
            req = admin_pb2.ServerMessage().ParseFromString(msg)
            header = req.WhichOneof('msg')
            if header == 'opts':
                self.future.set_result(json.loads(req.opts.options))
            elif header == 'set_opt_result':
                if req.set_opt_result.error:
                    error_msg = req.set_opt_result.message
                    self.future.set_exception(Exception(error_msg))
                else:
                    self.future.set_result(None)
            elif header == 'log_entry':
                self.log_handler(req.log_entry.message)

    async def get_opts(self):
        req = admin_pb2.ClientMessage()
        req.get_opts.SetInParent()
        await self.conn.send(req.SerializeToString())
        self.future = asyncio.Future()
        return await self.future

    async def connect(self, uri):
        print(f'Connecting to {uri}...')
        self.conn = await websockets.connect(uri)
        print(f'Connected to {uri}')
        asyncio.ensure_future(self._handler())