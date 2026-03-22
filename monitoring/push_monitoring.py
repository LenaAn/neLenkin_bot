from prometheus_client import CollectorRegistry, Gauge, push_to_gateway


async def push_dau():
    count = 25
    registry = CollectorRegistry()
    g = Gauge('daily_active_users', 'Daily active users', registry=registry)
    g.set(count)

    push_to_gateway('localhost:9091', job='telegram_bot', registry=registry)
