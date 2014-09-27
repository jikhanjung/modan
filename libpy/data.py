class Link:
  def __init__(self, id=0, pubitem_id=0, uri='', created_at=''):
    self.id = id
    self.pubitem_id = pubitem_id
    self.uri = uri
    self.created_at = created_at
 
class Comment:
  def __init__(self, id=0, pubitem_id=0, title='', textbody='', created_at=''):
    self.id = id
    self.pubitem_id = pubitem_id
    self.title = title
    self.textbody = textbody
    self.created_at = created_at
 
class Tag:
  def __init__(self, id=0, category='', name='', created_at=''):
    self.id = id
    self.category = category
    self.name = name
    self.created_at = created_at
    self.articles = []
