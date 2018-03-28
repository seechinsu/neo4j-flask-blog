from datetime import datetime
import uuid
from db import graph, Node, Relationship, calendar, GraphObject, Property, RelatedFrom, RelatedTo, RelatedObjects
from .post import Post

class Tag(GraphObject):
    __primarykey__ = 'name'

    uid = Property()
    name = Property()

    tagged = RelatedTo(Post)

    def __init__(self, name):
        self.name = name

    def find(self):
        tag = Tag.select(graph, self.name).first()
        return tag
