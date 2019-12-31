import asyncio
import json
import jsonpatch
import websockets

from .proto import admin_pb2

class RemoteAdmin:
    def __init__(self, server):
        self.server = server
        self.clients = set()

    async def handler(self, ws: websockets.WebSocketServerProtocol, _path):
        self.clients.add(ws)
        try:
            async for msg in ws:
                req = admin_pb2.ClientMessage().ParseFromString(msg)
                header = req.WhichOneof('msg')
                res = admin_pb2.ServerMessage()
                if header == 'get_opts':
                    opts_json = json.dumps(self.server.config)
                    res.opts.options = opts_json
                elif header == 'set_opt':
                    try:
                        patch = json.loads(req.set_opt.json_patch)
                        jsonpatch.apply_patch(self.server.config, patch, in_place=True)
                        self.server.refresh()
                    except Exception as exc:
                        res.set_opt_result.error = True
                        res.set_opt_result.message = str(exc)
                await ws.send(res.SerializeToString())
        finally:
            self.clients.remove(ws)

    def send_log(self, line):
        for client in self.clients:
            packet = admin_pb2.LogEntry()
            packet.message = line
            asyncio.ensure_future(client.send(packet.SerializeToString()))

    async def serve(self, port):
        return await websockets.serve(self.handler, host='localhost', port=port)
