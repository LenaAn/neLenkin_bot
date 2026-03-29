import logging

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

monitoring_logger = logging.getLogger(__name__)
monitoring_logger.setLevel(logging.DEBUG)


# todo: after restart that will push zeroes for metrics that are not populated
# pre-populate the metrics with correct values on init
class MetricsPusher:
    def __init__(self):
        self.registry = CollectorRegistry()
        self._gauges = {
            "users_started_bot": Gauge(
                'users_started_bot',
                'Total users who started the bot',
                registry=self.registry),
            "users_failed_broadcast": Gauge(
                'users_failed_broadcast',
                'Users failed during a broadcast out of all users who started the bot',
                registry=self.registry),
            "patreon_patrons": Gauge(
                'patreon_patrons',
                'Active paying > 0 Patreon patrons',
                registry=self.registry),
            "boosty_patrons": Gauge(
                'boosty_patrons',
                'Active paying > 0 Boosty patrons',
                registry=self.registry),
        }

    def set(self, metric_name: str, value: int):
        if metric_name not in self._gauges:
            raise ValueError(f"Unknown metric: {metric_name}")
        self._gauges[metric_name].set(value)

    def push(self):
        push_to_gateway('localhost:9091', job='nelenkin-bot', registry=self.registry)


metrics = MetricsPusher()
