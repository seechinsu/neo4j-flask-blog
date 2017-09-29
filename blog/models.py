from py2neo import Graph, Node, Relationship, authenticate
from passlib.hash import bcrypt
from datetime import datetime
import uuid

authenticate("localhost:7474", "neo4j", "sechien")
graph = Graph()

class User:

    def __init__(self, username):
        self.username = username

    def find(self):
        user = graph.find_one("User", "username", self.username)
        return user

    def register(self, password):
        if not self.find():
            # user = Node("User", username=self.username, password=bcrypt.encrypt(password))
            user = Node("User", username=self.username, password=password)
            graph.create(user)
            return True
        return False

    def verify_password(self, password):
        user = self.find()

        if not user:
            return False
            # return bcrypt.verify(password, user["password"])
        return password == user["password"]

    def add_post(self, title, tags, text):
        user = self.find()

        post = Node(
            "POST",
            id=str(uuid.uuid4()),
            title=title,
            text=text,
            timestamp=int(datetime.now().strftime("%H%M%S")),
            date=datetime.now().strftime("%x")
        )

        rel = Relationship(user, "PUBLISHED", post)

        graph.create(rel)

        tags = [x.strip() for x in tags.lower().split(",")]

        for tag in tags:
            t = Node("Tag", name=tag)
            rel = Relationship(t, "TAGGED", post)
            graph.merge(rel)

    def like_post(self, post_id):
        user = self.find()
        post = graph.find_one("POST", "id", post_id)
        rel = Relationship(user, "LIKES", post)
        graph.merge(rel)

    def recent_posts(self,n):
        query = """
        MATCH (user:User)-[:PUBLISHED]->(post:POST)<-[:TAGGED]-(tag:Tag)
        WHERE user.username = {username}
        RETURN post, COLLECT(tag.name) AS tags
        ORDER BY post.timestamp DESC LIMIT {n}
        """

        return graph.run(query,username=self.username,n=n).data()


def today_recent_posts(n):
    today = datetime.now().strftime("%x")

    query = """
    MATCH (user:User)-[:PUBLISHED]->(post:POST)<-[:TAGGED]-(tag:Tag) 
    WHERE post.date ={today}
    RETURN user.username as username, post, COLLECT(tag.name) AS tags
    ORDER BY post.timestamp DESC LIMIT {n}
    """

    return graph.run(query,today=today, n=n).data()