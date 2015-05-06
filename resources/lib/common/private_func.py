import socket
import struct


def is_ip(address):
    """from http://www.seanelavelle.com/2012/04/16/checking-for-a-valid-ip-in-python/"""
    try:
        socket.inet_aton(address)
        ip = True
    except socket.error:
        ip = False

    return ip


def wake_servers(settings):
    if settings.get_setting('wolon'):

        print "PleXBMC -> Wake On LAN: true"
        for servers in settings.get_wakeservers():
            if servers:
                try:
                    print "PleXBMC -> Waking server with MAC: %s" % servers
                    __wake_on_lan(servers)
                except ValueError:
                    print "PleXBMC -> Incorrect MAC address format for server %s" % servers
                except:
                    print "PleXBMC -> Unknown wake on lan error"


def __wake_on_lan(macaddress):
    """ Switches on remote computers using WOL. """

    macaddress = macaddress.strip()

    # Check macaddress format and try to compensate.
    if len(macaddress) == 12:
        pass
    elif len(macaddress) == 12 + 5:
        sep = macaddress[2]
        macaddress = macaddress.replace(sep, '')
    else:
        raise ValueError('Incorrect MAC address format')

    # Pad the synchronization stream.
    data = ''.join(['FFFFFFFFFFFF', macaddress * 20])
    send_data = ''

    # Split up the hex values and pack.
    for i in range(0, len(data), 2):
        send_data = ''.join([send_data,
                             struct.pack('B', int(data[i: i + 2], 16))])

    # Broadcast it to the LAN.
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(send_data, ('<broadcast>', 7))