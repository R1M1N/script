#!/usr/bin/env python3
"""
Add transcripts to YouTube videos using correct YouTubeTranscriptApi
"""
import os
import json
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi

class YouTubeTranscriptExtractor:
    def __init__(self, output_dir="data_ingest/raw/youtube"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def load_videos_metadata(self):
        """Load videos with metadata"""
        metadata_file = os.path.join(self.output_dir, "youtube_videos_metadata.json")
        
        if not os.path.exists(metadata_file):
            print(f"❌ Metadata file not found: {metadata_file}")
            print("Run youtube_metadata.py first!")
            return []
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_transcript(self, video_id):
        """Get transcript for a single video using correct API"""
        try:
            # Use the YouTubeTranscriptApi.fetch() method as shown
            ytt_api = YouTubeTranscriptApi()
            transcript_result = ytt_api.fetch(video_id)
            
            # Convert to text
            full_transcript = ""
            for snippet in transcript_result:
                full_transcript += snippet.text + " "
            
            return full_transcript.strip(), None
            
        except Exception as e:
            return None, str(e)
    
    def create_transcript_chunks(self, transcript, max_words=300):
        """Split transcript into chunks for embeddings"""
        if not transcript:
            return []
        
        words = transcript.split()
        chunks = []
        
        for i in range(0, len(words), max_words):
            chunk = " ".join(words[i:i + max_words])
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks
    
    def add_transcripts_to_videos(self):
        """Add transcripts to all videos"""
        videos = self.load_videos_metadata()
        if not videos:
            return
        
        print(f"🚀 Getting transcripts for {len(videos)} videos...")
        
        successful_transcripts = 0
        failed_transcripts = []
        
        for i, video in enumerate(videos, 1):
            video_id = video["video_id"]
            title = video.get("title", "Untitled")
            
            print(f"[{i}/{len(videos)}] Getting transcript for: {title[:50]}...")
            
            transcript, error = self.get_transcript(video_id)
            
            if transcript:
                # Add transcript and chunks
                video["transcript"] = transcript
                video["transcript_chunks"] = self.create_transcript_chunks(transcript)
                video["transcript_word_count"] = len(transcript.split())
                video["transcript_chunk_count"] = len(video["transcript_chunks"])
                
                successful_transcripts += 1
                print(f"  ✅ Got transcript ({len(transcript.split())} words)")
            else:
                video["transcript"] = ""
                video["transcript_chunks"] = []
                video["transcript_word_count"] = 0
                video["transcript_chunk_count"] = 0
                video["transcript_error"] = error
                
                failed_transcripts.append({
                    "video_id": video_id,
                    "title": title,
                    "error": error
                })
                print(f"  ❌ No transcript: {error}")
        
        # Save results
        self.save_videos_with_transcripts(videos, failed_transcripts, successful_transcripts)
        return videos
    
    def save_videos_with_transcripts(self, videos, failed_transcripts, successful_count):
        """Save videos with transcripts to files"""
        # Main file with transcripts
        output_file = os.path.join(self.output_dir, "youtube_videos_with_transcripts.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(videos, f, ensure_ascii=False, indent=2)
        
        # Failed transcripts
        if failed_transcripts:
            failed_file = os.path.join(self.output_dir, "failed_transcripts.json")
            with open(failed_file, 'w', encoding='utf-8') as f:
                json.dump(failed_transcripts, f, ensure_ascii=False, indent=2)
        
        # Summary
        total_transcript_words = sum(v.get("transcript_word_count", 0) for v in videos)
        total_chunks = sum(v.get("transcript_chunk_count", 0) for v in videos)
        
        summary = {
            "extraction_completed_at": datetime.now().isoformat(),
            "total_videos": len(videos),
            "successful_transcripts": successful_count,
            "failed_transcripts": len(failed_transcripts),
            "total_transcript_words": total_transcript_words,
            "total_transcript_chunks": total_chunks,
            "average_words_per_video": total_transcript_words // successful_count if successful_count else 0
        }
        
        summary_file = os.path.join(self.output_dir, "transcript_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎉 Transcript extraction completed!")
        print(f"📊 Results:")
        print(f"  • Videos with transcripts: {successful_count}")
        print(f"  • Videos without transcripts: {len(failed_transcripts)}")
        print(f"  • Total transcript words: {total_transcript_words:,}")
        print(f"  • Total transcript chunks: {total_chunks}")
        print(f"📁 Saved to: {output_file}")

def main():
    extractor = YouTubeTranscriptExtractor()
    extractor.add_transcripts_to_videos()

if __name__ == "__main__":
    main()
