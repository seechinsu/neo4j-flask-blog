from py2neo import Graph, Node, Relationship, authenticate
from py2neo.ext.calendar import GregorianCalendar
from py2neo.ogm import GraphObject, Property, RelatedFrom, RelatedTo, RelatedObjects
from passlib.hash import bcrypt

# authenticates into neo4j db using username and passsword
authenticate("localhost:7474", "neo4j", "sechien")

# initiates graph object
graph = Graph()
calendar = GregorianCalendar(graph)