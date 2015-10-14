#!/bin/env python3

from cluster_utils import get_connection_parameters
from mutex import Mutex
from time import sleep

# connection = pika.BlockingConnection()

# channel = connection.channel()

# channel.queue_declare(queue="test", durable=True, exclusive=False, auto_delete=False)

# channel.confirm_delivery()

# # Send a message
# if channel.basic_publish(exchange='test',
#                          routing_key='test',
#                          body='Hello World!',
#                          properties=pika.BasicProperties(content_type='text/plain',
#                                                          delivery_mode=1)):
#     print 'Message publish was confirmed'
# else:
#     print 'Message could not be confirmed'

conn = Mutex("foo", get_connection_parameters())
print(conn.channel)
