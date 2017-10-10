from py2neo import Graph, Node, Relationship, authenticate
from py2neo.ext.calendar import GregorianCalendar
from passlib.hash import bcrypt
from datetime import datetime
import uuid

# authenticates into neo4j db using username and passsword
authenticate("localhost:7474", "neo4j", "sechien")

# initiates graph object
graph = Graph()
calendar = GregorianCalendar(graph)

# creates a user class
class User:

    # creates username when given a username
    def __init__(self, username):
        self.username = username

    # finds a user node using username and searching the node's username property
    def find(self):
        user = graph.find_one("User", "username", self.username)
        return user

    # registers a user node with username and password by creating a node if the username cannot be found
    def register(self, password):
        if not self.find():
            # user = Node("User", username=self.username, password=bcrypt.encrypt(password))
            user = Node("User", username=self.username, password=password)
            graph.create(user)
            return True
        return False

    # authenticates the user using password
    def verify_password(self, password):
        user = self.find()

        if not user:
            return False
            # return bcrypt.verify(password, user["password"])
        return password == user["password"]

    # creates a post with title, tags, and text and relates it to the user
    def add_post(self, title, tags, text):
        user = self.find()

        # established the properties of the post node
        post = Node(
            "POST",
            id=str(uuid.uuid4()),
            title=title,
            text=text,
            timestamp=int(datetime.now().strftime("%H%M%S")),
            date=int(datetime.now().strftime("%Y%m%d")),
            display_date=datetime.now().strftime("%x")
        )

        # creates a relationship to link user to their published posts
        rel = Relationship(user, "PUBLISHED", post)

        # creates a post node and relates the node to the user who published it
        # if a node does not exist when creating a relationship neo4j will create it automatically
        graph.create(rel)

        # creates a list of tags entered by the user using comma as delimiter
        tags = [x.strip() for x in tags.lower().split(",")]

        # iterates through the list and creates a node for each tag
        for tag in tags:
            # establishes the properties of a tag node
            t = Node("Tag", name=tag)

            # the tag nodes are then related to the post node
            rel = Relationship(t, "TAGGED", post)

            # commits the relationship to neo4j
            # if a node does not exist when creating a relationship neo4j will create it automatically
            # if one was established, merge is used here instead of create as neo4j will only create
            # new distinct tags nodes, existing tag nodes will just get an additional TAGGED relationship
            # from it to the post node
            graph.merge(rel)

    # creates a like relationship
    def like_post(self, post_id):
        user = self.find()

        # finds the post node by post id
        post = graph.find_one("POST", "id", post_id)

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
        MATCH (user:User)-[:PUBLISHED]->(post:POST)<-[:TAGGED]-(tag:Tag)
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
        MATCH (user1:User)-[:PUBLISHED]->(:POST)<-[:TAGGED]-(tag:Tag),
              (user2:User)-[:PUBLISHED]->(:POST)<-[:TAGGED]-(tag)
        WHERE user1.username = {username} AND user1 <> user2
        WITH user2, COLLECT(DISTINCT tag.name) AS tags, COUNT(DISTINCT tag.name) AS tag_count
        ORDER BY tag_count DESC LIMIT {n}
        RETURN user2.username AS similar_user, tags
        """

        return graph.run(query,username=self.username, n=n).data()

    # returns n users that have liked posts with the same tags
    def commonality_of_user(self, user):
        query1 = """
        MATCH (user1:User)-[:PUBLISHED]->(post:POST)<-[:LIKES]-(user2:User)
        WHERE user1.username = {username1} AND user2.username = {username2}
        RETURN COUNT(post) AS likes
        """

        likes = graph.run(query1, username1=self.username, username2=user.username).evaluate()
        likes = 0 if not likes else likes

        query2 = """
        MATCH (user1:User)-[:PUBLISHED]->(:POST)<-[:TAGGED]-(tag:Tag),
              (user2:User)-[:PUBLISHED]->(:POST)<-[:TAGGED]-(tag)
        WHERE user1.username = {username1} AND user2.username = {username2}
        WITH COLLECT(DISTINCT tag.name) AS tags
        RETURN tags
        """

        tags = graph.run(query2, username1=self.username, username2=user.username).evaluate()

        return {"likes": likes, "tags": tags}


def today_recent_posts(n):
    today = int(datetime.now().strftime("%Y%m%d"))

    query = """
    MATCH (user:User)-[:PUBLISHED]->(post:POST)<-[:TAGGED]-(tag:Tag) 
    WHERE post.date ={today}
    RETURN user.username as username, post, COLLECT(tag.name) AS tags
    ORDER BY post.timestamp DESC LIMIT {n}
    """

    return graph.run(query,today=today, n=n).data()