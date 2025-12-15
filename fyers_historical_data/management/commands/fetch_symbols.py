"""
Management command to fetch real symbols from FYERS API (FIXED)
"""

from django.core.management.base import BaseCommand
from fyers_historical_data.services.symbol_fetcher import FYERSSymbolFetcher


class Command(BaseCommand):
    help = 'Fetch real symbols from FYERS API and save to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--exchange',
            type=str,
            choices=['NSE', 'BSE', 'all'],
            default='all',
            help='Exchange to fetch symbols for'
        )

    def handle(self, *args, **options):
        exchange = options['exchange']
        fetcher = FYERSSymbolFetcher()
        
        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS('Fetching Real Symbols from FYERS API'))
        self.stdout.write('='*60)
        
        total_created = 0
        total_updated = 0
        
        # Fetch NSE symbols
        if exchange in ['NSE', 'all']:
            self.stdout.write('\n📡 Fetching NSE symbols...')
            nse_symbols = fetcher.fetch_nse_symbols()
            
            if nse_symbols:
                self.stdout.write(self.style.SUCCESS(f'   ✅ Found {len(nse_symbols)} NSE symbols'))
                self.stdout.write('   💾 Saving to database...')
                created, updated = fetcher.save_symbols_to_database('NSE', 'STOCKS', nse_symbols)
                self.stdout.write(self.style.SUCCESS(
                    f'   ✅ NSE Complete: {created} created, {updated} updated'
                ))
                total_created += created
                total_updated += updated
            else:
                self.stdout.write(self.style.ERROR('   ❌ Failed to fetch NSE symbols'))
        
        # Fetch BSE symbols
        if exchange in ['BSE', 'all']:
            self.stdout.write('\n📡 Fetching BSE symbols...')
            bse_symbols = fetcher.fetch_bse_symbols()
            
            if bse_symbols:
                self.stdout.write(self.style.SUCCESS(f'   ✅ Found {len(bse_symbols)} BSE symbols'))
                self.stdout.write('   💾 Saving to database...')
                created, updated = fetcher.save_symbols_to_database('BSE', 'STOCKS', bse_symbols)
                self.stdout.write(self.style.SUCCESS(
                    f'   ✅ BSE Complete: {created} created, {updated} updated'
                ))
                total_created += created
                total_updated += updated
            else:
                self.stdout.write(self.style.ERROR('   ❌ Failed to fetch BSE symbols'))
        
        # Show statistics
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📊 Symbol Fetching Summary'))
        self.stdout.write('='*60)
        
        stats = fetcher.get_symbol_stats()
        
        if stats:
            self.stdout.write(f"\n📈 Total Symbols in Database: {stats['total_symbols']}")
            self.stdout.write(f"✅ Active Symbols: {stats['active_symbols']}")
            
            self.stdout.write("\n📊 By Exchange:")
            for exchange_code, count in stats['by_exchange'].items():
                self.stdout.write(f"   • {exchange_code}: {count} symbols")
            
            self.stdout.write("\n📊 By Instrument:")
            for instrument_code, count in stats['by_instrument'].items():
                self.stdout.write(f"   • {instrument_code}: {count} symbols")
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(
            f'✅ Fetch Complete! {total_created} created, {total_updated} updated'
        ))
        self.stdout.write('='*60)