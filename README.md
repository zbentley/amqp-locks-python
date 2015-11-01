# amqp-locks-python
A Python implementation of RabbitMQ-backed semaphores and mutexes, as defined by [amqp-locks](https://github.com/zbentley/amqp-locks)

# Disclaimer/WIP/Mea Culpa
This project is ***brand new, unfinished, and a known-to-be-sketchy work-in-progress***. I'm still experimenting with it (and don't have a prover to make sure its approach is correct yet), so it's all subject to change. For planned research/changes, see [TODO](TODO.md).

# Requirements
1. Python 3 must be installed.
2. [Pika](https://pika.readthedocs.org) must be installed.
3. [RabbitMQ](https://www.rabbitmq.com/) 3 or higher must be installed and running. 

For help installing RabbitMQ, check out these links:

- [Video of installation](https://vimeo.com/10254034); very thorough.
- [Official installation instructions](https://www.rabbitmq.com/install-standalone-mac.html).
- [Using RabbitMQ in a Docker container](https://elasticbox.com/blog/deploy-rabbitmq-docker-container-with-elasticbox/).


# Usage

`test_locks.py` is a script that uses the lock implementations in this repository against a local RabbitMQ broker. It is configured by default to connect as `guest` to RabbitMQ on localhost at the default port. 

Use `test_locks.py [lock type] [operation]` to experiment with locks. Available lock types are `true_mutex` and `semaphore` (a persistent semaphore). Each lock type has its own help message which displays actions that can be taken with that lock type. For example, `test_locks.py semaphore --help` displays everything that can be done with semaphores.

#### Global behavior flags

Several flags are available that affect the global behavior of the script in any lock mode:

- `--sleep SECONDS`: after finishing operations (or after each operation in a loop), sleep for SECONDS seconds. SECONDS can be a decimal value. It defaults to 0.5.
- `--verbose`: display more detailed information about locking operations, including timing.

#### True Mutex locks

Two behavior switches are available in `true_mutex` mode:

- `--acquire`: in this mode, `test_locks.py` will attempt to acquire a named mutex.
- `--loop`: continue trying to acquire/verify the mutex in a loop, sleeping in between each iteration.

#### Semaphore Locks

In `semaphore` mode, the following behavior switches are available:

- `--acquire`: try to acquire a slot on the semaphore.
	- `--loop`: continue trying to acquire/verify the semaphore in a loop, sleeping in between each iteration.
	- `--greedy`: try to acquire as many semaphores as possible, and then print out how many were acquired. In `--loop` mode, acquired semaphores are stored between iterations, and verified on each iteration of the loop; if they cannot be verified on a given iteration, they are released. If new semaphores become available, they will be added to the stored set on each iteration.
- `--destroy`: destroys the named semaphore used for testing. This is useful to prevent RabbitMQ clutter.
- `--change COUNT` given a positive or negative COUNT, increases or decreases the number of slots on the semaphore by that amount. Semaphores cannot be decremented below 0.

# Examples:

- If you do `test_locks.py --sleep 60 true_mutex --acquire` in two different shells at the same time, only should succeed in getting the lock.
- If you do `test_locks.py semaphore --acquire --greedy --loop` in one shell, and then issue `test_locks.py semaphore --change 1` in another, the first shell should output that it acquired a lock. Subsequent `--change` operations should cause locks to be acquired or released by the first process.

# FAQ

#### I get a ConnectionClosed error immediately upon trying to do anything. Help!

Make sure RabbitMQ is started and connectible using the default `guest` account, on the default port, on `localhost`.