from datetime import datetime
import sys
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from googleapiclient.errors import HttpError
import os

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

if __name__ == "__main__":
    
    api_key_comments = 'AIzaSyDEEcdPAPcvpKM9wPLIRJpe-9r-JrHhEiY'
    columns = ['Country', 'Party', 'Keyword', 'VideoID']
    df_videos = pd.DataFrame(columns=columns)

    df_keywords =  pd.read_excel('countries.xlsx',sheet_name='Keywords')

    df_channels = pd.read_excel('countries.xlsx',sheet_name='Channels')

    res = []

    folder_data = 'Data'
    if not os.path.exists(folder_data):
        # Create the folder if it doesn't exist
        os.makedirs(folder_data)
        print(f"Folder '{folder_data}' created.")

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
                    df_videos.to_excel(f'{folder_data}/output_incomplete_{timestamp}.xlsx', index=False)
                    print(f'Videos output extracted to file: {folder_data}/output_incomplete_{timestamp}.xlsx')
                    sys.exit()
                    
        

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_file_name = f'{folder_data}/output_final_{timestamp}.xlsx'
    df_videos.to_excel(output_file_name, index=False)
    print(f'Videos output extracted to file: {output_file_name}')

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
    comments_file_name = f'{folder_data}/comments_output_final_{timestamp}.xlsx'
    df_comments.to_excel(comments_file_name, index=False)
    print(f'Comments Output Extracted to file: {comments_file_name}')

    df_file_names = pd.DataFrame({output_file_name, comments_file_name})
    datafilename = 'data_files.xlsx'
    if os.path.exists(datafilename):
        os.remove(datafilename)
    df_file_names.to_excel(datafilename, index=False)


