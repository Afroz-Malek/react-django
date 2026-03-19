"""
Kafka Consumer for Fyers Historical Data

Consumes messages from:
  - historical_data_requests  : processes fetch requests and calls Fyers API

Publishes results to:
  - historical_data_results   : raw OHLCV candle data
  - historical_data_status    : status updates (processing / completed / failed)
"""

import json
import logging
import time
from datetime import datetime

import django
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError

from .kafka_config import (
    get_consumer_config,
    get_producer_config,
    TOPIC_HISTORICAL_DATA_REQUESTS,
    TOPIC_HISTORICAL_DATA_RESULTS,
    TOPIC_HISTORICAL_DATA_STATUS,
)

logger = logging.getLogger(__name__)


class HistoricalDataConsumer:
    """
    Long-running consumer that processes historical data fetch requests.

    Lifecycle
    ---------
    1. Receive a message from `historical_data_requests`
    2. Update the DB request status to 'processing'
    3. Fetch OHLCV data from Fyers API (via FyersDataService)
    4. Publish candle chunks to `historical_data_results`
    5. Update DB request status to 'completed' / 'failed'
    6. Publish final status to `historical_data_status`
    """

    CHUNK_SIZE = 500  # candles per result message

    def __init__(self):
        self.consumer = None
        self.producer = None
        self._running = False

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _init_consumer(self):
        config = get_consumer_config()
        config['value_deserializer'] = lambda v: json.loads(v.decode('utf-8'))
        self.consumer = KafkaConsumer(
            TOPIC_HISTORICAL_DATA_REQUESTS,
            **config,
        )
        logger.info(f"Kafka consumer subscribed to: {TOPIC_HISTORICAL_DATA_REQUESTS}")

    def _init_producer(self):
        config = get_producer_config()
        config['value_serializer'] = lambda v: json.dumps(v).encode('utf-8')
        self.producer = KafkaProducer(**config)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def start(self):
        """Start the consumer loop. Blocks until stop() is called."""
        self._init_consumer()
        self._init_producer()
        self._running = True
        logger.info("Historical data consumer started.")

        try:
            while self._running:
                records = self.consumer.poll(timeout_ms=1000)
                for _tp, messages in records.items():
                    for msg in messages:
                        self._handle_message(msg)
                        self.consumer.commit()
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user.")
        finally:
            self._shutdown()

    def stop(self):
        self._running = False

    def _shutdown(self):
        if self.consumer:
            self.consumer.close()
        if self.producer:
            self.producer.flush()
            self.producer.close()
        logger.info("Historical data consumer shut down.")

    # ------------------------------------------------------------------
    # Message handling
    # ------------------------------------------------------------------

    def _handle_message(self, msg):
        payload = msg.value
        request_id = payload.get('request_id')

        logger.info(f"Processing historical data request {request_id}")

        try:
            self._update_request_status(request_id, 'processing')
            self._publish_status(request_id, 'processing')

            candles = self._fetch_historical_data(payload)

            self._publish_results(request_id, payload, candles)
            self._update_request_status(
                request_id, 'completed',
                total_records=len(candles),
            )
            self._publish_status(request_id, 'completed')
            logger.info(f"Request {request_id} completed — {len(candles)} candles")

        except Exception as exc:
            logger.exception(f"Error processing request {request_id}: {exc}")
            self._update_request_status(request_id, 'failed', error_message=str(exc))
            self._publish_status(request_id, 'failed', error_message=str(exc))

    # ------------------------------------------------------------------
    # Fyers API interaction
    # ------------------------------------------------------------------

    def _fetch_historical_data(self, payload: dict) -> list:
        """
        Fetch OHLCV candle data from Fyers using stored access token.

        Returns a list of candle dicts:
          {'date': str, 'open': float, 'high': float, 'low': float,
           'close': float, 'volume': int}
        """
        from fyers_auth.models import FyersToken

        fyers_account_id = payload.get('fyers_account_id')
        fyers_symbol = payload['fyers_symbol']
        from_date = payload['from_date']
        to_date = payload['to_date']

        # Resolve access token
        token_qs = FyersToken.objects.using('fyers')
        if fyers_account_id:
            token_obj = token_qs.get(id=fyers_account_id)
        else:
            # Round-robin: pick the most recently updated token
            token_obj = token_qs.order_by('-updated_at').first()

        if not token_obj or not token_obj.access_token:
            raise ValueError("No valid Fyers access token available")

        import requests as http_requests

        headers = {
            'Authorization': f'{token_obj.client_id}:{token_obj.access_token}',
        }

        params = {
            'symbol': fyers_symbol,
            'resolution': 'D',  # daily candles — adjust as needed
            'date_format': '1',
            'range_from': from_date,
            'range_to': to_date,
            'cont_flag': '1',
        }

        response = http_requests.get(
            'https://api.fyers.in/data/history',
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        if data.get('s') != 'ok':
            raise ValueError(f"Fyers API error: {data.get('message', data)}")

        candles_raw = data.get('candles', [])
        candles = []
        for c in candles_raw:
            # Fyers format: [epoch, open, high, low, close, volume]
            candles.append({
                'date': datetime.utcfromtimestamp(c[0]).strftime('%Y-%m-%d'),
                'open': c[1],
                'high': c[2],
                'low': c[3],
                'close': c[4],
                'volume': c[5],
            })

        return candles

    # ------------------------------------------------------------------
    # Publishing helpers
    # ------------------------------------------------------------------

    def _publish_results(self, request_id: int, payload: dict, candles: list):
        """Publish candles to historical_data_results in chunks."""
        total = len(candles)
        for start in range(0, total, self.CHUNK_SIZE):
            chunk = candles[start: start + self.CHUNK_SIZE]
            message = {
                'request_id': request_id,
                'symbol': payload['symbol_code'],
                'fyers_symbol': payload['fyers_symbol'],
                'from_date': payload['from_date'],
                'to_date': payload['to_date'],
                'chunk_index': start // self.CHUNK_SIZE,
                'total_records': total,
                'candles': chunk,
            }
            self.producer.send(
                TOPIC_HISTORICAL_DATA_RESULTS,
                value=message,
                key=str(request_id).encode('utf-8'),
            )
        self.producer.flush(timeout=10)

    def _publish_status(self, request_id: int, status: str, error_message: str = None):
        message = {
            'request_id': request_id,
            'status': status,
            'error_message': error_message,
        }
        try:
            self.producer.send(
                TOPIC_HISTORICAL_DATA_STATUS,
                value=message,
                key=str(request_id).encode('utf-8'),
            )
            self.producer.flush(timeout=5)
        except KafkaError as exc:
            logger.error(f"Failed to publish status for request {request_id}: {exc}")

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _update_request_status(
        request_id: int,
        status: str,
        error_message: str = None,
        total_records: int = None,
    ):
        from .models import HistoricalDataRequest

        update_fields = {'status': status}
        if error_message is not None:
            update_fields['error_message'] = error_message
        if total_records is not None:
            update_fields['total_records'] = total_records
        if status in ('completed', 'failed'):
            update_fields['processed_at'] = datetime.utcnow()

        HistoricalDataRequest.objects.using('fyers').filter(id=request_id).update(
            **update_fields
        )
