import ast
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


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
    
    api_key = 'AIzaSyDEEcdPAPcvpKM9wPLIRJpe-9r-JrHhEiY'  

    df_videos = pd.read_excel('output_exploded_final.xlsx')

    comments_data = []
    
    for v in df_videos['VideoID']:
        resp = extract_youtube_comments_and_stats(api_key, v)
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
    comments_df = pd.DataFrame(comments_data)

    # Save the DataFrame to an Excel file
    comments_df.to_excel('comments_output_final1.xlsx', index=False)

    print("Comments extracted and saved to 'comments_output.xlsx'")