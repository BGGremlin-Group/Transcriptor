#!/data/data/com.termux/files/usr/bin/env python
from youtube_transcript_api import YouTubeTranscriptApi
import re
import os

def extract_video_id(url):
    """Extract the YouTube video ID from a URL."""
    pattern = r'(?:v=|youtu\.be/|youtube\.com/(?:embed/|watch\?v=))([^\s&?]{11})'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid YouTube URL or video ID not found.")

def get_transcript(video_id, output_file=None):
    """Fetch and display the transcript, optionally saving it to a file."""
    try:
        # Fetch the transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = ""

        # Combine transcript segments
        for entry in transcript:
            text = entry['text']
            start = entry['start']
            duration = entry['duration']
            transcript_text += f"[{start:.2f}s] {text}\n"

        # Print the transcript
        print("\nTranscript:\n")
        print(transcript_text)

        # Save to file if output_file is specified
        if output_file:
            storage_path = os.path.expanduser("~/storage/shared/Transcripts")
            os.makedirs(storage_path, exist_ok=True)
            file_path = os.path.join(storage_path, output_file)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(transcript_text)
            print(f"\nTranscript saved to: {file_path}")

    except Exception as e:
        print(f"Error: {str(e)}")
        print("Possible reasons: No transcript available, video is private, or invalid video ID.")

def main():
    # Get YouTube URL from user
    url = input("Enter YouTube video URL: ")
    try:
        video_id = extract_video_id(url)
        # Ask if user wants to save the transcript
        save = input("Save transcript to a file? (y/n): ").strip().lower()
        output_file = None
        if save == 'y':
            output_file = input("Enter output filename (e.g., transcript.txt): ").strip()
        get_transcript(video_id, output_file)
    except ValueError as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
