#!/bin/sh

sleep 1
exec i3-msg 'workspace 1:; append_layout /home/colinb/.i3/workspace-1.json; exec urxvt -name monitor -fn "xft:RobotoMono Nerd Font:size=12" -e python3 /home/colinb/polybar-scripts/term/monitor.py; exec urxvt -name media -e ncmpcpp; exec urxvt -name main'
