from datetime import datetime
from itertools import combinations
import sys
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import matplotlib.pyplot as plt
import seaborn as sns
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from googleapiclient.errors import HttpError
import os
import shutil
import networkx as nx


def get_video_links(api_key, query, channel_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
                    
    video_links = []
    proceed = True

    try:
        response = youtube.search().list(
        q=query,
        part='snippet',
        type='video',
        channelId=channel_id).execute()
        for item in response['items']:
            video_id = item['id']['videoId']
            video_links.append(video_id)

    except HttpError as e:
        proceed = False
        if (e.status_code == 403 and e.reason == 'The request cannot be completed because you have exceeded your <a href="/youtube/v3/getting-started#quota">quota</a>.'):
            print('Limit Exceeded for this API. Please try with another API key or try again after 24 Hours. ')
        else:
            print(f'Error Occured: {e.error_details}')
    

    return proceed, video_links

def plot_top_keywords(df, num_keywords=5):
    """
    Plots the top keywords with the most videos.

    Parameters:
    df (DataFrame): The cleaned dataframe containing 'Keyword' and 'Video_Count' columns.
    num_keywords (int): The number of top keywords to display.
    """
    keywords_video_count = df.groupby('Keyword')['Video_Count'].sum().sort_values(ascending=False)
    
    plt.figure(figsize=(12, 8))
    sns.barplot(x=keywords_video_count.head(num_keywords).values, y=keywords_video_count.head(num_keywords).index, palette="viridis")
    plt.xlabel('Number of Videos')
    plt.ylabel('Keywords')
    plt.title('Top {} Keywords with the Most Videos'.format(num_keywords))
    plt.show()

def plot_top_countries(df):
    """
    Plots the countries with the most videos.

    Parameters:
    df (DataFrame): The cleaned dataframe containing 'Country' and 'Video_Count' columns.
    """
    countries_video_count = df.groupby('Country')['Video_Count'].sum().sort_values(ascending=False)
    
    plt.figure(figsize=(12, 8))
    sns.barplot(x=countries_video_count.values, y=countries_video_count.index, palette="viridis")
    plt.xlabel('Number of Videos')
    plt.ylabel('Countries')
    plt.title('Countries with the Most Videos')
    plt.show()

def get_country_channel_stats(df, num_keywords=5):
    """
    Returns the stats for each country and channel combination for the top keywords with the most videos.

    Parameters:
    df (DataFrame): The cleaned dataframe containing 'Keyword', 'Country', 'Channel', and 'Video_Count' columns.
    num_keywords (int): The number of top keywords to consider.

    Returns:
    DataFrame: A dataframe with the stats for each country and channel combination for the top keywords.
    """
    keywords_video_count = df.groupby('Keyword')['Video_Count'].sum().sort_values(ascending=False)
    top_5_keywords = keywords_video_count.head(num_keywords).index
    df_top_keywords = df[df['Keyword'].isin(top_5_keywords)]
    country_channel_stats = df_top_keywords.groupby(['Country', 'Party', 'Keyword']).agg({'Video_Count': 'sum'}).reset_index()
    
    print(country_channel_stats)
    return country_channel_stats


def extract_youtube_comments_and_stats(api_key, video_id):
    # Build the YouTube service object
    youtube = build('youtube', 'v3', developerKey=api_key)

    # Get video statistics
    video_response = youtube.videos().list(
        part='statistics,snippet',
        id=video_id
    ).execute()

    video_info = video_response['items'][0]
    video_stats = video_info['statistics']
    video_snippet = video_info['snippet']

    like_count = video_stats.get('likeCount', 0)
    view_count = video_stats.get('viewCount', 0)
    comment_count = video_stats.get('commentCount', 0)
    upload_date = video_snippet['publishedAt']

    # Function to get comments
    def get_comments(youtube, video_id):
        comments = []
        results = youtube.commentThreads().list(
            part='snippet', videoId=video_id, textFormat='plainText', maxResults=100
        ).execute()
        
        while results:
            for item in results['items']:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                comments.append(comment)
            if 'nextPageToken' in results:
                results = youtube.commentThreads().list(
                    part='snippet', videoId=video_id, textFormat='plainText', pageToken=results['nextPageToken'], maxResults=100
                ).execute()
            else:
                break
        return comments

    # Get comments for the given video ID
    try:
        comments = get_comments(youtube, video_id)
    except HttpError as e:
        comments = []
    # Return the gathered information
    return {'like_count':like_count, 'view_count': view_count, 'comment_count': comment_count, 
            'upload_date':upload_date, 'comments':comments}

def analyze_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(text)
    return sentiment



def generate_visualizations(df_comments, df_videos, directory='Results/Reports'):
    """
    Generates various visualizations based on the input dataframes and saves them to the specified directory.
    Prints the name of each file being saved.
    
    Parameters:
    df_comments (pd.DataFrame): DataFrame containing YouTube comments data with sentiment analysis.
    df_videos (pd.DataFrame): DataFrame containing YouTube video data with political and keyword information.
    directory (str): Directory where visualizations will be saved. Default is 'Reports'.
    """
    
    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)

    # Merging df_comments and df_videos on 'VideoID' for analysis
    df_comments_merged = df_comments.merge(df_videos, on='VideoID')

    # Extracting sentiment details from the 'sentiment' column in df_comments
    try:
        sentiment_df = df_comments_merged['sentiment'].apply(eval).apply(pd.Series)
    except TypeError as e:
        print(f'Error: {e}') 
    df_comments_merged = df_comments_merged.join(sentiment_df)

    # 1. Keyword Popularity by Party
    plt.figure(figsize=(12, 8))
    keyword_party_count = df_videos.groupby(['Party', 'Keyword']).size().unstack().fillna(0)
    keyword_party_count.plot(kind='bar', stacked=True)
    plt.title('Keyword Popularity by Party')
    plt.xlabel('Political Party')
    plt.ylabel('Number of Mentions')
    filename = os.path.join(directory, 'keyword_popularity_by_party.png')
    plt.savefig(filename, dpi=300)
    print(f'Saved: {filename}')

    # 2. Keyword Popularity by Country
    plt.figure(figsize=(12, 8))
    keyword_country_count = df_videos.groupby(['Country', 'Keyword']).size().unstack().fillna(0)
    keyword_country_count.plot(kind='bar', stacked=True)
    plt.title('Keyword Popularity by Country')
    plt.xlabel('Country')
    plt.ylabel('Number of Mentions')
    filename = os.path.join(directory, 'keyword_popularity_by_country.png')
    plt.savefig(filename, dpi=300)
    print(f'Saved: {filename}')

    # 3. Video Engagement by Keyword
    plt.figure(figsize=(12, 8))
    sns.boxplot(x='Keyword', y='LikeCount', data=df_comments_merged)
    plt.title('Like Count Distribution by Keyword')
    plt.xticks(rotation=45)
    filename = os.path.join(directory, 'like_count_distribution_by_keyword.png')
    plt.savefig(filename, dpi=300)
    print(f'Saved: {filename}')

    plt.figure(figsize=(12, 8))
    sns.boxplot(x='Keyword', y='ViewCount', data=df_comments_merged)
    plt.title('View Count Distribution by Keyword')
    plt.xticks(rotation=45)
    filename = os.path.join(directory, 'view_count_distribution_by_keyword.png')
    plt.savefig(filename, dpi=300)
    print(f'Saved: {filename}')

    # 4. Sentiment Analysis by Keyword
    plt.figure(figsize=(12, 8))
    sns.boxplot(x='Keyword', y='compound', data=df_comments_merged)
    plt.title('Sentiment Distribution by Keyword')
    plt.xticks(rotation=45)
    filename = os.path.join(directory, 'sentiment_distribution_by_keyword.png')
    plt.savefig(filename, dpi=300)
    print(f'Saved: {filename}')

    # 5. Keyword Mentions Over Time
    df_comments_merged['UploadDate'] = pd.to_datetime(df_comments_merged['UploadDate'])
    df_comments_merged['YearMonth'] = df_comments_merged['UploadDate'].dt.to_period('M')

    plt.figure(figsize=(14, 8))
    keyword_time_series = df_comments_merged.groupby(['YearMonth', 'Keyword']).size().unstack().fillna(0)
    keyword_time_series.plot()
    plt.title('Keyword Mentions Over Time')
    plt.xlabel('Time')
    plt.ylabel('Number of Mentions')
    filename = os.path.join(directory, 'keyword_mentions_over_time.png')
    plt.savefig(filename, dpi=300)
    print(f'Saved: {filename}')

    # 6. Party-Specific Keyword Usage
    plt.figure(figsize=(12, 8))
    keyword_party_country = df_videos.groupby(['Country', 'Party', 'Keyword']).size().unstack().fillna(0)
    sns.heatmap(keyword_party_country, cmap="YlGnBu", annot=True, fmt=".1f", linewidths=.5)
    plt.title('Keyword Usage by Party and Country')
    filename = os.path.join(directory, 'keyword_usage_by_party_and_country.png')
    plt.savefig(filename, dpi=300)
    print(f'Saved: {filename}')

    # 7. Country-Specific Video Engagement
    plt.figure(figsize=(10, 6))
    engagement_country = df_comments_merged.groupby('Country')[['LikeCount', 'ViewCount']].mean()
    engagement_country.plot(kind='bar')
    plt.title('Average Video Engagement by Country')
    plt.xlabel('Country')
    plt.ylabel('Average Counts')
    filename = os.path.join(directory, 'average_video_engagement_by_country.png')
    plt.savefig(filename, dpi=300)
    print(f'Saved: {filename}')

    # 8. Sentiment Analysis by Party
    plt.figure(figsize=(12, 8))
    sns.violinplot(x='Party', y='compound', data=df_comments_merged)
    plt.title('Sentiment Analysis by Party')
    filename = os.path.join(directory, 'sentiment_analysis_by_party.png')
    plt.savefig(filename, dpi=300)
    print(f'Saved: {filename}')

    # 9. Keyword Co-occurrence Network
    keyword_pairs = df_videos.groupby('VideoID')['Keyword'].apply(lambda x: list(combinations(x, 2)))
    keyword_pairs = [pair for sublist in keyword_pairs for pair in sublist]

    G = nx.Graph()
    G.add_edges_from(keyword_pairs)
    pos = nx.spring_layout(G)

    plt.figure(figsize=(12, 12))
    nx.draw(G, pos, with_labels=True, node_color='lightblue', edge_color='gray', node_size=2000, font_size=10)
    plt.title('Keyword Co-occurrence Network')
    filename = os.path.join(directory, 'keyword_cooccurrence_network.png')
    plt.savefig(filename, dpi=300)
    print(f'Saved: {filename}')

    # 10. Cross-Party Keyword Sentiment Comparison
    plt.figure(figsize=(14, 8))
    sns.boxplot(x='Keyword', y='compound', hue='Party', data=df_comments_merged)
    plt.title('Sentiment Comparison by Party for Each Keyword')
    plt.xticks(rotation=45)
    filename = os.path.join(directory, 'sentiment_comparison_by_party_for_each_keyword.png')
    plt.savefig(filename, dpi=300)
    print(f'Saved: {filename}')


