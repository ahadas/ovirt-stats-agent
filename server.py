import time
import json
import BaseHTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

HOST_NAME = '10.35.1.90' # !!!REMEMBER TO CHANGE THIS!!!
PORT_NUMBER = 9002 # Maybe set this to 9000.

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
    def do_GET(s):
        """Respond to a GET request."""
        stats = s.server.cache
        s.server.cache = {}
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
                output[vm]['ps_cpu'][type] = stats[stat]

            elif type in ['rx_bytes', 'tx_bytes', 'iface_time',
                          'rx_dropped', 'tx_dropped']:
                iface = vals[2]
                ifaces = output[vm]['network']
                if iface not in ifaces:
                    ifaces[iface] = {}
                ifaces[iface][type] = stats[stat]

            elif type in ['rd_bytes', 'wr_bytes', 'rd_ops', 'wr_ops',
                          'rd_time', 'wr_time', 'disk_time']:
                disk = vals[2]
                disks = output[vm]['disks']
                if disk not in disks:
                    disks[disk] = {}
                disks[disk][type] = stats[stat]

        str = json.dumps(output)

        s.send_response(200)
        s.send_header("Content-type", "text/json")
        s.end_headers()
        s.wfile.write(str)

    def do_POST(s):
        print time.asctime(), 'got something'
        content_len = int(s.headers.getheader('content-length', 0))
        post_body = s.rfile.read(content_len)

        stats = json.loads(post_body)

        print stats

        for st in stats:
            if st['plugin'] != 'virt':
                continue

            vm = st['host']
            type = st['type']
            if type == 'ps_cputime':
                s.server.cache[vm+'$cpu_user'] = st['values'][0]
                s.server.cache[vm+'$cpu_sys'] = st['values'][1]
                s.server.cache[vm+'$sample_time'] = st['time']

            elif type == 'virt_cpu_total':
                s.server.cache[vm+'$cpu_total'] = st['values'][0]

            elif type == 'if_octets':
                iface = st['type_instance']
                s.server.cache[vm+'$rx_bytes$'+iface] = \
                    st['values'][0]
                s.server.cache[vm+'$tx_bytes$'+iface] = \
                    st['values'][1]
                s.server.cache[vm+'$iface_time$'+iface] = \
                    st['time']

            elif type == 'if_dropped':
                iface = st['type_instance']
                s.server.cache[vm+'$rx_dropped$'+iface] = \
                    st['values'][0]
                s.server.cache[vm+'$tx_dropped$'+iface] = \
                    st['values'][1]

            elif type == 'disk_octets':
                disk = st['type_instance']
                s.server.cache[vm+'$rd_bytes$'+disk] = \
                    st['values'][0]
                s.server.cache[vm+'$wr_bytes$'+disk] = \
                    st['values'][1]
                s.server.cache[vm+'$disk_time$'+disk] = \
                    st['time']

            elif type == 'disk_ops':
                disk = st['type_instance']
                s.server.cache[vm+'$rd_ops$'+disk] = \
                    st['values'][0]
                s.server.cache[vm+'$wr_ops$'+disk] = \
                    st['values'][1]

            elif type == 'disk_time':
                disk = st['type_instance']
                s.server.cache[vm+'$rd_time$'+disk] = \
                    st['values'][0]
                s.server.cache[vm+'$wr_time$'+disk] = \
                    st['values'][1]

class http_server:
    def __init__(self):
        server = HTTPServer((HOST_NAME, PORT_NUMBER), MyHandler)
        server.cache = {}
        print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        server.server_close()
        print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)

class main:
    def __init__(self):
        self.server = http_server()

if __name__ == '__main__':
    m = main()
