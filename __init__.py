"""QGIS plugin entry point for 02Agent Smart Modeler (QGIS 4+)."""


def classFactory(iface):
    """Instantiates the 02Agent Smart Modeler plugin."""
    from .main_plugin import SmartModelerPlugin

    return SmartModelerPlugin(iface)