if __name__ == "__main__":
    
    api_key_comments = 'AIzaSyDEEcdPAPcvpKM9wPLIRJpe-9r-JrHhEiY'
    columns = ['Country', 'Party', 'Keyword', 'VideoID']
    df_videos = pd.DataFrame(columns=columns)

    df_keywords =  pd.read_excel('countries.xlsx',sheet_name='Keywords')

    df_channels = pd.read_excel('countries.xlsx',sheet_name='Channels')

    res = []

    for index, channel in df_channels.iterrows():
        api_key = channel['API_Key']
        if api_key != 'NNN' and channel['TODO'] == 'Yes':
            for index, query in df_keywords.iterrows():
                proceed, links = get_video_links(api_key=api_key, query=query.iloc[0], channel_id=channel['Channel_ID'])
                if(proceed):
                    result = []
                    for l in links:
                        new_row = {
                        'Country': channel['Country'],
                        'Party': channel['Party'],
                        'Keyword': query.iloc[0],
                        'VideoID': l
                    }    
                        result.append(new_row)
                        print(result)
                    df_videos = pd.concat([df_videos, pd.DataFrame(result)], ignore_index=True)
                    
                else:
                    print(f'Due to an error, the execution is terminated.The output has been saved until and not including ChannelID: {channel['Channel_ID']} and Keyword: {query.iloc[0]}')
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    df_videos.to_excel(f'Results/output_incomplete_{timestamp}.xlsx', index=False)
                    print(f'Videos output extracted to file: Results/output_incomplete_{timestamp}.xlsx')
                    sys.exit()
                    
        

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    df_videos.to_excel(f'Results/output_final_{timestamp}.xlsx', index=False)
    print(f'Videos output extracted to file: output_final_{timestamp}.xlsx')

    #Extracting comments for videos
    comments_data = []
    
    for v in df_videos['VideoID']:
        resp = extract_youtube_comments_and_stats(api_key_comments, v)
        for comment in resp['comments']:
            #print(comment)
            if comment:
                sentiment = analyze_sentiment(comment)
                newrow = {
                            'VideoID': v
                            , 'UploadDate': resp['upload_date']
                            , 'LikeCount': resp['like_count']
                            , 'ViewCount': resp['view_count']
                            ,'Comment': comment
                            , 'sentiment': sentiment
                            }
                print(newrow)
                comments_data.append(newrow)
   
    # Create a DataFrame from the collected data
    df_comments = pd.DataFrame(comments_data)
    df_comments.to_excel(f'Results/comments_output_final_{timestamp}.xlsx', index=False)
    print(f'Comments Output Extracted to file: comments_output_final_{timestamp}.xlsx')

    create_reports_folder('.')

    generate_visualizations(df_comments, df_videos)

    print('Visualisations Saved in Results/Reports/ directory.')


# Calculate the number of videos for each row ----  for this, need to group by keywords. below technique is not accurate
    #df_videos['Video_Count'] = df_videos['VideoID'].apply(len)

    #plot_top_keywords(df_videos)

    #get_country_channel_stats(df_videos)

    #plot_top_countries(df_videos)