if not hasattr(context.aq_explicit, 'rss'):
    raise 'NotFound', 'This object does not support RSS export'

context.REQUEST.RESPONSE.setHeader('Content-Type', 'text/xml;charset=UTF-8')

return context.rss()
