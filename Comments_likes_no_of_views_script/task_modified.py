import pandas as pd
from googleapiclient.discovery import build

def get_video_links(api_key, query, max_results=10):
    youtube = build('youtube', 'v3', developerKey=api_key)

    request = youtube.search().list(
        q=query,
        part='snippet',
        type='video',
        maxResults=max_results
    )
    
    response = request.execute()

    video_links = []
    video_details = []
    for item in response['items']:
        video_id = item['id']['videoId']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        video_links.append(video_url)
        
        video_details.append({
            'video_id': video_id,
            'title': item['snippet']['title'],
            'description': item['snippet']['description'],
            'channel_title': item['snippet']['channelTitle'],
            'publish_time': item['snippet']['publishTime']
        })

    return video_links, video_details

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
    comments = get_comments(youtube, video_id)

    # Return the gathered information
    return like_count, view_count, comment_count, upload_date, comments

def save_to_excel(video_details, api_key, file_name):
    all_data = []
    for video in video_details:
        video_id = video['video_id']
        like_count, view_count, comment_count, upload_date, comments = extract_youtube_comments_and_stats(api_key, video_id)
        for comment in comments:
            all_data.append({
                'Video ID': video_id,
                'Title': video['title'],
                'Description': video['description'],
                'Channel Title': video['channel_title'],
                'Publish Time': video['publish_time'],
                'Like Count': like_count,
                'View Count': view_count,
                'Comment Count': comment_count,
                'Upload Date': upload_date,
                'Comment': comment
            })

    df = pd.DataFrame(all_data)
    df.to_excel(file_name, index=False)

if __name__ == "__main__":
    api_key = 'AIzaSyA4CD1mPnWF3kVsUFnEHxAN67qKX8XD08A'  # Replace with your actual API key
    query = 'climate change'  # Replace with your search keywords
    max_results = 10  # Adjust the number of results you want

    video_links, video_details = get_video_links(api_key, query, max_results)
    save_to_excel(video_details, api_key, 'youtube_video_details.xlsx')
    print("Video details and comments have been saved to youtube_video_details.xlsx")
