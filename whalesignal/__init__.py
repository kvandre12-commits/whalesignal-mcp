"""WhaleSignal MCP — composite market-intelligence tools on top of the Unusual Whales API.

This is *not* a dumb passthrough of the Unusual Whales REST API. It fuses several
proprietary datasets (options flow alerts, net premium, dark pool, gamma exposure,
market tide, congressional trades) into a handful of explainable, decision-ready
signals exposed as Model Context Protocol (MCP) tools.
"""

__version__ = "0.1.0"
