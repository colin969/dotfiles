#!/bin/sh

sleep 1
exec i3-msg 'workspace 1:Term; append_layout /home/colinb/.i3/workspace-1.json; exec urxvt -e python3 /home/colinb/polybar-scripts/term/monitor.py; exec urxvt; exec urxvt'
