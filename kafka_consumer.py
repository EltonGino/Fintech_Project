# from kafka import KafkaConsumer
# import json
#
# # Initialize Kafka consumer
# consumer = KafkaConsumer(
#     'your_topic',
#     bootstrap_servers='localhost:9092',
#     value_deserializer=lambda x: json.loads(x.decode('utf-8'))
# )
#
# # Consume messages
# for message in consumer:
#     print("Received message:", message.value)

from kafka import KafkaConsumer
import json

# Initialize Kafka consumer
consumer = KafkaConsumer(
    'stock_data',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# Consume messages
print("Waiting for messages on 'stock_data' topic...")
for message in consumer:
    print("Received message:", message.value)