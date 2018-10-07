import psutil
import sys
import time
import curses
import math
import collections
import ipgetter
from pyfiglet import Figlet
from queue import Queue
import threading

# Util

class Line:
    def __init__(self, string, meta=None):
        self.string = string
        self.formatted = False
        if(meta is not None):
            self.formatted = True
            self.meta = meta

    def set_meta(self, meta):
        self.formatted = True
        self.meta = meta

    def is_formatted(self):
        return self.formatted

def get_ip_thread(ip_q):
    ip_q.put(ipgetter.myip())

def get_ip():
    global ip_q

    worker = threading.Thread(target=get_ip_thread, args=(ip_q,))
    worker.daemon = True
    worker.start()

def update_ip():
    global ip_q
    global ip

    if not ip_q.empty(): 
        ip = ip_q.get()

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def sizeof_fmt_net(num, suffix='B'):
        num /= 1024
        for unit in ['Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)    

def draw_to_screen(y, x, lines, screen):
    height,_ = screen.getmaxyx()
    
    for line in lines:
        if(y < height):
            screen.move(y, x)
            if(line.is_formatted()):
                screen.addstr(line.string, line.meta)
            else:
                screen.addstr(line.string)
            y += 1
    return y

def draw_bar(y, x, screen, length=20, percent=50):
    height,_ = screen.getmaxyx()
    if(y >= height):
        return None
    
    filled = math.floor((length * (percent / 100)))
    empty = length - filled

    screen.move(y, x)

    if(filled > 0):
        screen.addstr(" "*filled, curses.color_pair(2))
    if(empty > 0):
        screen.addstr(" "*empty, curses.color_pair(3))
    

def get_columns(data, form='{:<13} {:>12} {:>12} {:>12}'):
    col_width = max(len(word) for row in data for word in row) + 2  # padding
    data_str = []
    for row in data:
        data_str.append(Line(form.format(*row)))
    return data_str

def pad(name):
    return name.ljust(12) + ":"

def cycle_q(q, to_add, length):
    old = 0
    if len(q) > length:
        old = q.popleft()
    q.append(to_add)
    return q, old
    

# Stat Strings

def get_space_string(path):
    usage = psutil.disk_usage(path)
    return [sizeof_fmt(usage.used), sizeof_fmt(usage.total), str(usage.percent) + "%"]

def get_memory_string():
    memory = psutil.virtual_memory()
    return [sizeof_fmt(memory.used), sizeof_fmt(memory.total), str(memory.percent) + "%"]

def get_swap_memory_string():
    swap_memory = psutil.swap_memory()
    return [sizeof_fmt(swap_memory.used), sizeof_fmt(swap_memory.total), str(swap_memory.percent) + "%"]

def get_net_stats():
    nics = psutil.net_io_counters(pernic=True)
    if 'tun0' in nics:
        nic = nics['tun0']
        vpn = 'On'
    else:
        nic = nics['eno1']
        vpn = 'Off'
    return [nic.bytes_recv, nic.bytes_sent, vpn]
    

# Main

def update(screen):
    height,width = screen.getmaxyx()
    offset_x = int((width / 2) - (50 / 2))
    if(offset_x < 0):
        return None
    offset_y = 0

    # Memory

    memory = [["Memory", "Used", "Total", "Percent"]]
    memory.append([pad("Physical")] + get_memory_string())
    memory.append([pad("Swap")] + get_swap_memory_string())
    memory_lines = get_columns(memory)
    memory_lines[0].set_meta(curses.color_pair(1) | curses.A_BOLD)

    memory_percent = psutil.virtual_memory().percent
    

    # Disks

    disks = [["Disk", "Used", "Total", "Percent"]]
    disks.append([pad("Root Disk")] + get_space_string('/'))
    disks.append([pad("Data Disk")] + get_space_string('/mnt/data'))
    disks.append([pad("NTFS Disk 1")] + get_space_string('/mnt/ntfs'))
    disks.append([pad("NTFS Disk 2")] + get_space_string('/mnt/ntfs3'))
    disks.append([pad("NTFS Disk 3")] + get_space_string('/mnt/ntfs2'))
    disks_lines = get_columns(disks)
    disks_lines[0].set_meta(curses.color_pair(1) | curses.A_BOLD)

    # CPU

    global cpu_q
    
    cpu_percent = psutil.cpu_percent()
    cpu_q, _ = cycle_q(cpu_q, cpu_percent, 10)
    cpu_percent = sum(cpu_q) / len(cpu_q)

    # Network

    global net_q_sent
    global net_q_recv
    global vpn_state
    global ip

    update_ip()
    net_stats = get_net_stats()
    
    net = [["External IP", "Data In", "Data Out"]]
    net_q_recv, old_recv = cycle_q(net_q_recv, net_stats[0], 20)
    net_q_sent, old_sent = cycle_q(net_q_sent, net_stats[1], 20)
    real_recv = net_stats[0] - old_recv
    real_sent = net_stats[1] - old_sent
    net.append([ip, sizeof_fmt_net(real_recv), sizeof_fmt_net(real_sent)])
    

    vpn = [["VPN Status"]]
    vpn.append([net_stats[2]])
    vpn_lines = get_columns(vpn, '{:>52}')
    vpn_lines[0].set_meta(curses.color_pair(1) | curses.A_BOLD)
    pair = 5 if net_stats[2] == 'Off' else 4
    vpn_lines[1].set_meta(curses.color_pair(pair) | curses.A_BOLD)

    if(net_stats[2] != vpn_state):
        get_ip()
        vpn_state = net_stats[2]
    net_lines = get_columns(net, "{:<13} {:>12} {:>12}")
    net_lines[0].set_meta(curses.color_pair(1) | curses.A_BOLD)
    
    
    # Screen (Banner > CPU Bar > Memory Bar > Memory > Disks > Network > VPN)

    global banner
    offset_y = draw_to_screen(offset_y, offset_x, banner, screen)

    offset_y = draw_to_screen(offset_y+1, offset_x, [Line("CPU Usage - {0:.1f}%".format(cpu_percent))], screen)
    draw_bar(offset_y, offset_x, screen, 52, cpu_percent)
    offset_y += 2

    offset_y = draw_to_screen(offset_y, offset_x, [Line("Memory Usage - {}%".format(memory_percent))], screen)
    draw_bar(offset_y, offset_x, screen, 52, memory_percent)
    offset_y += 2

    offset_y = draw_to_screen(offset_y, offset_x, memory_lines, screen)
    offset_y = draw_to_screen(offset_y+1, offset_x, disks_lines, screen)

    draw_to_screen(offset_y+1, offset_x, vpn_lines, screen)
    draw_to_screen(offset_y+1, offset_x, net_lines, screen)
    

# Globals
banner = []
cpu_q = collections.deque()
net_q_sent = collections.deque()
net_q_recv = collections.deque()
vpn_state = 'start'
ip = ipgetter.myip()
ip_q = Queue()

if __name__ == "__main__":
    screen = curses.initscr()
    curses.noecho()
    curses.curs_set(0)
    # Headers
    curses.start_color()
    curses.use_default_colors()

    # Headers
    curses.init_color(curses.COLOR_GREEN,100,600,100)
    curses.init_color(curses.COLOR_BLUE,0,350,750)

    # Headers
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    # Bar
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_GREEN)
    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLUE)
    # VPN Status
    curses.init_pair(4, 40, -1)
    curses.init_pair(5, curses.COLOR_RED, -1)

    fig = Figlet()
    text = fig.renderText('Manjaro I3')
    for s in text.splitlines():
        banner.append(Line(s, curses.color_pair(1)))
    
    while True:
        screen.erase()
        update(screen)
        screen.refresh()
        time.sleep(0.1)
    