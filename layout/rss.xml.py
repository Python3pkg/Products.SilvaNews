if not hasattr(self.aq_explicit, 'rss'):
    raise 'NotFound', 'This object does not support RSS export'

return self.rss()
