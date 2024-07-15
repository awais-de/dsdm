import pandas as pd
from googleapiclient.discovery import build
import matplotlib.pyplot as plt
import seaborn as sns


def get_video_links(api_key, query, channel_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
                    
    video_links = []

    response = youtube.search().list(
        q=query,
        part='snippet',
        type='video',
        #maxResults=max_results,
        channelId=channel_id
    ).execute()

    for item in response['items']:
        video_id = item['id']['videoId']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        video_links.append(video_url)

    return video_links

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


if __name__ == "__main__":
    
    columns = ['Country', 'Party', 'Keyword', 'Video']
    df_videos = pd.DataFrame(columns=columns)

    df_keywords =  pd.read_excel('countries.xlsx',sheet_name='Keywords')

    df_channels = pd.read_excel('countries.xlsx',sheet_name='Channels')

    res = []

    for index, channel in df_channels.iterrows():
        api_key = channel['API_Key']
        if api_key != 'NNN' and channel['TODO'] == 'Yes':
            for index, query in df_keywords.iterrows():
                links = get_video_links(api_key=api_key, query=query.iloc[0], channel_id=channel['Channel_ID'])
                result = []
                new_row = {
                    'Country': channel['Country'],
                    'Party': channel['Party'],
                    'Keyword': query.iloc[0],
                    'Video': links
                }    
                result.append(new_row)
                print(result)
                df_videos = pd.concat([df_videos, pd.DataFrame(result)], ignore_index=True)
        
# Calculate the number of videos for each row
    df_videos['Video_Count'] = df_videos['Video'].apply(len)

    plot_top_keywords(df_videos)

    get_country_channel_stats(df_videos)

    plot_top_countries(df_videos)