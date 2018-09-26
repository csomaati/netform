#!/bin/bash

SCRIPT_FOLDER=/mnt/ADAT/netform/valley_free/scripts
REMOTE_SCRIPT_FOLDER='~/compnet/scripts/'

rsync -azP --include='tools/' --include='*.py' --exclude='*' $SCRIPT_FOLDER/ superman:$REMOTE_SCRIPT_FOLDER
