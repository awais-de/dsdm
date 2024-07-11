import pandas as pd
from googleapiclient.discovery import build

api_key = 'AIzaSyCDYMgkKyBXWOYCSR9BBcIAkKF0TKaWibg'  # Replace with your actual API key
youtube = build('youtube', 'v3', developerKey=api_key)
max_results = 500


def get_video_links(query, channel_id, max_results=10):
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

if __name__ == "__main__":
    
    columns = ['Country', 'Channel', 'Keyword', 'Video']
    df_videos = pd.DataFrame(columns=columns)

    df_keywords = pd.read_excel('keywords.xlsx')

    df_channels = pd.read_excel('countries.xlsx',sheet_name='channels')

    res = []

    for index, channel in df_channels.iterrows():
        for index, query in df_keywords.iterrows():

            links = get_video_links(query.iloc[0], channel['Channel_ID'], max_results)
            result = []
            new_row = {
                'Country': channel['Country'],
                'Channel': channel['Party'],
                'Keyword': query.iloc[0],
                'Video': links
            }    
            result.append(new_row)
            print(result)
            df_videos = pd.concat([df_videos, pd.DataFrame(result)], ignore_index=True)
        

#    print(df_videos.describe())

df_videos.to_excel('output.xlsx')