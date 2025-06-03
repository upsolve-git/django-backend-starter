from .base import *

DEBUG = True

# Additional apps for development only
INSTALLED_APPS += [
 #   'debug_toolbar',
]

# Additional middleware for development
MIDDLEWARE += [
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# Show emails in console during development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Allow all hosts for development
ALLOWED_HOSTS = ['*']

# Django Debug Toolbar
INTERNAL_IPS = [
   # '127.0.0.1',
]