#!/usr/bin/env python3

from cluster_utils import get_connection_parameters
from time import sleep
import sys

sys.path.append("lib")
from rabbitlock.mutex import Mutex

conn = Mutex("foo", get_connection_parameters())
while conn.ensure_acquired():
    print("Got lock")
    sleep(1)
