from zope.interface import Interface

class INewsProvider(Interface):
    """is able to provide news items"""

    def get_items(self, number):
        """returns a set of the most current items"""

class INewsItemReference(Interface):

    def id(self):
        """get the ID of this reference"""

    def title(self):
        """get the title of this reference"""

    def description(self, maxchars):
        """get the description (from metadata) of this reference"""

    def intro(self, maxchars):
        """get the intro of this reference"""

    def link(self):
        """get the link(url) of this reference"""
        
    def creation_datetime(self):
        """get the creationdatetime of this reference"""
        
    def start_datetime(self):
        """get the sdt of this reference"""
        
    def end_datetime(self):
        """get the edt of this reference"""

    def location(self):
        """get the  of this reference"""

    def get_news_item(self):
        """get the real item"""
