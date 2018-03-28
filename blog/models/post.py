from datetime import datetime
import uuid
from db import graph, Node, Relationship, calendar, GraphObject, Property, RelatedFrom, RelatedTo, RelatedObjects


# post class object
class Post(GraphObject):
    __primarykey__ = 'title'

    id = Property()
    title = Property()
    text = Property()
    timestamp = Property()
    date = Property()
    display_date = Property()

    def __init__(self, title, text):
        today = datetime.now()

        self.id = str(uuid.uuid4())
        self.title = title
        self.text = text
        self.timestamp = int(today.strftime("%H%M%S"))
        self.date = int(today.strftime("%Y%m%d"))
        self.display_date = today.strftime("%x")

    def find(self):
        post = Post.select(graph, self.title).first()
        return post

