"""This module parses BX_Books.csv file and saves
them as documents in a local ElasticSearch cluster."""
from elasticsearch import Elasticsearch
import pandas as pd


def es_connect():
    """Connects to the cluster and notifies user."""

    client = Elasticsearch("http://localhost:9200")
    if client.ping():
        print("Successfully connected to Elasticsearch cluster.")
        print(
            f" Cluster Name: {client.info().body['cluster_name']}\nCluster UUID: {client.info().body['cluster_uuid']}"
        )
    else:
        print("Could not connect to Elasticsearch cluster.")

    return client


def create_index(client, index_name="books"):
    """Initializes specified index in the cluster."""

    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)

    client.indices.create(index=index_name)
    print(f"New index created: -{index_name}")


def add_data(client, index_name="books"):
    """Parses data from BX-Books.csv as Elasticsearch documents
    and adds them to the specified index."""

    df = pd.read_csv("BX-Books.csv")

    for i, r in df.iterrows():

        # Creates document for each row and adds it to index.
        doc = {
            "isbn": r["isbn"],
            "book_title": r["book_title"],
            "book_author": r["book_author"],
            "year_of_publication": r["year_of_publication"],
            "publisher": r["publisher"],
            "summary": r["summary"],
            "category": r["category"],
        }
        client.index(index=index_name, id=i, document=doc)


if __name__ == "__main__":
    es = es_connect()
    create_index(es)
    add_data(es)
