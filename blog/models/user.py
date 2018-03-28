from datetime import datetime
import uuid
from db import graph, Node, Relationship, calendar, GraphObject, Property, RelatedFrom, RelatedTo, RelatedObjects
from .post import Post
from .tag import Tag

# creates a user class
class User(GraphObject):
    __primarykey__ = 'username'

    uid = Property()
    username = Property()
    password = Property()

    published = RelatedTo(Post)

    # finds a user node using username and searching the node's username property
    def find(self):
        user = User.select(graph, self.username).first()
        return user

    # registers a user node with username and password by creating a node if the username cannot be found
    def register(self, password):
        if not self.find():
            # user = Node("User", username=self.username, password=bcrypt.encrypt(password))
            self.password = password
            graph.create(self)
            return True
        return False

    # authenticates the user using password
    def verify_password(self, password):
        user = self.find()

        if not user:
            return False
            # return bcrypt.verify(password, user["password"])
        return password == user.password

    # creates a post with title, tags, and text and relates it to the user
    def add_post(self, title, tags, text):
        user = self.find()
        today = datetime.now()

        post = Post(title, text)
        graph.create(post)
        user.published.add(post)
        graph.push(user)

        today_node = calendar.date(today.year, today.month, today.day).day
        graph.create(Relationship(post.__ogm__.node, "ON", today_node))

        tags = [x.strip() for x in tags.lower().split(",")]

        for tag in tags:
            t = Tag(name=tag)
            graph.merge(t)
            t.tagged.add(post)
            graph.push(t)


    # creates a like relationship
    def like_post(self, post_id):
        user = self.find()

        # finds the post node by post id
        post = graph.find_one("Post", "id", post_id)

        # creates a LIKES relationships from the user node to the post node
        rel = Relationship(user, "LIKES", post)

        # merge is used here instead of create as neo4j will only create new distinct tags
        # existing tags will just get an additional TAGGED relationship from it to the post node
        # find_one was used so the merge below will not create new posts when creating the relationship
        graph.merge(rel)

    # returns n number of recent posts by the user as a list of dictionaries with post name and tags for post
    def recent_posts(self,n):

        # query returns post node and tags that are common
        # need to refactor the query using the OGM in py2neo v3
        query = """
        MATCH (user:User)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag)
        WHERE user.username = {username}
        RETURN post, COLLECT(tag.name) AS tags
        ORDER BY post.timestamp DESC LIMIT {n}
        """

        return graph.run(query,username=self.username,n=n).data()

    # returns n users that have published posts with the same tags
    def similar_users(self,n):

        # query returns user node and the tags that are common between user1 and user2
        # need to refactor the query using the OGM in py2neo v3
        query = """
        MATCH (user1:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag:Tag),
              (user2:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag)
        WHERE user1.username = {username} AND user1 <> user2
        WITH user2, COLLECT(DISTINCT tag.name) AS tags, COUNT(DISTINCT tag.name) AS tag_count
        ORDER BY tag_count DESC LIMIT {n}
        RETURN user2.username AS similar_user, tags
        """

        return graph.run(query,username=self.username, n=n).data()

    # returns n users that have liked posts with the same tags
    def commonality_of_user(self, user):
        query1 = """
        MATCH (user1:User)-[:PUBLISHED]->(post:Post)<-[:LIKES]-(user2:User)
        WHERE user1.username = {username1} AND user2.username = {username2}
        RETURN COUNT(post) AS likes
        """

        likes = graph.run(query1, username1=self.username, username2=user.username).evaluate()
        likes = 0 if not likes else likes

        query2 = """
        MATCH (user1:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag:Tag),
              (user2:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag)
        WHERE user1.username = {username1} AND user2.username = {username2}
        WITH COLLECT(DISTINCT tag.name) AS tags
        RETURN tags
        """

        tags = graph.run(query2, username1=self.username, username2=user.username).evaluate()

        return {"likes": likes, "tags": tags}


def today_recent_posts(n):
    today = int(datetime.now().strftime("%Y%m%d"))

    query = """
    MATCH (user:User)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag) 
    WHERE post.date ={today}
    RETURN user.username as username, post, COLLECT(tag.name) AS tags
    ORDER BY post.timestamp DESC LIMIT {n}
    """

    return graph.run(query,today=today, n=n).data()