"""Exercise the compiled client through a local TLS WebSocket TV, with dummy keys."""
import asyncio, base64, hashlib, json, ssl, struct, sys, tempfile
from pathlib import Path
import websockets

BINARY = str(Path(sys.argv[1]).resolve())

async def scenario(mode, tls, directory):
    complete = asyncio.get_running_loop().create_future()
    async def tv(ws):
        try:
            for ident in ('hello', 'sys', 'register'):
                m = json.loads(await asyncio.wait_for(ws.recv(), 3))
                assert m['id'] == ident and isinstance(m['payload'], dict), m
                if ident == 'register':
                    assert m['payload']['client-key'] == 'dummy-existing-key'
                await ws.send(json.dumps({'id':ident, 'type':'error' if mode == 'auth' and ident == 'register' else 'registered' if ident == 'register' else 'response'}))
            if mode == 'auth':
                complete.set_result(True)
                return
            m = json.loads(await asyncio.wait_for(ws.recv(), 3))
            assert m['type'] == 'subscribe' and m['uri'] == 'ssap://com.webos.applicationManager/getForegroundAppInfo'
            if mode == 'permission':
                await ws.send(json.dumps({'id':'foreground','type':'error'}))
                complete.set_result(True)
                return
            async def foreground(app):
                await ws.send(json.dumps({'id':'foreground','type':'response','payload':{'appId':app}}))
            async def quiet():
                try:
                    unexpected = await asyncio.wait_for(ws.recv(), .25)
                    raise AssertionError('unexpected TV command: '+unexpected)
                except asyncio.TimeoutError:
                    pass
            await foreground('com.webos.app.hdmi1')
            await quiet()
            await foreground('com.webos.app.home')
            if mode not in ('observe', 'heartbeat'):
                m = json.loads(await asyncio.wait_for(ws.recv(), 3))
                assert m == {'id':'launch','type':'request','uri':'ssap://system.launcher/launch','payload':{'id':'test.launcher'}}, m
                if mode == 'launch-permission':
                    await ws.send(json.dumps({'id':'launch','type':'error'}))
                    complete.set_result(True)
                    return
                await foreground('test.launcher')
                await foreground('com.webos.app.home')
            await quiet()
            if mode == 'redirect':
                # Escape clears the window: the next Home is allowed to launch again.
                await foreground('com.webos.app.hdmi1')
                await foreground('com.webos.app.home')
                m = json.loads(await asyncio.wait_for(ws.recv(), 3))
                assert m['uri'] == 'ssap://system.launcher/launch'
                await asyncio.sleep(3.1)
                await foreground('com.webos.app.home')
                m = json.loads(await asyncio.wait_for(ws.recv(), 3))
                assert m['uri'] == 'ssap://system.launcher/launch'
            if mode == 'heartbeat':
                await asyncio.sleep(16)
                pong = await ws.ping(b'server-health')
                await asyncio.wait_for(pong, 3)
                await quiet()
            complete.set_result(True)
            await ws.wait_closed()
        except BaseException as error:
            if not complete.done(): complete.set_exception(error)
    config = directory/'config.json'
    config.write_text(json.dumps({'host':'127.0.0.1','client_key':'dummy-existing-key','launcher_id':'test.launcher','registration':{'id':'register','type':'register','payload':{}}}))
    async with websockets.serve(tv, '127.0.0.1', 3001, ssl=tls, ping_interval=None):
        args = [BINARY] + (['--observe'] if mode in ('observe','heartbeat') else []) + [str(config)]
        process = await asyncio.create_subprocess_exec(*args, stderr=asyncio.subprocess.PIPE)
        try:
            await asyncio.wait_for(complete, 25)
            if mode in ('auth','permission','launch-permission'):
                assert await asyncio.wait_for(process.wait(), 3) == 77
            else:
                process.terminate()
                assert await asyncio.wait_for(process.wait(), 3) == 0
            logs = (await process.stderr.read()).decode()
            assert 'dummy-existing-key' not in logs
        finally:
            if process.returncode is None:
                process.kill()
                await process.wait()
    print('PASS', mode, flush=True)

