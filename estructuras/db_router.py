"""
Router de base de datos para dirigir consultas específicas a Oracle
"""

class OracleRouter:
    """
    Router para dirigir consultas específicas de FID a la base de datos Oracle
    """
    
    route_app_labels = {'oracle_queries'}
    
    def db_for_read(self, model, **hints):
        """Dirigir lecturas de modelos específicos a Oracle"""
        if model._meta.app_label == 'oracle_queries':
            return 'oracle'
        return None
    
    def db_for_write(self, model, **hints):
        """No permitir escrituras en Oracle"""
        if model._meta.app_label == 'oracle_queries':
            return None  # No escrituras en Oracle
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """No permitir migraciones en Oracle"""
        if db == 'oracle':
            return False
        elif app_label == 'oracle_queries':
            return False
        return None