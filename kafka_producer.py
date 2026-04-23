from kafka import KafkaProducer
import json
import os

KAFKA_SERVER = os.getenv("KAFKA_SERVER", "kafka:9092")

producer = None

def get_producer ():
    global producer
    if producer is None:
        producer = KafkaProducer(
        bootstrap_servers = KAFKA_SERVER,
        value_serialize = lambda
    )

    return producer

def enviar_evento(topico: str, evento: dict):
    prod = get_producer()
    prod.send(topico,evento)
    prod.flush()

