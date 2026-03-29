import logging

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

monitoring_logger = logging.getLogger(__name__)
monitoring_logger.setLevel(logging.DEBUG)


# todo: after restart that will push zeroes for metrics that are not populated
# pre-populate the metrics with correct values on init
class MetricsPusher:
    def __init__(self):
        self.registry = CollectorRegistry()
        self.users_started_bot_gauge = Gauge(
            'users_started_bot',
            'Total users who started the bot',
            registry=self.registry)
        self.users_failed_broadcast_gauge = Gauge(
            'users_failed_broadcast',
            'Users failed during a broadcast out of all users who started the bot',
            registry=self.registry)
        self.patreon_patrons_gauge = Gauge(
            'patreon_patrons',
            'Active paying > 0 Patreon patrons',
            registry=self.registry)
        self.boosty_patrons_gauge = Gauge(
            'boosty_patrons',
            'Active paying > 0 Boosty patrons',
            registry=self.registry)

    def push(self):
        push_to_gateway('localhost:9091', job='nelenkin-bot', registry=self.registry)

    async def push_users_started_bot(self, users_count: int) -> None:
        monitoring_logger.debug(f'pushing users_started_bot: {users_count}')
        self.users_started_bot_gauge.set(users_count)
        self.push()

    async def push_users_failed_broadcast(self, users_count: int) -> None:
        monitoring_logger.debug(f'pushing users_failed_broadcast: {users_count}')
        self.users_failed_broadcast_gauge.set(users_count)
        self.push()

    async def push_patreon_patrons(self, users_count: int) -> None:
        monitoring_logger.debug(f'pushing patreon_patrons: {users_count}')
        self.patreon_patrons_gauge.set(users_count)
        self.push()

    async def push_boosty_patrons(self, users_count: int) -> None:
        monitoring_logger.debug(f'pushing boosty_patrons: {users_count}')
        self.boosty_patrons_gauge.set(users_count)
        self.push()


metrics = MetricsPusher()
