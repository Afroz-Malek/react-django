"""
Database Router for StockstarCapital Multi-Database Architecture

This router ensures that:
- stockstarauthversionone app uses 'default' database
- fyers_auth and fyers_historical_data apps use 'fyers' database
- Built-in Django apps (auth, contenttypes, sessions, admin) use 'default' database
"""

import logging

logger = logging.getLogger(__name__)


class MultiDatabaseRouter:
    """
    Route models to appropriate databases based on app labels
    """

    def db_for_read(self, model, **hints):
        """
        Determine which database to use for read operations
        """
        app_label = model._meta.app_label
        
        # Platform authentication - default database
        if app_label == 'stockstarauthversionone':
            return 'default'
        
        # FYERS apps - fyers database
        if app_label in ['fyers_auth', 'fyers_historical_data']:
            return 'fyers'
        
        # Built-in Django apps - default database
        if app_label in ['auth', 'contenttypes', 'sessions', 'admin']:
            return 'default'
        
        # Default: use default database
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Determine which database to use for write operations
        """
        app_label = model._meta.app_label
        
        # Platform authentication - default database
        if app_label == 'stockstarauthversionone':
            return 'default'
        
        # FYERS apps - fyers database
        if app_label in ['fyers_auth', 'fyers_historical_data']:
            return 'fyers'
        
        # Built-in Django apps - default database
        if app_label in ['auth', 'contenttypes', 'sessions', 'admin']:
            return 'default'
        
        # Default: use default database
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations only if both objects are in the same database
        """
        db1 = self.db_for_read(obj1.__class__)
        db2 = self.db_for_read(obj2.__class__)
        
        if db1 and db2:
            return db1 == db2
        
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Control which migrations run on which database
        """
        # Platform authentication - only on default database
        if app_label == 'stockstarauthversionone':
            return db == 'default'
        
        # FYERS apps - only on fyers database
        if app_label in ['fyers_auth', 'fyers_historical_data']:
            return db == 'fyers'
        
        # Built-in Django apps - only on default database
        if app_label in ['auth', 'contenttypes', 'sessions', 'admin']:
            return db == 'default'
        
        # Default: allow on default database
        return db == 'default'