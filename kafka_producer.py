# from kafka import KafkaProducer
# import json
#
# # Initialize Kafka producer
# producer = KafkaProducer(
#     bootstrap_servers='localhost:9092',
#     value_serializer=lambda v: json.dumps(v).encode('utf-8')
# )
#
# # Example data
# data = {'message': 'Hello, Kafka! Good Day! Hope this works!', 'age': 31}
#
# # Send data to Kafka
# producer.send('your_topic', data)
# producer.flush()
# print("Data sent to Kafka.")

from kafka import KafkaProducer
import json

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Example data
data = {'message': 'Hello, Kafka! Testing stock_data topic!', 'age': 31}

# Send data to Kafka
producer.send('stock_data', data)
producer.flush()
print("Data sent to Kafka on 'stock_data' topic.")