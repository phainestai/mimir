"""
Django settings package for mimir.

Environment-specific settings are loaded based on DJANGO_SETTINGS_MODULE or MIMIR_ENV.
"""
import os

# Determine which settings module to use
env = os.getenv('MIMIR_ENV', 'dev')

if env == 'prod':
    from .prod import *  # noqa: F401, F403
elif env == 'test':
    from .test import *  # noqa: F401, F403
else:
    from .dev import *  # noqa: F401, F403
