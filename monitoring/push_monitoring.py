from prometheus_client import CollectorRegistry, Gauge, push_to_gateway


async def push_users_started_bot(users_count: int) -> None:
    registry = CollectorRegistry()
    g = Gauge('users_started_bot', 'Total users who started the bot', registry=registry)
    g.set(users_count)

    push_to_gateway('localhost:9091', job='nelenkin-bot', registry=registry)


async def push_users_failed_broadcast(users_count: int) -> None:
    registry = CollectorRegistry()
    g = Gauge('users_failed_broadcast',
              'Users failed during a broadcast out of all users who started the bot', registry=registry)
    g.set(users_count)

    push_to_gateway('localhost:9091', job='nelenkin-bot', registry=registry)
