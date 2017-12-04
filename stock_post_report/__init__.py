# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

try:
    from . import wizard
except ImportError:
    import logging
    logging.getLogger(__name__).warn(
        "report_xls not available in addons path")
