# type: ignore
import multiprocessing
import os
from concurrent.futures import _base
from typing import Dict

from prometheus_client import Gauge, Summary, Counter, Histogram
from prometheus_client.metrics import MetricWrapperBase
from prometheus_client.utils import INF
from psycopg2._psycopg import cursor
from psycopg2.extras import execute_values

_queue: multiprocessing.Queue = None


def initialize_multiprocessing_metrics(queue):
    global _queue
    _queue = queue


class MetricProxy:
    """
    Metrics proxy used in child processes: this is queued to the parent process to update the actual metric
    """

    def __init__(self, name, labelvalues=None, labelkwargs=None):
        self.name = name
        self.labelvalues = labelvalues
        self.labelkwargs = labelkwargs
        self.action = None
        self.value = None

    def labels(self, *labelvalues, **labelkwargs):
        return MetricProxy(self.name, labelvalues=labelvalues, labelkwargs=labelkwargs)

    def set(self, v, values=None):
        self.action = 'set'
        self.value = v
        _queue.put(self)
        if values is not None:
            values.append((self.name, self.labelvalues[0] if self.labelvalues else '', v))

    def inc(self, amount=1):
        self.action = 'inc'
        self.value = amount
        _queue.put(self)

    def dec(self, amount=1):
        self.action = 'dec'
        self.value = amount
        _queue.put(self)

    def observe(self, v):
        self.action = 'observe'
        self.value = v
        _queue.put(self)

    def run(self, metric: MetricWrapperBase):
        if self.labelvalues or self.labelkwargs:
            m = metric.labels(*self.labelvalues, **self.labelkwargs)
        else:
            m = metric
        if self.action == 'set':
            m.set(self.value)
        elif self.action == 'inc':
            m.inc(amount=self.value)
        elif self.action == 'dec':
            m.dec(amount=self.value)
        elif self.action == 'observe':
            m.observe(self.value)


