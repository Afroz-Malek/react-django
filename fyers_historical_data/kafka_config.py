"""
Kafka Configuration for Fyers Historical Data
"""

from django.conf import settings


def get_kafka_bootstrap_servers():
    return settings.KAFKA_BOOTSTRAP_SERVERS


def get_producer_config():
    return {
        'bootstrap_servers': get_kafka_bootstrap_servers(),
        'value_serializer': None,  # handled in producer
        'retries': 3,
        'retry_backoff_ms': 500,
        'request_timeout_ms': 30000,
        'acks': 'all',
    }


def get_consumer_config(group_id=None):
    return {
        'bootstrap_servers': get_kafka_bootstrap_servers(),
        'group_id': group_id or settings.KAFKA_CONSUMER_GROUP_ID,
        'auto_offset_reset': 'earliest',
        'enable_auto_commit': False,
        'value_deserializer': None,  # handled in consumer
        'session_timeout_ms': 30000,
        'heartbeat_interval_ms': 10000,
    }


# Topic names — single source of truth
TOPIC_HISTORICAL_DATA_REQUESTS = settings.KAFKA_TOPICS['HISTORICAL_DATA_REQUESTS']
TOPIC_HISTORICAL_DATA_RESULTS = settings.KAFKA_TOPICS['HISTORICAL_DATA_RESULTS']
TOPIC_HISTORICAL_DATA_STATUS = settings.KAFKA_TOPICS['HISTORICAL_DATA_STATUS']