async def heartbeat_timeout(tls, config):
    # Minimal RFC6455 peer deliberately ignores Ping, unlike websockets auto-pong.
    complete = asyncio.get_running_loop().create_future()
    async def peer(reader, writer):
        try:
            headers = (await reader.readuntil(b"\r\n\r\n")).decode()
            key = next(line.split(":",1)[1].strip() for line in headers.split("\r\n") if line.lower().startswith("sec-websocket-key:"))
            accept = base64.b64encode(hashlib.sha1((key+"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
            writer.write(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: "+accept+"\r\n\r\n").encode())
            await writer.drain()
            async def frame():
                head = await reader.readexactly(2)
                length = head[1] & 127
                if length == 126: length = struct.unpack("!H",await reader.readexactly(2))[0]
                if length == 127: length = struct.unpack("!Q",await reader.readexactly(8))[0]
                assert head[1] & 128
                mask = await reader.readexactly(4)
                body = await reader.readexactly(length)
                return head[0] & 15, bytes(v ^ mask[i%4] for i,v in enumerate(body))
            for ident in ('hello','sys','register','foreground'):
                opcode, raw = await asyncio.wait_for(frame(),3)
                message = json.loads(raw)
                assert opcode == 1 and message['id'] == ident
                body = json.dumps({'id':ident,'type':'registered' if ident == 'register' else 'response','payload':{}}).encode()
                assert len(body) < 126
                writer.write(bytes([0x81,len(body)])+body)
                await writer.drain()
            opcode, _ = await asyncio.wait_for(frame(),18)
            assert opcode == 9, 'Client did not send heartbeat Ping'
            # Ignoring Ping must cause a disconnect within its ten-second deadline.
            assert await asyncio.wait_for(reader.read(1),12) == b''
            complete.set_result(True)
        except BaseException as error:
            if not complete.done(): complete.set_exception(error)
        finally:
            writer.close()
    server = await asyncio.start_server(peer,'127.0.0.1',3001,ssl=tls)
    async with server:
        p = await asyncio.create_subprocess_exec(BINARY,'--observe',str(config),stderr=asyncio.subprocess.PIPE)
        try:
            await asyncio.wait_for(complete,30)
            assert p.returncode is None, 'Heartbeat failure must retry, not exit'
            p.terminate()
            assert await asyncio.wait_for(p.wait(),3) == 0
            logs = (await p.stderr.read()).decode()
            assert 'retrying in 5s' in logs
        finally:
            if p.returncode is None: p.kill(); await p.wait()
    print('PASS heartbeat-timeout',flush=True)

async def main():
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        cert, key = directory/'cert.pem', directory/'key.pem'
        p = await asyncio.create_subprocess_exec('openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','1','-subj','/CN=localhost',stdout=asyncio.subprocess.DEVNULL,stderr=asyncio.subprocess.DEVNULL)
        assert await p.wait() == 0
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls.load_cert_chain(cert, key)
        for mode in ('redirect','observe','auth','permission','launch-permission','heartbeat'):
            await scenario(mode, tls, directory)
        bad = directory/'bad.json'
        bad.write_text('{"host":"127.0.0.1"}')
        p = await asyncio.create_subprocess_exec(BINARY, str(bad), stderr=asyncio.subprocess.PIPE)
        assert await p.wait() == 78
        print('PASS invalid-config', flush=True)
        await heartbeat_timeout(tls, directory/'config.json')
        # A dropped handshake must cause reconnection without terminating the client.
        connections = 0
        connected_twice = asyncio.Event()
        async def disconnect(ws):
            nonlocal connections
            connections += 1
            await ws.close()
            if connections == 2: connected_twice.set()
        async with websockets.serve(disconnect, '127.0.0.1',3001,ssl=tls):
            p = await asyncio.create_subprocess_exec(BINARY, '--observe',str(directory/'config.json'),stderr=asyncio.subprocess.PIPE)
            try:
                await asyncio.wait_for(connected_twice.wait(), 10)
                p.terminate()
                assert await asyncio.wait_for(p.wait(),3) == 0
            finally:
                if p.returncode is None: p.kill(); await p.wait()
        print('PASS reconnect',flush=True)
asyncio.run(main())
