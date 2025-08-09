import ast
import shutil
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os


def create_reports_folder(directory):
    folder_path = os.path.join(directory, 'Reports')
    
    if os.path.exists(folder_path):
        # Delete the folder and all its contents if it already exists
        shutil.rmtree(folder_path)
        print(f"Deleted existing folder: {folder_path}")
    
    # Create the new 'Reports' folder
    os.makedirs(folder_path)
    print(f"Created new folder: {folder_path}")

def get_sentiment_label(compound_score):
    if compound_score >= 0.05:
        return 'Positive'
    elif compound_score > -0.05 and compound_score < 0.05:
        return 'Neutral'
    else:
        return 'Negative'

# Define decades based on years
def get_5year_period(year):
    start_year = (year // 5) * 5
    end_year = start_year + 4
    return f'{start_year} - {end_year}'



def generate_visualizations(df_comments, df_videos, directory='Results/Reports'):
    """
    Generates various visualizations based on the input dataframes and saves them to the specified directory.
    Prints the name of each file being saved.
    
    Parameters:
    df_comments (pd.DataFrame): DataFrame containing YouTube comments data with sentiment analysis.
    df_videos (pd.DataFrame): DataFrame containing YouTube video data with political and keyword information.
    directory (str): Directory where visualizations will be saved. Default is 'Reports'.
    """    

    create_reports_folder('Results/')
    
    # Convert sentiment strings to dictionaries
    df_comments['sentiment'] = df_comments['sentiment'].apply(ast.literal_eval)

    df_comments['sentiment_label'] = df_comments['sentiment'].apply(lambda x: get_sentiment_label(x['compound']))

    df_comments['compound'] = df_comments['sentiment'].apply(lambda x: x['compound'])



    # Convert UploadDate to datetime and extract the year
    df_comments['UploadDate'] = pd.to_datetime(df_comments['UploadDate'])
    df_comments['Year'] = df_comments['UploadDate'].dt.year

    # Merging df_comments and df_videos on 'VideoID' for analysis
    df_merged = df_comments.merge(df_videos, on='VideoID')


    #01. Summary of videos (number of videos, number of views, number of likes) as per each country and party
    df_summary = pd.merge(
        df_videos.groupby(['Country', 'Party']).agg(
            Number_of_Videos = ('VideoID', 'count')
        ).reset_index(),
        df_merged.groupby(['Country', 'Party']).agg(
    Number_of_Views=('ViewCount', 'sum'),
    Number_of_Likes=('LikeCount', 'sum')
    ).reset_index()
    )
    # Rename the columns for clarity
    df_summary.columns = ['Country', 'Party', 'Number of Videos', 'Total Views', 'Total Likes']

    df_summary.sort_values(by=['Country', 'Number of Videos', 'Total Views'], ascending=[True, False, False]).to_excel(f'{directory}/01_Videos_Summary_By_Country_Party.xlsx', index=False)
    print(f'File saved at: {directory}/01_Videos_Summary_By_Country_Party.xlsx')




    #02. Summary of sentiments (Positives, Neutrals, Negatives) as per each country and party
    df_comments_summary = df_merged.groupby(['Country', 'Party', 'sentiment_label']).size().unstack(fill_value=0).reset_index()
    df_comments_summary.columns = ['Country', 'Party', 'Number of Negative Sentiments', 'Number of Neutral Sentiments', 'Number of Positive Sentiments']

    df_comments_summary.to_excel(f'{directory}/02_Comments_Sentiment_Summary_By_Country_Party.xlsx', index=False)
    print(f'File saved at: {directory}/02_Comments_Sentiment_Summary_By_Country_Party.xlsx')




    #03. Video popularity (number of views) over time as per each country

    # Group by Country and Year, then sum the ViewCounts
    df_grouped_time_series_analysis = df_merged.groupby(['Country', 'Year']).agg({'ViewCount': 'sum'}).reset_index()

    # Pivot the data to have years on the X-axis and countries as columns
    df_pivot_time_series_analysis = df_grouped_time_series_analysis.pivot(index='Year', columns='Country', values='ViewCount').fillna(0)

    

    df_pivot_time_series_analysis.index = df_pivot_time_series_analysis.index.to_series().apply(get_5year_period)

    df_pivot_time_series_analysis = df_pivot_time_series_analysis.groupby(df_pivot_time_series_analysis.index).sum()

    # Plot the data with a logarithmic scale on the y-axis
    plt.figure(figsize=(10, 10))
    for country in df_pivot_time_series_analysis.columns:
        plt.plot(df_pivot_time_series_analysis.index, df_pivot_time_series_analysis[country], marker='o', label=country)

    plt.yscale('log')  # Apply logarithmic scale to the y-axis
    plt.title('Video Popularity Over Time (Logarithmic Scale)')
    plt.xlabel('5-Year Period')
    plt.ylabel('Number of Views (Log Scale)')
    plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
    plt.legend(title='Country')
    plt.grid(True)
    filename = os.path.join(directory, '03_video_popularity_time_series_analysis_by_country.png')
    plt.savefig(filename, dpi = 300)
    print(f'Saved: {filename}')

    # 04. Keyword Mentions Over Time ---------------WIP--------------
    df_merged['UploadDate'] = pd.to_datetime(df_merged['UploadDate'])
    df_merged['YearMonth'] = df_merged['UploadDate'].dt.to_period('M')

    plt.figure(figsize=(20, 20))
    keyword_time_series = df_merged.groupby(['YearMonth', 'Keyword']).size().unstack().fillna(0)
    keyword_time_series.plot()
    plt.title('Keyword Mentions Over Time')
    plt.xlabel('Time')
    plt.ylabel('Number of Mentions')
    filename = os.path.join(directory, '04_keyword_mentions_over_time.png')
    plt.savefig(filename, dpi=300)
    print(f'Saved: {filename}')

    # 05. Party-Specific Keyword Usage ---------------WIP--------------
    plt.figure(figsize=(15, 21))
    keyword_party_country = df_videos.groupby(['Country', 'Party', 'Keyword']).size().unstack().fillna(0)
    sns.heatmap(keyword_party_country, cmap="YlGnBu", annot=True, fmt=".1f", linewidths=.5)
    plt.title('Keyword Usage by Party and Country')
    filename = os.path.join(directory, '05_keyword_usage_by_party_and_country.png')
    plt.savefig(filename, dpi=300)
    print(f'Saved: {filename}')

    # 06. Video Engagement by Keyword ---------------WIP--------------
    plt.figure(figsize=(12, 15))
    sns.boxplot(x='Keyword', y='LikeCount', data=df_merged)
    plt.title('Like Count Distribution by Keyword')
    plt.xticks(rotation=45)
    filename = os.path.join(directory, '06_01_like_count_distribution_by_keyword.png')
    plt.savefig(filename, dpi=300)
    print(f'Saved: {filename}')

    plt.figure(figsize=(12, 15))
    sns.boxplot(x='Keyword', y='ViewCount', data=df_merged)
    plt.title('View Count Distribution by Keyword')
    plt.xticks(rotation=45)
    filename = os.path.join(directory, '06_02_view_count_distribution_by_keyword.png')
    plt.savefig(filename, dpi=300)
    print(f'Saved: {filename}')

    # 07. Sentiment Analysis by Keyword ---------------WIP--------------
    plt.figure(figsize=(14, 15))
    sns.boxplot(x='Keyword', y='compound', data=df_merged)
    plt.title('Sentiment Distribution by Keyword')
    plt.xticks(rotation=45)
    filename = os.path.join(directory, '07_sentiment_distribution_by_keyword.png')
    plt.savefig(filename, dpi=300)
    print(f'Saved: {filename}')

    # 08. Cross-Party Keyword Sentiment Comparison ---------------WIP--------------
    plt.figure(figsize=(14, 17))
    sns.boxplot(x='Keyword', y='compound', hue='Party', data=df_merged)
    plt.title('Sentiment Comparison by Party for Each Keyword')
    plt.xticks(rotation=45)
    filename = os.path.join(directory, '08_sentiment_comparison_by_party_for_each_keyword.png')
    plt.savefig(filename, dpi=300)
    print(f'Saved: {filename}')


if __name__ == "__main__":
    
    datafilename = 'data_files.xlsx'
    df_file_names = pd.read_excel(datafilename)

    file_names_list = df_file_names.iloc[:, 0].tolist()

    df_comments = pd.read_excel(file_names_list[0])
    df_videos = pd.read_excel(file_names_list[1])


    create_reports_folder('.')

    generate_visualizations(df_comments, df_videos)

    print('Visualisations Saved in Results/Reports/ directory.')
