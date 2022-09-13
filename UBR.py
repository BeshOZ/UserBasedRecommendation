## User Based Recommendation

#############################################
#imports and settings
#############################################

import pandas as pd
pd.pandas.set_option('display.max_columns', None)
pd.pandas.set_option('display.width', 100)

#############################################
# Data reading and preparing
#############################################

movie = pd.read_csv("movie.csv")
rating = pd.read_csv("rating.csv")

# Add movie titles and info to the rating table
df = rating.merge(movie,how="left",on="movieId")

# remove movies with less than 1000 ratings by getting how many times they were writen in the data, and then filter them
ratingCounts = pd.DataFrame(df["title"].value_counts())
moviesToRemove = ratingCounts[ratingCounts["title"] <= 1000].index
movies = df[~df["title"].isin(moviesToRemove)]

# Create a pivot table with users IDs as index and movies as columns names
user_movie_df = movies.pivot_table(index="userId",columns="title",values="rating")
user_movie_df.head()


# Make it all as a function
def user_movie_creator():
    movie = pd.read_csv("hws/hybrid/movie_lens_dataset/movie.csv")
    rating = pd.read_csv("hws/hybrid/movie_lens_dataset/rating.csv")

    df = rating.merge(movie, how="left", on="movieId")
    ratingCounts = pd.DataFrame(df["title"].value_counts())
    moviesToRemove = ratingCounts[ratingCounts["title"] <= 1000].index
    movies = df[~df["title"].isin(moviesToRemove)]
    user_movie_df = movies.pivot_table(index="userId", columns="title", values="rating")
    return user_movie_df

# Pick a random user to recommend films to
random_user =int(pd.Series(user_movie_df.index).sample(1).values)

# Make a dataframe for our random user:
random_user_df = user_movie_df[user_movie_df.index == random_user]
random_user_df.head()
movies_watched = random_user_df.columns[random_user_df.notna().any()].tolist()
len(movies_watched)

#Take the movies that our random user already watched along with the other users
movies_watched_df = user_movie_df[movies_watched]

# Get how many movies were watched by the other users
user_movie_count = movies_watched_df.T.notnull().sum()
user_movie_count = user_movie_count.reset_index()
user_movie_count.columns = ["userId", "movie_count"]
user_movie_count.head()

# Get user IDs of users who watched at least 60% of the movies our random user had watched
users_same_movies = user_movie_count[user_movie_count["movie_count"] > len(movies_watched)*60/100]["userId"]


# Get only the users we specified and make a new dataframe
final_df = movies_watched_df[movies_watched_df.index.isin(users_same_movies)]

# Now movies_watched_df contains only our top 60% users with all the movies our random user had watched
corr_df = final_df.T.corr().unstack().sort_values()
corr_df = pd.DataFrame(corr_df, columns=["corr"])
corr_df.index.names = ['user_id_1', 'user_id_2']
corr_df = corr_df.reset_index()

# Get a list of our top users who had at least 0.65 correlation with our random user
top_users = corr_df[(corr_df["user_id_1"] == random_user) & (corr_df["corr"] >= 0.65)]
top_users = top_users[["user_id_2","corr"]]
top_users.reset_index(drop=True,inplace=True)
top_users.rename(columns={"user_id_2": "userId"}, inplace=True)


# Merge it with our ratings dataframe and remove our user
top_users_ratings = top_users.merge(rating[["userId", "movieId", "rating"]], how='inner')
top_users_ratings = top_users_ratings[top_users_ratings["userId"] != random_user]


# Make a new feature called weighted rating:
top_users_ratings["weighted_rating"] = top_users_ratings["corr"]*top_users_ratings["rating"]

#Make a new dataframe that consists of the average value of each movie's ratings and get only the movies that got more than 3.5 weighted rating

recommendation_df = top_users_ratings.groupby("movieId")["weighted_rating"].mean()
recommendation_df =recommendation_df.reset_index()

moviesToRecommend = recommendation_df[recommendation_df["weighted_rating"] > 3.5].sort_values("weighted_rating" , ascending=False)
moviesToRecommend = moviesToRecommend.merge(movie[["movieId", "title"]])
moviesToRecommend.head()

#    movieId  weighted_rating                                              title
# 0    52435         3.718011             How the Grinch Stole Christmas! (1966)
# 1    53138         3.718011  Librarian: Return to King Solomon's Mines, The...
# 2    87446         3.718011             Mickey's Twice Upon a Christmas (2004)
# 3    86332         3.718011                                        Thor (2011)
# 4    86298         3.718011                                         Rio (2011)



#Item Based Recommendations

user = 108170
# pick the latest movie that a user rated 5
movie_id = rating[(rating["userId"] == user) & (rating["rating"] == 5.0)].sort_values(by="timestamp", ascending=False)["movieId"][0:1].values[0]

# Get only the movie we picked along with the other users ratings
movie_df = user_movie_df[movie[movie["movieId"] == movie_id]["title"].values[0]]

#Find movies with high correlation with the filtered movie
corr = user_movie_df.corrwith(movie_df)

# sort te correlation values
moveisToRecommend = corr.sort_values(ascending=False)[1:6]

# Get the first 5 movies to recommend
moveisToRecommend
