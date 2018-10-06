import psutil
import sys
import time
import curses
import math
import collections
from pyfiglet import Figlet

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


def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def draw_to_screen(y, x, lines, screen):
    for line in lines:
        screen.move(y, x)
        if(line.is_formatted()):
            screen.addstr(line.string, line.meta)
        else:
            screen.addstr(line.string)
            
        y += 1
    return y

def draw_bar(y, x, screen, length=20, percent=50):
    filled = math.floor((length * (percent / 100)))
    empty = length - filled

    screen.move(y, x)

    if(filled > 0):
        screen.addstr(" "*filled, curses.color_pair(2))
    if(empty > 0):
        screen.addstr(" "*empty, curses.color_pair(3))
    

def get_columns(data):
    col_width = max(len(word) for row in data for word in row) + 2  # padding
    data_str = []
    for row in data:
        data_str.append(Line('{:<13} {:>12} {:>12} {:>12}'.format(*row)))
    return data_str

def pad(name):
    return name.ljust(12) + ":"
    

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
    
    

# Main

def update(screen):
    offset_y = 1
    offset_x = 2

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

    cpu_percent = psutil.cpu_percent()
    global cpu_q
    if len(cpu_q) >= 10:
        cpu_q.popleft()
    cpu_q.append(cpu_percent)
    cpu_percent = sum(cpu_q) / len(cpu_q)

    # Screen

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

# Globals
banner = []
cpu_q = collections.deque()
    
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
    
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_GREEN)
    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLUE)
    curses.init_pair(4, curses.COLOR_WHITE, -1)

    fig = Figlet()
    text = fig.renderText('Manjaro I3')
    for s in text.splitlines():
        banner.append(Line(s, curses.color_pair(4)))
    
    while True:
        screen.erase()
        update(screen)
        screen.refresh()
        time.sleep(0.2)
    