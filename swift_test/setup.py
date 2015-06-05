from setuptools import setup, find_packages


setup(
    name="swift",
    packages=find_packages(),
    author="pothik",
    version="1.0",
    entry_points={
        "paste.app_factory": [
            "proxy = swift.proxy.server:app_factory"
        ],
        "paste.filter_factory": [
            "proxy_logging = swift.common.middleware.proxy_logging:filter_factory",
            "dlo = swift.common.middleware.dlo:filter_factory",
            "slo = swift.common.middleware.slo:filter_factory",
            "account_quotas = swift.common.middleware.account_quotas:filter_factory",
            "container_quotas = swift.common.middleware.container_quotas:filter_factory",
            "tempauth = swift.common.middleware.tempauth:filter_factory",
            "ratelimit = swift.common.middleware.ratelimit:filter_factory",
            "tempurl = swift.common.middleware.tempurl:filter_factory",
            "bulk = swift.common.middleware.bulk:filter_factory",
            "container_sync = swift.common.middleware.container_sync:filter_factory",
            "memcache = swift.common.middleware.memcache:filter_factory",
            "healthcheck = swift.common.middleware.healthcheck:filter_factory",
            "gatekeeper = swift.common.middleware.gatekeeper:filter_factory",
            "catch_errors = swift.common.middleware.catch_errors:filter_factory"
        ]
    }
)
