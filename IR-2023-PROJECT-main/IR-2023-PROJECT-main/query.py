"""This module accepts a search query and optionally a user id
and returns the best matching result from the Elasticsearch Books index"""
from sys import argv
from elasticsearch import Elasticsearch
import pandas as pd


# Coefficients values for the weighted average.
RATING_COEFF = 0.5
RANK_COEFF = 0.5


def get_args():
    """Gets the values of the arguments given in the command line."""
    # Case: Query and User ID
    if len(argv) == 3:
        return argv[1], int(argv[2])
    return argv[1], None


def es_connect():
    """Connects to the cluster and notifies user."""

    client = Elasticsearch("http://localhost:9200")

    # Print success message.
    if client.ping():
        print("Successfully connected to Elasticsearch cluster.")
        print(
            f"""
             Cluster Name: {client.info().body['cluster_name']}\n
             Cluster UUID: {client.info().body['cluster_uuid']}
            """
        )
    else:
        print("Could not connect to Elasticsearch cluster.")

    return client


def es_search(es_client, user_query):
    """Queries Elastisearch client based on user input."""
    # Create and submit the query
    query_body = {"bool": {"should": {"match": {"book_title": user_query}}}}
    response = es_client.search(index="books", query=query_body, size=1000)
    # Create list of results
    es_results = []
    for hit in response["hits"]["hits"]:
        result = {
            "isbn": hit["_source"]["isbn"],
            "title": hit["_source"]["book_title"],
            "author": hit["_source"]["book_author"],
            "year_of_publication": hit["_source"]["year_of_publication"],
            "rank": float(hit["_score"]),
        }
        es_results.append(result)

    return es_results


def get_ratings(user_id):
    """Get all the ratings of a certain user."""
    # Parse the data file to get ratings
    df = pd.read_csv("BX-Book-Ratings-Final.csv")
    result = df[df["uid"] == user_id][["uid", "isbn", "rating"]]

    user_ratings = {}  # Create dict isbn : user-rating
    for _, row in result.iterrows():
        user_ratings[row["isbn"]] = float(row["rating"])

    return user_ratings


def calibrate_results(elastic_results, user_ratings):
    """Combine user ratings and elastic search response into the final list."""
    # Final result calculated using weighted average.
    for res in elastic_results:
        rating = (
            float(user_ratings[res["isbn"]]) if res["isbn"] in user_ratings else None
        )
        if rating is not None:
            # 0 rated books go to the bottom of the result list.
            if rating == 0:
                res["rank"] = 0
            else:
                res["rank"] = rating * RATING_COEFF + res["rank"] * RANK_COEFF
        else:
            # calculate rank only based on the Elasticsearch result.
            res["rank"] = res["rank"] * RANK_COEFF

    return elastic_results


def get_results(es_client):
    """Query Elasticsearch and return final results."""
    # Get query and user id from the command line.
    user_query, user_id = get_args()
    # Query elastic search.
    elastic_results = es_search(es_client, user_query)

    # Recalibrate elastic search results based on users ratings.
    if user_id is not None:
        user_ratings = get_ratings(user_id)
        elastic_results = calibrate_results(elastic_results, user_ratings)

    return elastic_results


def print_results(final_results):
    """Prints the final result in a readable format"""
    # Sort the results based on rank if user id was provided.
    if len(argv) == 3:
        final_results = sorted(final_results, key=lambda x: x["rank"], reverse=True)

    # Keep 10% of the resutls
    final_results = final_results[: int(len(final_results) / 10) :]

    print(f"\n{len(final_results)} Results: \n")
    for res in final_results:
        print(
            f' Title: {res["title"]}, Author: {res["author"]}, Year: {res["year_of_publication"]}\n Matching rank: {res["rank"]}'
        )
        print("--------------------------------------------------------------------")


if __name__ == "__main__":
    es = es_connect()
    results = get_results(es)
    print_results(results)
