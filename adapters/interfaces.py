from Interface import Interface

class INewsProvider(Interface):
    """is able to provide news items"""

    def get_items(self, number):
        """returns a set of the most current items"""
