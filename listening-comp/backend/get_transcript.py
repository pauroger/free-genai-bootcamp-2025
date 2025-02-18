import os
from youtube_transcript_api import YouTubeTranscriptApi
from typing import Optional, List, Dict

class YouTubeTranscriptDownloader:
    def __init__(self, languages: List[str] = ["de", "en"]):
        self.languages = languages

    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL
        
        Args:
            url (str): YouTube URL
            
        Returns:
            Optional[str]: Video ID if found, None otherwise
        """
        if "v=" in url:
            return url.split("v=")[1][:11]
        elif "youtu.be/" in url:
            return url.split("youtu.be/")[1][:11]
        return None

    def get_transcript(self, video_id: str) -> Optional[List[Dict]]:
        """
        Download YouTube Transcript
        
        Args:
            video_id (str): YouTube video ID or URL
            
        Returns:
            Optional[List[Dict]]: Transcript if successful, None otherwise
        """
        # Extract video ID if full URL is provided
        if "youtube.com" in video_id or "youtu.be" in video_id:
            video_id = self.extract_video_id(video_id)
        if not video_id:
            print("Invalid video ID or URL")
            return None

        print(f"Downloading transcript for video ID: {video_id}")
        try:
            return YouTubeTranscriptApi.get_transcript(video_id, languages=self.languages)
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return None

    def save_transcript(self, transcript: List[Dict], filename: str) -> bool:
        """
        Save transcript to file
        
        Args:
            transcript (List[Dict]): Transcript data
            filename (str): Output filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for entry in transcript:
                    f.write(f"{entry['text']}\n")
            return True
        except Exception as e:
            print(f"Error saving transcript: {str(e)}")
            return False

def main(video_url, print_transcript=False):
    downloader = YouTubeTranscriptDownloader()
    transcript = downloader.get_transcript(video_url)

    if transcript:
        video_id = downloader.extract_video_id(video_url)
        filename = f"./data/transcripts/{video_id}.txt"
        if downloader.save_transcript(transcript, filename):
            print(f"Transcript saved successfully to {filename}")
            if print_transcript:
                for entry in transcript:
                    print(entry['text'])
        else:
            print("Failed to save transcript")
    else:
        print("Failed to get transcript")

if __name__ == "__main__":
    video_url = "https://www.youtube.com/watch?v=J6B82SjPFYY&list=PLxNPzeuPCA7BWJ8Uy5XaSkCdkhei21FhO"
    main(video_url, print_transcript=True)
