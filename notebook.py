import pandas as pd
from googleapiclient.discovery import build



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
        

#    print(df_videos.describe())

df_videos.to_excel('output3.xlsx')