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
    for item in response['items']:
        video_id = item['id']['videoId']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        video_links.append(video_url)

    return video_links

if __name__ == "__main__":
    api_key = 'AIzaSyA4CD1mPnWF3kVsUFnEHxAN67qKX8XD08A'  # Replace with your actual API key
    query = 'climate change'  # Replace with your search keywords
    df=pd.read_excel('keywords.xlsx')
    max_results = 100  # Adjust the number of results you want

    links = get_video_links(api_key, df, max_results)
    for link in links:
        print(link)
