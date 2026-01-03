from neo4j import GraphDatabase

# URI examples: "neo4j://localhost", "neo4j+s://xxx.databases.neo4j.io"
URI = "neo4j+s://4615b712.databases.neo4j.io"
AUTH = ("neo4j", "foBqieR1IzXERX7e71YohZ14yoOMkkwVwtjG6utfe4w")

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()

 # Create an example graph: 
 # Run a Cypher query with the method Driver.execute_query(). Do not hardcode or concatenate parameters: use placeholders and specify the parameters as keyword arguments.

summary = driver.execute_query("""
    CREATE (a:Person {name: $name})
    CREATE (b:Person {name: $friendName})
    CREATE (a)-[:KNOWS]->(b)
    """,
    name="Alice", friendName="David",
    database_="neo4j",
).summary
print("Created {nodes_created} nodes in {time} ms.".format(
    nodes_created=summary.counters.nodes_created,
    time=summary.result_available_after
))

#Query a graphTo retrieve information from the database, use the Cypher clause MATCH:

records, summary, keys = driver.execute_query("""
    MATCH (p:Person)-[:KNOWS]->(:Person)
    RETURN p.name AS name
    """,
    database_="neo4j",
)

# Loop through results and do something with them
for record in records:
    print(record.data())  # obtain record as dict

# Summary information
print("The query `{query}` returned {records_count} records in {time} ms.".format(
    query=summary.query, records_count=len(records),
    time=summary.result_available_after
))

#Close connections and sessions: 
# Unless you created them using the with statement, call the .close() method on all Driver and Session instances to release any resources still held by them.

from neo4j import GraphDatabase


driver = GraphDatabase.driver(URI, auth=AUTH)
session = driver.session(database="neo4j")

# session/driver usage

session.close()
driver.close()