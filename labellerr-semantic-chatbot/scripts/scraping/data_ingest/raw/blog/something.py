from youtube_transcript_api import YouTubeTranscriptApi

video_id = 'L9RNTGcFbUg'
ytt_api = YouTubeTranscriptApi()
transcript_result = ytt_api.fetch(video_id)

# Convert to text
full_transcript = ""
for snippet in transcript_result:
    full_transcript += snippet.text + " "
print(full_transcript)