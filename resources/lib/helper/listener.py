import re
import traceback
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from urlparse import urlparse, parse_qs

import xbmc
from resources.lib.helper.functions import *
from resources.lib.helper.subscribers import subMgr
from resources.lib.common import GLOBAL_SETUP, get_platform, PrintDebug, settings

log_print = PrintDebug("PleXBMC Helper", "listener")

class MyHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(s, format, *args):
        # I have my own logging, suppressing BaseHTTPRequestHandler's
        #printDebug(format % args)
        return True
    def do_HEAD(s):
        log_print.debug("Serving HEAD request...")
        s.answer_request(0)

    def do_GET(s):
        log_print.debug("Serving GET request...")
        s.answer_request(1)

    def do_OPTIONS(s):
        s.send_response(200)
        s.send_header('Content-Length', '0')
        s.send_header('X-Plex-Client-Identifier', settings.get_setting('client_id'))
        s.send_header('Content-Type', 'text/plain')
        s.send_header('Connection', 'close')
        s.send_header('Access-Control-Max-Age', '1209600')
        s.send_header('Access-Control-Allow-Origin', '*')
        s.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, DELETE, PUT, HEAD')
        s.send_header('Access-Control-Allow-Headers', 'x-plex-version, x-plex-platform-version, x-plex-username, x-plex-client-identifier, x-plex-target-client-identifier, x-plex-device-name, x-plex-platform, x-plex-product, accept, x-plex-device')
        s.end_headers()
        s.wfile.close()

    def response(s, body, headers = {}, code = 200):
        try:
            s.send_response(code)
            for key in headers:
                s.send_header(key, headers[key])
            s.send_header('Content-Length', len(body))
            s.send_header('Connection', "close")
            s.end_headers()
            s.wfile.write(body)
            s.wfile.close()
        except:
            pass

    def answer_request(s, sendData):
        try:
            request_path=s.path[1:]
            request_path=re.sub(r"\?.*","",request_path)
            url = urlparse(s.path)
            paramarrays = parse_qs(url.query)
            params = {}
            for key in paramarrays:
                params[key] = paramarrays[key][0]
            log_print ( "request path is: [%s]" % ( request_path,) )
            log_print ( "params are: %s" % params )
            subMgr.updateCommandID(s.headers.get('X-Plex-Client-Identifier', s.client_address[0]), params.get('commandID', False))
            if request_path=="version":
                s.response("PleXBMC Helper Remote Redirector: Running\r\nVersion: %s" % GLOBAL_SETUP['__version__'])
            elif request_path=="verify":
                result=jsonrpc("ping")
                s.response("XBMC JSON connection test:\r\n"+result)
            elif "resources" == request_path:
                resp = getXMLHeader()
                resp += "<MediaContainer>"
                resp += "<Player"
                resp += ' title="%s"' % settings.get_setting('devicename')
                resp += ' protocol="plex"'
                resp += ' protocolVersion="1"'
                resp += ' protocolCapabilities="navigation,playback,timeline"'
                resp += ' machineIdentifier="%s"' % settings.get_setting('client_id')
                resp += ' product="PleXBMC"'
                resp += ' platform="%s"' % get_platform()
                resp += ' platformVersion="%s"' % GLOBAL_SETUP['__version__']
                resp += ' deviceClass="pc"'
                resp += "/>"
                resp += "</MediaContainer>"
                log_print("crafted resources response: %s" % resp)
                s.response(resp, getPlexHeaders())
            elif "/subscribe" in request_path:
                s.response(getOKMsg(), getPlexHeaders())
                protocol = params.get('protocol', False)
                host = s.client_address[0]
                port = params.get('port', False)
                uuid = s.headers.get('X-Plex-Client-Identifier', "")
                commandID = params.get('commandID', 0)
                subMgr.addSubscriber(protocol, host, port, uuid, commandID)
            elif "/poll" in request_path:
                if params.get('wait', False) == '1':
                    xbmc.sleep(950)
                commandID = params.get('commandID', 0)
                s.response(re.sub(r"INSERTCOMMANDID", str(commandID), subMgr.msg(getPlayers())), {
                  'X-Plex-Client-Identifier': settings.get_setting('client_id'),
                  'Access-Control-Expose-Headers': 'X-Plex-Client-Identifier',
                  'Access-Control-Allow-Origin': '*',
                  'Content-Type': 'text/xml'
                })
            elif "/unsubscribe" in request_path:
                s.response(getOKMsg(), getPlexHeaders())
                uuid = s.headers.get('X-Plex-Client-Identifier', False) or s.client_address[0]
                subMgr.removeSubscriber(uuid)
            elif request_path == "player/playback/setParameters":
                s.response(getOKMsg(), getPlexHeaders())
                if 'volume' in params:
                    volume = int(params['volume'])
                    log_print("adjusting the volume to %s%%" % volume)
                    jsonrpc("Application.SetVolume", {"volume": volume})
            elif "/playMedia" in request_path:
                s.response(getOKMsg(), getPlexHeaders())
                resume = params.get('viewOffset', params.get('offset', "0"))
                protocol = params.get('protocol', "http")
                address = params.get('address', s.client_address[0])
                server = getServerByHost(address)
                port = params.get('port', server.get('port', '32400'))
                fullurl = protocol+"://"+address+":"+port+params['key']
                log_print("playMedia command -> fullurl: %s" % fullurl)
                jsonrpc("playmedia", [fullurl, resume])
                subMgr.lastkey = params['key']
                subMgr.server = server.get('server', 'localhost')
                subMgr.port = port
                subMgr.protocol = protocol
                subMgr.notify()
            elif request_path == "player/playback/play":
                s.response(getOKMsg(), getPlexHeaders())
                for playerid in getPlayerIds():
                    jsonrpc("Player.PlayPause", {"playerid" : playerid, "play": True})
            elif request_path == "player/playback/pause":
                s.response(getOKMsg(), getPlexHeaders())
                for playerid in getPlayerIds():
                    jsonrpc("Player.PlayPause", {"playerid" : playerid, "play": False})
            elif request_path == "player/playback/stop":
                s.response(getOKMsg(), getPlexHeaders())
                for playerid in getPlayerIds():
                    jsonrpc("Player.Stop", {"playerid" : playerid})
            elif request_path == "player/playback/seekTo":
                s.response(getOKMsg(), getPlexHeaders())
                for playerid in getPlayerIds():
                    jsonrpc("Player.Seek", {"playerid":playerid, "value":millisToTime(params.get('offset', 0))})
                subMgr.notify()
            elif request_path == "player/playback/stepForward":
                s.response(getOKMsg(), getPlexHeaders())
                for playerid in getPlayerIds():
                    jsonrpc("Player.Seek", {"playerid":playerid, "value":"smallforward"})
                subMgr.notify()
            elif request_path == "player/playback/stepBack":
                s.response(getOKMsg(), getPlexHeaders())
                for playerid in getPlayerIds():
                    jsonrpc("Player.Seek", {"playerid":playerid, "value":"smallbackward"})
                subMgr.notify()
            elif request_path == "player/playback/skipNext":
                s.response(getOKMsg(), getPlexHeaders())
                for playerid in getPlayerIds():
                    jsonrpc("Player.Seek", {"playerid":playerid, "value":"bigforward"})
                subMgr.notify()
            elif request_path == "player/playback/skipPrevious":
                s.response(getOKMsg(), getPlexHeaders())
                for playerid in getPlayerIds():
                    jsonrpc("Player.Seek", {"playerid":playerid, "value":"bigbackward"})
                subMgr.notify()
            elif request_path == "player/navigation/moveUp":
                s.response(getOKMsg(), getPlexHeaders())
                jsonrpc("Input.Up")
            elif request_path == "player/navigation/moveDown":
                s.response(getOKMsg(), getPlexHeaders())
                jsonrpc("Input.Down")
            elif request_path == "player/navigation/moveLeft":
                s.response(getOKMsg(), getPlexHeaders())
                jsonrpc("Input.Left")
            elif request_path == "player/navigation/moveRight":
                s.response(getOKMsg(), getPlexHeaders())
                jsonrpc("Input.Right")
            elif request_path == "player/navigation/select":
                s.response(getOKMsg(), getPlexHeaders())
                jsonrpc("Input.Select")
            elif request_path == "player/navigation/home":
                s.response(getOKMsg(), getPlexHeaders())
                jsonrpc("Input.Home")
            elif request_path == "player/navigation/back":
                s.response(getOKMsg(), getPlexHeaders())
                jsonrpc("Input.Back")
        except:
            traceback.print_exc()
    
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True