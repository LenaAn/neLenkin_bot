import logging

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

registry = CollectorRegistry()

monitoring_logger = logging.getLogger(__name__)
monitoring_logger.setLevel(logging.DEBUG)


async def push_users_started_bot(users_count: int) -> None:
    g = Gauge('users_started_bot', 'Total users who started the bot', registry=registry)
    g.set(users_count)
    push_to_gateway('localhost:9091', job='nelenkin-bot', registry=registry)


async def push_users_failed_broadcast(users_count: int) -> None:
    g = Gauge('users_failed_broadcast',
              'Users failed during a broadcast out of all users who started the bot', registry=registry)
    g.set(users_count)

    push_to_gateway('localhost:9091', job='nelenkin-bot', registry=registry)


async def push_patreon_patrons(users_count: int) -> None:
    monitoring_logger.debug(f'pushing patreon_patrons: {users_count}')
    g = Gauge('patreon_patrons',
              'Active paying > 0 Patreon patrons', registry=registry)
    g.set(users_count)

    push_to_gateway('localhost:9091', job='nelenkin-bot', registry=registry)


async def push_boosty_patrons(users_count: int) -> None:
    monitoring_logger.debug(f'pushing boosty_patrons: {users_count}')

    g = Gauge('boosty_patrons',
              'Active paying > 0 Boosty patrons', registry=registry)
    g.set(users_count)

    push_to_gateway('localhost:9091', job='nelenkin-bot', registry=registry)
