#!/usr/bin/env python3

import pika
import time
import sys
import argparse
sys.path.append("lib")
from rabbitlock.mutex import Mutex
from rabbitlock.semaphore import Semaphore
import cProfile


# http://www.huyng.com/posts/python-performance-analysis/
class Timer(object):
    def __init__(self, verbose=True):
        self.verbose = verbose

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000  # millisecs
        if self.verbose:
            print('elapsed time: %f ms' % self.msecs)

def get_connection_parameters():
    # return cluster_utils.get_connection_parameters()

    return pika.ConnectionParameters("localhost",
                                     5672,
                                     "/",
                                     pika.PlainCredentials("guest", "guest")
                                     )

def true_mutex_operations(args):
    print(args)
    lock = Mutex("foo", get_connection_parameters())
    while True:
        acquired = False
        with Timer(args.time) as t:
            acquired = lock.ensure_acquired()
        if acquired:
            print("Got lock")
        else:
            print("Lost lock")
        if args.loop:
            time.sleep(0.5)
        else:
            break

def semaphore_operations(args):
    lock = Semaphore("foo", get_connection_parameters())
    if args.destroy:
        with Timer() as t:
            lock.ensure_semaphore_destroyed()
    elif args.acquire:
        if args.loop:
            pass
        else:
            acquired = False
            with Timer() as t:
                acquired = lock.ensure_semaphore_held()
            if acquired:
                print("Got lock: " + acquired)
            else:
                print("Could not get lock")
    elif args.change:
        lock.adjust_semaphore(args.change)

def parse_args(args):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    parser.add_argument("--time", action="store_true")

    semparser = subparsers.add_parser("semaphore")
    semparser.set_defaults(func=semaphore_operations)

    semops = semparser.add_mutually_exclusive_group()
    semops.add_argument("--change", type=int)
    semops.add_argument("--acquire", action="store_true")
    semops.add_argument("--loop", action="store_true")
    semops.add_argument("--destroy", action="store_true")

    truemutexparser = subparsers.add_parser("true_mutex")
    truemutexparser.set_defaults(func=true_mutex_operations)

    truemutexparser.add_argument("--acquire", action="store_true", default=True)
    truemutexparser.add_argument("--loop", action="store_true")

    return parser.parse_args(args)

args = parse_args(sys.argv[1:])
args.func(args)