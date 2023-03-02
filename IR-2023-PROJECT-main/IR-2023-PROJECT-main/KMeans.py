import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set()
from sklearn.cluster import KMeans

CLUSTERS = 6


def elbow(data):
    """
    Using the Elbow Method to Identify
    optimal number of clusters.
    """
    wcss = []
    for i in range(1, 25):
        kmeans = KMeans(i)
        kmeans.fit(data)
        wcss_iter = kmeans.inertia_
        wcss.append(wcss_iter)

    number_of_clusters = range(1, 25)
    plt.plot(number_of_clusters, wcss)
    plt.title("The Elbow Method")
    plt.xlabel("Number of Clusters")
    plt.ylabel("Within Cluster Sum-of-Squares")
    plt.show()


def loadData(filename):
    """
    Load the data from csv
    and return dataframe for clustering
    """
    df = pd.read_csv(filename)
    x = []
    y = []
    for _, row in df.iterrows():
        x.append(float(row["age"]))
        y.append(float(row["country_encoding"]))

    newdf = pd.DataFrame(list(zip(x, y)), columns=["AGE", "COUNTRY"])

    return newdf


def showClusters(data_with_clusters):
    # Plot Results
    plt.scatter(
        data_with_clusters["AGE"],
        data_with_clusters["COUNTRY"],
        c=data_with_clusters["cluster"],
        cmap="rainbow",
    )
    plt.xlabel("USER AGE")
    plt.ylabel("USER COUNTRY")
    plt.show()


def clustering(filename):
    """Perform Clustering"""
    df = loadData(filename)

    kmeans = KMeans(CLUSTERS, n_init=10)
    id_clusters = kmeans.fit_predict(df)
    data_with_clusters = df.copy()
    data_with_clusters["cluster"] = id_clusters

    showClusters(data_with_clusters)


if __name__ == "__main__":

    # Load clustered users
    df_users = pd.read_csv("BX-Users-Clustered.csv")
    # Load user ratings
    df_ratings = pd.read_csv("BX-Book-Ratings-clean.csv")

    # A list holding each dictionary of book average rating per cluster => [{}, {}, ... ,{}]
    cluster_ratings = []
    for i in range(0, CLUSTERS):

        # { isbn : {accumlative_rating : 0, users_rated : 0} } => {isbn: avg_rating}
        books_cluster = {}
        # Get users dataframe of a specific cluster
        cluster_users = df_users[df_users["cluster"] == i]

        for j, row in cluster_users.iterrows():

            # User id
            user_id = row["uid"]
            # Consider 0 ratings as missing. Examine only valid ratings
            user_ratings = df_ratings[
                (df_ratings["uid"] == user_id) & (df_ratings["rating"] > 0)
            ]

            # Update book dictionary for cluster per user's ratings
            if not user_ratings.empty:
                
                print(f"Cluster {i},record {j}")
                
                for k, row in user_ratings.iterrows():

                    book_isbn = str(row["isbn"])
                    book_rating = float(row["rating"])

                    if book_isbn not in books_cluster.keys():
                        books_cluster[book_isbn] = {
                            "acc_rating": book_rating,
                            "users_rated": 1,
                        }
                    else:
                        books_cluster[book_isbn]["acc_rating"] += book_rating
                        books_cluster[book_isbn]["users_rated"] += 1
                        
        # Create new dictionary containg the average rating for this cluster
        books_cluster_average = {}
        for isbn,values in books_cluster.items():
            total_sum = float(values['acc_rating'])
            no_ratings = float(values['users_rated'])
            
            books_cluster_average[isbn] = int(total_sum/ no_ratings)
            
        cluster_ratings.append(books_cluster_average)



    # Create cluster Specific csv files
    df_books = pd.read_csv('BX-Books-clean.csv')
    for i, d in enumerate(cluster_ratings):
        print("Cluster: ", i)
        isbn_list = []
        summary_list = []
        rating_list = []
        for key, value in d.items():
            book_isbn = key
            book_summary = df_books[df_books["isbn"] == key]['summary'].iloc[0]
            book_rating = int(value)
            
            isbn_list.append(book_isbn)
            summary_list.append(book_summary)
            rating_list.append(book_rating)
            
        clusterdf = pd.DataFrame({"isbn" : isbn_list, "summary": summary_list, "rating" : rating_list})
        
        clusterdf.to_csv(f'cluster{i+1}.csv', index= False) 
    
    
    # Update new user ratings from the cluster's average
    for i,row in df_ratings.iterrows():
        current_uid = row["uid"]
        current_rating = row["rating"]
        current_isbn = row["isbn"]
        user_cluster = int(df_users[df_users["uid"] == current_uid].head(1)['cluster'])
        print(f"User ID: {current_uid} , Cluster: {user_cluster}")
        if current_rating == 0:
            # Access book ratings of the user's cluster
            if current_isbn in cluster_ratings[user_cluster].keys():
                df_ratings.at[i, 'rating'] = int(cluster_ratings[user_cluster][current_isbn])
    
    df_ratings.to_csv('BX-Book-Ratings-Clustered.csv', index=False)
            
        
        

    
