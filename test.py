#!/usr/bin/env python3
import sys
sys.path.append("lib")


from cluster_utils import get_connection_parameters
from rabbitlock.mutex import Mutex
from time import sleep

conn = Mutex("foo", get_connection_parameters())
while conn.ensure_acquired():
	print("Got lock")
	sleep(1)