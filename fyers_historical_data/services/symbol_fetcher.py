"""
FYERS Symbol Fetcher Service (FIXED)
Fetches real symbol data from FYERS API
"""

import requests
import logging
import csv
from io import StringIO
from typing import List, Dict
from fyers_historical_data.models import Exchange, Instrument, Symbol

logger = logging.getLogger(__name__)


class FYERSSymbolFetcher:
    """
    Fetch symbols from FYERS API
    """
    
    SYMBOL_MASTER_URL = "https://public.fyers.in/sym_details/NSE_CM.csv"
    BSE_SYMBOL_URL = "https://public.fyers.in/sym_details/BSE_CM.csv"
    
    def __init__(self):
        self.session = requests.Session()
    
    def _safe_float(self, value: str, default: float = 0.0) -> float:
        """Safely convert string to float"""
        try:
            return float(value) if value and value.strip() else default
        except (ValueError, AttributeError):
            return default
    
    def _safe_int(self, value: str, default: int = 1) -> int:
        """Safely convert string to int"""
        try:
            return int(value) if value and value.strip() else default
        except (ValueError, AttributeError):
            return default
    
    def fetch_nse_symbols(self) -> List[Dict]:
        """
        Fetch NSE equity symbols from FYERS
        """
        try:
            logger.info("Fetching NSE symbols from FYERS...")
            response = self.session.get(self.SYMBOL_MASTER_URL)
            response.raise_for_status()
            
            # Parse CSV properly using csv module
            csv_file = StringIO(response.text)
            csv_reader = csv.reader(csv_file)
            
            # Skip header
            headers = next(csv_reader)
            logger.info(f"CSV Headers: {headers}")
            
            symbols = []
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    if len(row) < 11:
                        continue
                    
                    # Extract fields safely
                    symbol_data = {
                        'fytoken': row[0].strip() if len(row) > 0 else '',
                        'symbol_details': row[1].strip() if len(row) > 1 else '',
                        'exchange_instrument': row[2].strip() if len(row) > 2 else '',
                        'segment': row[3].strip() if len(row) > 3 else '',
                        'scrip_code': row[4].strip() if len(row) > 4 else '',
                        'scrip_name': row[5].strip() if len(row) > 5 else '',
                        'isin': row[7].strip() if len(row) > 7 else '',
                        'tick_size': self._safe_float(row[9] if len(row) > 9 else '', 0.05),
                        'lot_size': self._safe_int(row[10] if len(row) > 10 else '', 1),
                    }
                    
                    # Only add if we have essential data
                    if symbol_data['symbol_details'] and symbol_data['scrip_code']:
                        symbols.append(symbol_data)
                
                except Exception as row_error:
                    logger.warning(f"Error parsing row {row_num}: {row_error}")
                    continue
            
            logger.info(f"Successfully fetched {len(symbols)} NSE symbols")
            return symbols
        
        except Exception as e:
            logger.error(f"Error fetching NSE symbols: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def fetch_bse_symbols(self) -> List[Dict]:
        """
        Fetch BSE equity symbols from FYERS
        """
        try:
            logger.info("Fetching BSE symbols from FYERS...")
            response = self.session.get(self.BSE_SYMBOL_URL)
            response.raise_for_status()
            
            # Parse CSV properly using csv module
            csv_file = StringIO(response.text)
            csv_reader = csv.reader(csv_file)
            
            # Skip header
            headers = next(csv_reader)
            logger.info(f"CSV Headers: {headers}")
            
            symbols = []
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    if len(row) < 11:
                        continue
                    
                    # Extract fields safely
                    symbol_data = {
                        'fytoken': row[0].strip() if len(row) > 0 else '',
                        'symbol_details': row[1].strip() if len(row) > 1 else '',
                        'exchange_instrument': row[2].strip() if len(row) > 2 else '',
                        'segment': row[3].strip() if len(row) > 3 else '',
                        'scrip_code': row[4].strip() if len(row) > 4 else '',
                        'scrip_name': row[5].strip() if len(row) > 5 else '',
                        'isin': row[7].strip() if len(row) > 7 else '',
                        'tick_size': self._safe_float(row[9] if len(row) > 9 else '', 0.05),
                        'lot_size': self._safe_int(row[10] if len(row) > 10 else '', 1),
                    }
                    
                    # Only add if we have essential data
                    if symbol_data['symbol_details'] and symbol_data['scrip_code']:
                        symbols.append(symbol_data)
                
                except Exception as row_error:
                    logger.warning(f"Error parsing row {row_num}: {row_error}")
                    continue
            
            logger.info(f"Successfully fetched {len(symbols)} BSE symbols")
            return symbols
        
        except Exception as e:
            logger.error(f"Error fetching BSE symbols: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def save_symbols_to_database(self, exchange_code: str, instrument_code: str, symbols_data: List[Dict]):
        """
        Save symbols to database
        """
        try:
            exchange = Exchange.objects.using('fyers').get(code=exchange_code)
            instrument = Instrument.objects.using('fyers').get(code=instrument_code)
            
            created_count = 0
            updated_count = 0
            error_count = 0
            
            logger.info(f"Saving {len(symbols_data)} symbols to database...")
            
            for idx, data in enumerate(symbols_data, start=1):
                try:
                    # Validate data
                    if not data.get('scrip_code') or not data.get('symbol_details'):
                        error_count += 1
                        continue
                    
                    symbol, created = Symbol.objects.using('fyers').update_or_create(
                        exchange=exchange,
                        instrument=instrument,
                        symbol_code=data['scrip_code'],
                        defaults={
                            'symbol_name': data['scrip_name'] or data['scrip_code'],
                            'fyers_symbol': data['symbol_details'],
                            'isin': data.get('isin', ''),
                            'lot_size': data.get('lot_size', 1),
                            'tick_size': data.get('tick_size', 0.05),
                            'is_active': True,
                        }
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                    
                    # Log progress every 500 symbols
                    if idx % 500 == 0:
                        logger.info(f"Progress: {idx}/{len(symbols_data)} symbols processed...")
                
                except Exception as symbol_error:
                    error_count += 1
                    logger.warning(f"Error saving symbol {data.get('scrip_code', 'unknown')}: {symbol_error}")
                    continue
            
            logger.info(
                f"Symbols saved: {created_count} created, {updated_count} updated, "
                f"{error_count} errors"
            )
            return created_count, updated_count
        
        except Exchange.DoesNotExist:
            logger.error(f"Exchange {exchange_code} not found in database")
            return 0, 0
        except Instrument.DoesNotExist:
            logger.error(f"Instrument {instrument_code} not found in database")
            return 0, 0
        except Exception as e:
            logger.error(f"Error saving symbols: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0, 0
    
    def get_symbol_stats(self) -> Dict:
        """Get statistics about symbols in database"""
        try:
            stats = {
                'total_symbols': Symbol.objects.using('fyers').count(),
                'active_symbols': Symbol.objects.using('fyers').filter(is_active=True).count(),
                'by_exchange': {},
                'by_instrument': {},
            }
            
            # Count by exchange
            exchanges = Exchange.objects.using('fyers').all()
            for exchange in exchanges:
                count = Symbol.objects.using('fyers').filter(
                    exchange=exchange,
                    is_active=True
                ).count()
                stats['by_exchange'][exchange.code] = count
            
            # Count by instrument
            instruments = Instrument.objects.using('fyers').all()
            for instrument in instruments:
                count = Symbol.objects.using('fyers').filter(
                    instrument=instrument,
                    is_active=True
                ).count()
                stats['by_instrument'][instrument.code] = count
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting symbol stats: {e}")
            return {}