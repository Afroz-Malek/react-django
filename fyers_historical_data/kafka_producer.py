"""
Kafka Producer for Fyers Historical Data Requests

Publishes messages to:
  - historical_data_requests  : new fetch request submitted by user
  - historical_data_status    : status update for an existing request
"""

import json
import logging
from datetime import date

from kafka import KafkaProducer
from kafka.errors import KafkaError

from .kafka_config import (
    get_producer_config,
    TOPIC_HISTORICAL_DATA_REQUESTS,
    TOPIC_HISTORICAL_DATA_STATUS,
)

logger = logging.getLogger(__name__)

_producer = None


def _get_producer() -> KafkaProducer:
    """Return a module-level singleton producer (lazy init)."""
    global _producer
    if _producer is None:
        config = get_producer_config()
        config['value_serializer'] = lambda v: json.dumps(v, default=_json_default).encode('utf-8')
        _producer = KafkaProducer(**config)
    return _producer


def _json_default(obj):
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _on_send_error(exc):
    logger.error(f"Kafka send error: {exc}")


def publish_historical_data_request(request_obj) -> bool:
    """
    Publish a new historical data request to Kafka.

    Args:
        request_obj: HistoricalDataRequest model instance

    Returns:
        True if published successfully, False otherwise.
    """
    message = {
        'request_id': request_obj.id,
        'user_email': request_obj.user_email,
        'exchange_id': request_obj.exchange_id,
        'exchange_code': request_obj.exchange.code,
        'instrument_id': request_obj.instrument_id,
        'instrument_code': request_obj.instrument.code,
        'symbol_id': request_obj.symbol_id,
        'symbol_code': request_obj.symbol.symbol_code,
        'fyers_symbol': request_obj.symbol.fyers_symbol,
        'from_date': request_obj.from_date,
        'to_date': request_obj.to_date,
        'account_type': request_obj.account_type,
        'fyers_account_id': request_obj.fyers_account_id,
    }

    try:
        producer = _get_producer()
        future = producer.send(
            TOPIC_HISTORICAL_DATA_REQUESTS,
            value=message,
            key=str(request_obj.id).encode('utf-8'),
        )
        future.add_errback(_on_send_error)
        producer.flush(timeout=10)
        logger.info(f"Published historical data request {request_obj.id} to Kafka")
        return True
    except KafkaError as exc:
        logger.error(f"Failed to publish request {request_obj.id} to Kafka: {exc}")
        return False


def publish_status_update(request_id: int, new_status: str, error_message: str = None) -> bool:
    """
    Publish a status update for an existing request.

    Args:
        request_id: ID of the HistoricalDataRequest
        new_status: One of 'pending', 'processing', 'completed', 'failed'
        error_message: Optional error detail when status is 'failed'

    Returns:
        True if published successfully, False otherwise.
    """
    message = {
        'request_id': request_id,
        'status': new_status,
        'error_message': error_message,
    }

    try:
        producer = _get_producer()
        future = producer.send(
            TOPIC_HISTORICAL_DATA_STATUS,
            value=message,
            key=str(request_id).encode('utf-8'),
        )
        future.add_errback(_on_send_error)
        producer.flush(timeout=10)
        logger.info(f"Published status update for request {request_id}: {new_status}")
        return True
    except KafkaError as exc:
        logger.error(f"Failed to publish status update for request {request_id}: {exc}")
        return False


def close_producer():
    """Flush and close the producer. Call on application shutdown."""
    global _producer
    if _producer is not None:
        _producer.flush()
        _producer.close()
        _producer = None