class Prometheus:

    def __init__(self):
        self._metrics: Dict[str, MetricWrapperBase] = dict()

        # http server metrics
        buckets = tuple(
            [.005, .01, .025, .05, .075, .1, .25, .5, .75, 1., 1.5, 2., 2.5, 3., 4., 5., 6., 7., 8., 9., 10., 12.,
             15., 18., 20., 30., 60., 120., INF])
        self.request_duration = self._prepare(
            Histogram('wakapi_request_duration_seconds', 'Flask request duration',
                      ['method', 'endpoint'], buckets=buckets))
        self.request_count = self._prepare(Counter('wakapi_request_count', 'Flask request count',
                                                   ['method', 'endpoint', 'http_status']))

        # metrics for backlog
        self.ocr_backlog = self._prepare(Gauge('wakapi_ocr_backlog', 'Number of pages to be OCRed', ['scope']))
        self.prediction_backlog = self._prepare(
            Gauge('wakapi_prediction_backlog', 'Number of pages to be predicted', ['scope']))
        self.control_backlog = self._prepare(
            Gauge('wakapi_control_backlog', 'Number of documents to be controlled', ['scope']))
        self.classification_backlog = self._prepare(
            Gauge('wakapi_classification_backlog', 'Number of documents to be classified', ['scope']))
        self.pdf_backlog = self._prepare(
            Gauge('wakapi_pdf_backlog', 'Number of documents PDF to be generated', ['scope']))
        self.export_backlog = self._prepare(
            Gauge('wakapi_export_backlog', 'Number of documents to be exported', ['scope']))
        self.documents_in_backlog = self._prepare(
            Gauge('wakapi_documents_in_backlog', 'Number of documents to be processed', ['scope']))
        self.documents_in_error = self._prepare(
            Gauge('wakapi_documents_in_error', 'Number of documents in error', ['scope']))
        self.processing_delay = self._prepare(Gauge('wakapi_processing_delay',
                                                    'Processing delay: estimated duration, in seconds, a new document would wait before it would start being processed',
                                                    []))

        # factory task creation delay
        self.factory_task_creation_delay = self._prepare(
            Gauge('wakapi_factory_last_update_delay', 'Number of seconds since factory last_update', []))

        # metrics for processors
        self.ocr_pages = self._prepare(Counter('wakapi_ocr_pages', 'Count of OCRed pages', ['scope']))
        self.prediction_pages = self._prepare(Counter('wakapi_prediction_pages', 'Count of predicted pages', ['scope']))
        self.control_documents = self._prepare(Counter('wakapi_control_documents', 'Count of controlled documents',
                                                       ['scope']))
        self.pdf_generations = self._prepare(Counter('wakapi_pdf_generations', 'Count of generated PDFs',
                                                     ['scope']))
        self.classification_documents = self._prepare(Counter('wakapi_classification_documents',
                                                              'Count of classified documents', ['scope']))

        # metrics for model generation
        self.model_generation = self._prepare(
            Gauge('wakapi_model_generation',
                  'Timestamp of the last successful Classella model generation, in milliseconds since epoch',
                  ['scope', 'type']))
        self.model_generation_duration = self._prepare(
            Gauge('wakapi_model_generation_duration',
                  'Duration of the last successful Classella model generation, in milliseconds',
                  ['scope', 'type']))
        self.model_generation_compressed_size = self._prepare(
            Gauge('wakapi_model_generation_compressed_size',
                  'Compressed size of the last successful Classella model, in bytes',
                  ['scope', 'type']))
        self.model_generation_uncompressed_size = self._prepare(
            Gauge('wakapi_model_generation_uncompressed_size',
                  'Unompressed size of the last successful Classella model, in bytes',
                  ['scope', 'type']))
        self.model_generation_error = self._prepare(
            Gauge('wakapi_model_generation_error',
                  'Timestamp of the last Classella model generation error, in milliseconds since epoch',
                  ['scope', 'type', 'error']))
        self.model_size = self._prepare(
            Gauge('wakapi_model_size', 'Size in bytes of the Classella models loaded in memory', ['scope']))

        # metrics for messenger
        self.collector_sent_messages = self._prepare(
            Counter('wakapi_collector_sent_messages', 'Number of messages sent to collector',
                    ['topic', 'scope']))
        self.collector_sent_documents = self._prepare(Counter('wakapi_collector_sent_documents',
                                                              'Number of documents sent to collector',
                                                              ['topic', 'scope']))
        self.messenger_processed_messages = self._prepare(Counter('wakapi_messenger_processed_messages',
                                                                  'Number of messages processed by messenger',
                                                                  ['group', 'topic', 'scope']))
        self.messenger_failed_messages = self._prepare(Counter('wakapi_messenger_failed_messages',
                                                               'Number of messages failed by messenger',
                                                               ['group', 'topic', 'scope']))
        self.messenger_processed_documents = self._prepare(Counter('wakapi_messenger_processed_documents',
                                                                   'Number of documents processed by messenger',
                                                                   ['group', 'topic', 'scope']))
        self.messenger_messages_sent = self._prepare(
            Counter('wakapi_messenger_sent_messages', 'Number of messages sent to messenger',
                    ['topic', 'scope']))

        # metrics for collector
        self.collector_processed_messages = self._prepare(Counter('wakapi_collector_processed_messages',
                                                                  'Number of messages processed by collector',
                                                                  ['group', 'topic', 'scope']))
        self.collector_failed_messages = self._prepare(Counter('wakapi_collector_failed_messages',
                                                               'Number of messages failed by collector',
                                                               ['group', 'topic', 'scope']))
        self.collector_processed_documents = self._prepare(Counter('wakapi_collector_processed_documents',
                                                                   'Number of documents processed by collector',
                                                                   ['group', 'topic', 'scope']))
        self.collector_ignored_documents = self._prepare(Counter('wakapi_collector_ignored_documents',
                                                                 'Number of documents ignored by collector',
                                                                 ['group', 'topic', 'scope']))
        self.collector_deleted_documents = self._prepare(Counter('wakapi_collector_deleted_documents',
                                                                 'Number of documents deleted by collector',
                                                                 ['group', 'topic', 'scope']))

        # metrics for company search
        self.cascade_search_duration = self._prepare(
            Histogram('wakapi_cascade_search_seconds', 'Cascade Search duration',
                      ['service'], buckets=buckets))

        # metrics for connection pools
        self.pool_connection = self._prepare(Summary('wakapi_pool_connection',
                                                     'Time spent waiting on pool for a connection, in seconds',
                                                     ['pool']))
        self.pool_exhaustion = self._prepare(Counter('wakapi_pool_exhaustion',
                                                     'Number of times the pool was exhausted when acquiring a connection',
                                                     ['pool']))
        self.database_connection_duration = self._prepare(Summary('wakapi_database_connection_duration',
                                                                  'Time spent connecting to the database, in seconds',
                                                                  ['pool']))
        self.database_connection_init_duration = self._prepare(Summary('wakapi_database_connection_init_duration',
                                                                       'Time spent initializing the database connection, in seconds',
                                                                       ['pool']))
        self.pool_close_duration = self._prepare(Summary('wakapi_pool_close_duration',
                                                         'Time spent closing a connection pool, in seconds',
                                                         ['pool']))
        self.database_connection_discard_duration = self._prepare(Summary('wakapi_database_connection_discard_duration',
                                                                          'Time spent discarding the database connection, in seconds',
                                                                          ['pool']))
        self.pool_size = self._prepare(
            Gauge('wakapi_pool_size', 'Number of connections currently in the pool', ['pool']))
        self.pool_max_size = self._prepare(
            Gauge('wakapi_pool_max_size', 'Maximum number of connections in the pool', ['pool']))
        self.pool_fallback_connections = self._prepare(Counter('wakapi_pool_fallback_connections',
                                                               'Counter of connection fallbacks from standby to primary',
                                                               ['pool']))

    def run(self, proxy: MetricProxy):
        metric = self._metrics[proxy.name]
        proxy.run(metric)

    def _prepare(self, metric):
        def _proxify_metric():
            proxy = MetricProxy(metric._name)
            metric.labels = proxy.labels

        if hasattr(os, 'register_at_fork'):
            os.register_at_fork(after_in_child=_proxify_metric)

        self._metrics[metric._name] = metric
        return metric

    def _compute(self, db, scope):
        with db.ro_autocommit_cursor(options={'statement_timeout': 60000}) as cur:
            cur.execute(f'''
                SELECT * FROM {scope}.get_scope_stats()
            ''')
            return cur.fetchone()

    def compute_db_metrics(self, db, nb_workers):
        from task.executor import Executor
        executor: Executor = Executor('prometheus', nb_workers, nb_workers)
        values = list()
        with db.ro_autocommit_cursor() as cur:
            cur.execute('''
                SELECT scope FROM _internal.settings INNER JOIN pg_namespace ON nspname = scope
            ''')
            scopes = [r['scope'] for r in cur.fetchall()]
            cur.execute('''
                SELECT EXTRACT(EPOCH FROM (NOW() - (value->>'last_run')::timestamptz)) delay_seconds
                FROM _internal.status
                WHERE name = 'factory_tasks'
            ''')
            r = cur.fetchone()
            if r:
                delay_seconds = r['delay_seconds']
                self.factory_task_creation_delay.labels().set(0 if delay_seconds < 0 else delay_seconds, values)
        futures: Dict[str, _base.Future] = dict()
        for scope in scopes:
            futures[scope] = executor.submit('', 0, self._compute, *(db, scope))
        for scope, future in futures.items():
            r = future.result()
            scope = r['scope']
            no_quota = r['no_quota']
            self.ocr_backlog.labels(scope).set(0 if no_quota else r['ocr_backlog'], values)
            self.prediction_backlog.labels(scope).set(0 if no_quota else r['prediction_backlog'], values)
            self.control_backlog.labels(scope).set(0 if no_quota else r['control_backlog'], values)
            self.classification_backlog.labels(scope).set(0 if no_quota else r['classification_backlog'], values)
            self.pdf_backlog.labels(scope).set(0 if no_quota else r['pdf_backlog'], values)
            self.export_backlog.labels(scope).set(0 if no_quota else r['export_backlog'], values)
            self.documents_in_backlog.labels(scope).set(0 if no_quota else r['documents_in_backlog'], values)
            self.documents_in_error.labels(scope).set(0 if no_quota else r['documents_in_error'], values)
        self.compute_processing_delay(db, values)
        # persist db metrics
        with db.rw_autocommit_cursor() as cur:
            execute_values(cur, '''
                INSERT INTO _internal.prometheus_db_metrics(name, scope, value)
                VALUES %s
                ON CONFLICT(scope, name)
                DO UPDATE
                SET value = EXCLUDED.value
                ''', values, page_size=10000)
            cur.execute('''
                DELETE FROM _internal.prometheus_db_metrics
                WHERE scope != ALL(%(scopes)s::text[])
            ''', {'scopes': scopes + ['']})
        executor.shutdown()

    def compute_processing_delay(self, db, values: list):
        with db.ro_autocommit_cursor() as cur:
            # compute processing delay: this is a rough estimation based on the maximum number of operations executed
            # over a 5-minute interval during the last 72 hours
            ops = Prometheus._get_ops_by_kind(cur, '72 hours', '5 minutes')
            if len(ops) > 0:
                # get backlog for operation kinds from prometheus metrics
                backlog = {'OCR': sum(s.value for s in self.ocr_backlog.collect()[0].samples),
                           'PREDICTION': sum(s.value for s in self.prediction_backlog.collect()[0].samples),
                           'CONTROL': sum(s.value for s in self.control_backlog.collect()[0].samples),
                           'CLASSELLA': sum(s.value for s in self.classification_backlog.collect()[0].samples),
                           'PDF': sum(s.value for s in self.pdf_backlog.collect()[0].samples)}

                # for each operation kind, we compute the expected duration as backlog[kind] / ops[kind]
                duration = {kind: 0 if ops[kind] == 0 else backlog[kind] / ops[kind] for kind in ops.keys()}

                # the processing delay is the max duration, considering perfect concurrency
                processing_delay_value = max(duration.values())
            else:
                processing_delay_value = 0
            self.processing_delay.labels().set(processing_delay_value, values)

    def fetch_metrics_from_db(self, db):
        with db.ro_autocommit_cursor() as cur:
            cur.execute('''
                    SELECT scope, name, value
                    FROM _internal.prometheus_db_metrics
                ''')
            for r in cur.fetchall():
                name, scope, value = r['name'], r['scope'], r['value']
                if scope:
                    self._metrics[name].labels(scope).set(value)
                else:
                    self._metrics[name].set(value)

    def get_model_generation_stats(self, db):
        with db.ro_autocommit_cursor() as cur:
            cur.execute('''
                SELECT scope, type, EXTRACT(EPOCH FROM ended) * 1000 generation,
                    EXTRACT(EPOCH FROM (ended - started)) * 1000 duration,
                    error,
                    compressed_size,
                    uncompressed_size
                FROM _internal.model_stat
            ''')
            for r in cur.fetchall():
                scope = r['scope']
                type = r['type']
                t = r['generation']
                error = r['error']
                if error and error != 'abort' and error != 'timeout':
                    error = 'failure'
                if error is None:
                    self.model_generation.labels(scope, type).set(t)
                    self.model_generation_duration.labels(scope, type).set(r['duration'])
                    if r['compressed_size']:
                        self.model_generation_compressed_size.labels(scope, type).set(r['compressed_size'])
                    if r['uncompressed_size']:
                        self.model_generation_uncompressed_size.labels(scope, type).set(r['uncompressed_size'])
                self.model_generation_error.labels(scope, type, 'abort').set(t if error == 'abort' else 0)
                self.model_generation_error.labels(scope, type, 'timeout').set(t if error == 'timeout' else 0)
                self.model_generation_error.labels(scope, type, 'failure').set(t if error == 'failure' else 0)

    @staticmethod
    def _get_ops_by_kind(cur: cursor, long_interval: str, short_interval: str) -> Dict[str, float]:
        cur.execute('''
            WITH tstart(t) AS (
                SELECT to_timestamp(floor(EXTRACT(EPOCH FROM NOW()) / EXTRACT(EPOCH FROM INTERVAL '{short_interval}'))
                    * EXTRACT(EPOCH FROM INTERVAL '{short_interval}'))
            ),
            intervals(t0, t1) AS (
                SELECT generate_series(t - INTERVAL '{long_interval}', t, INTERVAL '{short_interval}'),
                    generate_series(t - INTERVAL '{long_interval}' + INTERVAL '{short_interval}', t + INTERVAL '{short_interval}', INTERVAL '{short_interval}')
                FROM tstart
            ),
            defaults(kind) AS (
                VALUES('OCR'), ('PREDICTION'), ('CONTROL'), ('CLASSELLA'), ('PDF')
            ),
            ops_by_interval(t0, t1, kind, ops) AS (
                SELECT t0, t1, d.kind,
                    SUM(COALESCE(CASE WHEN d.kind IN ('CONTROL', 'CLASSELLA', 'PDF') THEN 1 ELSE nb_pages END, 0)
                    -- adjust using ratio of operation time interval overlapping considered time interval
                    * EXTRACT (EPOCH FROM LEAST(ended, t1) - GREATEST(started, t0)) / EXTRACT (EPOCH FROM ended - started))
                     / EXTRACT(EPOCH FROM t1 - t0) ops
                FROM defaults d
                LEFT JOIN intervals i ON TRUE
                LEFT JOIN operation o ON o.kind = d.kind
                WHERE (ended >= t0 AND ended < t1) OR (started >= t0 AND started < t1)
                GROUP BY t0, t1, d.kind
            )
            SELECT kind, ops FROM ops_by_interval WHERE t0 = (SELECT t0 FROM ops_by_interval GROUP BY t0 ORDER BY SUM(ops) DESC LIMIT 1)
        '''.format(long_interval=long_interval, short_interval=short_interval))
        return {r['kind']: r['ops'] for r in cur.fetchall()}


prometheus = Prometheus()
