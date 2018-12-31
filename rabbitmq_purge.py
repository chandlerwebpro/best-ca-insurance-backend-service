import pika
params = pika.ConnectionParameters(host='localhost')
conn = pika.BlockingConnection(params)
ch = conn.channel()
ch.queue_delete(queue='rpc_queue')
ch.close()