"""
Django management command to start the Kafka historical data consumer.

Usage:
    python manage.py start_kafka_consumer
    python manage.py start_kafka_consumer --group-id custom-group
"""

import logging
import signal
import sys

from django.core.management.base import BaseCommand

from fyers_historical_data.kafka_consumer import HistoricalDataConsumer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start the Kafka consumer for processing historical data requests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--group-id',
            type=str,
            default=None,
            help='Override the Kafka consumer group ID (default: from settings)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Kafka historical data consumer...'))
        self.stdout.write('Press Ctrl+C to stop.\n')

        consumer = HistoricalDataConsumer()

        def _shutdown(signum, frame):
            self.stdout.write('\nShutting down consumer...')
            consumer.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        try:
            consumer.start()
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f'Consumer error: {exc}'))
            logger.exception('Kafka consumer crashed')
            sys.exit(1)
