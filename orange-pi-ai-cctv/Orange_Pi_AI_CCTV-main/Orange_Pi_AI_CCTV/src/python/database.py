# src/python/database.py
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class DatabasePool:
    def __init__(self, host: str, port: int, user: str, password: str, 
                 database: str, min_connections: int = 2, max_connections: int = 10):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connections = []
        
        self._init_pool()
    
    def _init_pool(self):
        for _ in range(self.min_connections):
            conn = psycopg2.connect(
                host=self.host, port=self.port, user=self.user,
                password=self.password, database=self.database,
                cursor_factory=RealDictCursor
            )
            self.connections.append(conn)
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            if self.connections:
                conn = self.connections.pop()
            else:
                conn = psycopg2.connect(
                    host=self.host, port=self.port, user=self.user,
                    password=self.password, database=self.database,
                    cursor_factory=RealDictCursor
                )
            yield conn
            self.connections.append(conn)
        except Exception as e:
            if conn:
                conn.close()
            raise e
    
    def close_all(self):
        for conn in self.connections:
            conn.close()
        self.connections.clear()

class AnalyticsQueries:
    @staticmethod
    def get_daily_summary(db_pool: DatabasePool, date: Optional[datetime] = None) -> Dict:
        if date is None:
            date = datetime.now()
        
        with db_pool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        object_type,
                        COUNT(*) as count,
                        AVG(confidence) as avg_confidence
                    FROM detections
                    WHERE DATE(timestamp) = %s
                    GROUP BY object_type
                    ORDER BY count DESC
                """, (date.date(),))
                
                results = cur.fetchall()
                
                return {
                    'date': date.date(),
                    'detections': results,
                    'total_detections': sum(r['count'] for r in results)
                }
    
    @staticmethod
    def get_hourly_activity(db_pool: DatabasePool, camera_id: int, 
                           hours: int = 24) -> List[Dict]:
        with db_pool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        DATE_TRUNC('hour', timestamp) as hour,
                        COUNT(*) as detections,
                        COUNT(DISTINCT track_id) as unique_objects
                    FROM detections
                    WHERE camera_id = %s 
                    AND timestamp > NOW() - INTERVAL '%s hours'
                    GROUP BY DATE_TRUNC('hour', timestamp)
                    ORDER BY hour DESC
                """, (camera_id, hours))
                
                return cur.fetchall()
    
    @staticmethod
    def get_peak_times(db_pool: DatabasePool, object_type: Optional[str] = None) -> List[Dict]:
        with db_pool.get_connection() as conn:
            with conn.cursor() as cur:
                if object_type:
                    cur.execute("""
                        SELECT 
                            EXTRACT(HOUR FROM timestamp) as hour,
                            COUNT(*) as count
                        FROM detections
                        WHERE object_type = %s
                        GROUP BY EXTRACT(HOUR FROM timestamp)
                        ORDER BY count DESC
                        LIMIT 5
                    """, (object_type,))
                else:
                    cur.execute("""
                        SELECT 
                            EXTRACT(HOUR FROM timestamp) as hour,
                            COUNT(*) as count
                        FROM detections
                        GROUP BY EXTRACT(HOUR FROM timestamp)
                        ORDER BY count DESC
                        LIMIT 5
                    """)
                
                return cur.fetchall()
    
    @staticmethod
    def get_anomaly_detection(db_pool: DatabasePool, hours: int = 24, 
                             threshold: float = 2.0) -> List[Dict]:
        """Detect anomalous detection patterns using Z-score"""
        with db_pool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    WITH hourly_counts AS (
                        SELECT 
                            DATE_TRUNC('hour', timestamp) as hour,
                            COUNT(*) as count
                        FROM detections
                        WHERE timestamp > NOW() - INTERVAL '%s hours'
                        GROUP BY DATE_TRUNC('hour', timestamp)
                    ),
                    stats AS (
                        SELECT 
                            AVG(count) as mean,
                            STDDEV(count) as stddev
                        FROM hourly_counts
                    )
                    SELECT 
                        h.hour,
                        h.count,
                        s.mean,
                        s.stddev,
                        ABS(h.count - s.mean) / NULLIF(s.stddev, 0) as zscore
                    FROM hourly_counts h, stats s
                    WHERE ABS(h.count - s.mean) / NULLIF(s.stddev, 0) > %s
                    ORDER BY zscore DESC
                """, (hours, threshold))
                
                return cur.fetchall()

class DataRetention:
    def __init__(self, db_pool: DatabasePool, retention_days: int = 30):
        self.db_pool = db_pool
        self.retention_days = retention_days
    
    def cleanup_old_data(self) -> Dict[str, int]:
        """Delete data older than retention period"""
        deleted_counts = {}
        
        with self.db_pool.get_connection() as conn:
            with conn.cursor() as cur:
                # Clean detections
                cur.execute("""
                    DELETE FROM detections 
                    WHERE timestamp < NOW() - INTERVAL '%s days'
                    RETURNING COUNT(*)
                """, (self.retention_days,))
                deleted_counts['detections'] = cur.fetchone()[0]
                
                # Clean alerts
                cur.execute("""
                    DELETE FROM alerts 
                    WHERE timestamp < NOW() - INTERVAL '%s days'
                    RETURNING COUNT(*)
                """, (self.retention_days,))
                deleted_counts['alerts'] = cur.fetchone()[0]
                
                # Clean face events
                cur.execute("""
                    DELETE FROM face_events 
                    WHERE timestamp < NOW() - INTERVAL '%s days'
                    RETURNING COUNT(*)
                """, (self.retention_days,))
                deleted_counts['face_events'] = cur.fetchone()[0]
                
                conn.commit()
        
        return deleted_counts
    
    def archive_to_csv(self, output_dir: str, date_range: tuple) -> bool:
        """Archive data to CSV files"""
        import csv
        import os
        
        start_date, end_date = date_range
        
        tables = ['detections', 'alerts', 'face_events', 'license_plates']
        
        for table in tables:
            with self.db_pool.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"""
                        SELECT * FROM {table}
                        WHERE timestamp BETWEEN %s AND %s
                    """, (start_date, end_date))
                    
                    rows = cur.fetchall()
                    
                    if rows:
                        filename = f"{output_dir}/{table}_{start_date.date()}_{end_date.date()}.csv"
                        os.makedirs(output_dir, exist_ok=True)
                        
                        with open(filename, 'w', newline='') as f:
                            if rows:
                                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                                writer.writeheader()
                                writer.writerows(rows)
        
        return True
