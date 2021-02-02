# type: ignore
import multiprocessing
import os
from typing import Dict

from prometheus_client import Counter, Histogram
from prometheus_client.metrics import MetricWrapperBase
from prometheus_client.utils import INF

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
            Histogram('sentrix_request_duration_seconds', 'Flask request duration',
                      ['method', 'endpoint'], buckets=buckets))
        self.request_count = self._prepare(Counter('sentrix_request_count', 'Flask request count',
                                                   ['method', 'endpoint', 'http_status']))

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


prometheus = Prometheus()
