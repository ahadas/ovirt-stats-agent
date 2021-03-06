import collectd
import threading
import time
import json
import BaseHTTPServer
import ssl
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

collectd.info('spam: Loading Python plugin:') 
HOST_NAME = '0.0.0.0'
PORT_NUMBER = 9002 # Maybe set this to 9000.
CERTFILE_PATH = "/root/server.pem"

cache = {}

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(s):
        global cache 
        stats = cache
        cache = {}
        """Respond to a GET request."""
        collectd.info('MyHandler')

        output = {}

        for stat in stats:
            vals = stat.split('$')
            vm = vals[0]
            type = vals[1]
            if vm not in output:
                output[vm] = {'network':{}, 'disks':{}}

            if type in ['sample_time', 'cpu_user', 'cpu_sys', 'cpu_total']:
                if 'ps_cpu' not in output[vm]:
                    output[vm]['ps_cpu'] = {}
                output[vm]['ps_cpu'][type] = str(stats[stat])

            elif type in ['rx_bytes', 'tx_bytes', 'iface_time',
                          'rx_dropped', 'tx_dropped']:
                iface = vals[2]
                ifaces = output[vm]['network']
                if iface not in ifaces:
                    ifaces[iface] = {}
                ifaces[iface][type] = str(stats[stat])

            elif type in ['rd_bytes', 'wr_bytes', 'rd_ops', 'wr_ops', 'fl_ops',
                          'rd_time', 'wr_time', 'disk_time', 'fl_time']:
                disk = vals[2]
                disks = output[vm]['disks']
                if disk not in disks:
                    disks[disk] = {}
                disks[disk][type] = str(stats[stat])

            elif type == 'balloon':
                output[vm]['balloon_cur'] = str(stats[stat])

        string = json.dumps(output)

        s.send_response(200)
        s.send_header("Content-type", "text/json")
        s.end_headers()
        s.wfile.write(string)

def write(vl, data=None):
    global cache
    collectd.info('Writing data (vl=%r)' % (vl))
    if vl.plugin == 'virt':
        vm = vl.host
        type = vl.type
        if type == 'ps_cputime':
            cache[vm+'$cpu_user'] = vl.values[0]
            cache[vm+'$cpu_sys'] = vl.values[1]
            cache[vm+'$sample_time'] = vl.time

        elif type == 'virt_cpu_total':
            cache[vm+'$cpu_total'] = vl.values[0]

        elif vl.type_instance == 'actual_balloon':
            cache[vm+'$balloon'] = int(vl.values[0])

        elif type == 'if_octets':
            iface = vl.type_instance
            cache[vm+'$rx_bytes$'+iface] = \
                vl.values[0]
            cache[vm+'$tx_bytes$'+iface] = \
                vl.values[1]
            cache[vm+'$iface_time$'+iface] = \
                vl.time

        elif type == 'if_dropped':
            iface = vl.type_instance
            cache[vm+'$rx_dropped$'+iface] = \
                vl.values[0]
            cache[vm+'$tx_dropped$'+iface] = \
                vl.values[1]

        elif type == 'disk_octets':
            disk = vl.type_instance
            cache[vm+'$rd_bytes$'+disk] = \
                vl.values[0]
            cache[vm+'$wr_bytes$'+disk] = \
                vl.values[1]
            cache[vm+'$disk_time$'+disk] = \
                vl.time

        elif type == 'disk_ops':
            disk = vl.type_instance
            cache[vm+'$rd_ops$'+disk] = \
                vl.values[0]
            cache[vm+'$wr_ops$'+disk] = \
                vl.values[1]

        elif type == 'disk_time':
            disk = vl.type_instance
            cache[vm+'$rd_time$'+disk] = \
                vl.values[0]
            cache[vm+'$wr_time$'+disk] = \
                vl.values[1]

        elif type == 'total_time_in_ms':
            disk = vl.type_instance[6:]
            cache[vm+'$fl_time$'+disk] = \
                vl.values[0]

        elif type == 'total_requests':
            disk = vl.type_instance[6:]
            cache[vm+'$fl_ops$'+disk] = \
                vl.values[0]

def init_callback():
    def init():
        server = HTTPServer((HOST_NAME, PORT_NUMBER), MyHandler)
#        server.socket = ssl.wrap_socket(server.socket, certfile=CERTFILE_PATH,
#                                        server_side=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        server.server_close()

    t = threading.Thread(target=init)
    t.start()   

collectd.register_write(write)
collectd.register_init(init_callback)
