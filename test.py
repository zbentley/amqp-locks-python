#!/bin/env python3

from cluster_utils import get_connection_parameters
from mutex import Mutex
from time import sleep

conn = Mutex("foo", get_connection_parameters())
while conn.ensure_acquired():
	print("Got lock")
	sleep(1)