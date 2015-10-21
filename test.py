#!/usr/bin/env python3

import pika
import time
import sys
import argparse
sys.path.append("lib")
from rabbitlock.mutex import Mutex
from rabbitlock.semaphore import Semaphore

def positive_float(value):
    retval = float(value)
    if retval < 0:
         raise argparse.ArgumentTypeError("%s not a positive float" % value)
    return retval

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

    return pika.ConnectionParameters("localhost", 5672, "/", pika.PlainCredentials("guest", "guest"))


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

        time.sleep(args.sleep)
        if not args.loop:
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
            with Timer() as t:
                acquired = lock.ensure_semaphore_held()
            if acquired:
                print("Got lock: %d" % acquired)
            else:
                print("Could not get lock")
            time.sleep(args.sleep)
    elif args.change:
        if lock.adjust_semaphore(args.change):
            print("Adjustment success")
        else:
            print("Adjustment failure")


def parse_and_dispatch(args):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    parser.add_argument("--profile", action="store_true")
    parser.add_argument("--sleep", type=positive_float, default=0.5)

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

    result = parser.parse_args(args)
    result.func(result)

parse_and_dispatch(sys.argv[1:])