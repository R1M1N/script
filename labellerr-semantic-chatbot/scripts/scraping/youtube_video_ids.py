#!/usr/bin/env python3
"""
Extract all video IDs from Labellerr's YouTube channel
"""
import os
import json
import subprocess
from datetime import datetime

class YouTubeVideoIDExtractor:
    def __init__(self, output_dir="data_ingest/raw"):
        self.output_dir = output_dir
        self.youtube_dir = os.path.join(output_dir, "youtube")
        os.makedirs(self.youtube_dir, exist_ok=True)
    
    def get_channel_video_ids(self, channel_url="https://www.youtube.com/@Labellerr"):
        """Get all video IDs from Labellerr's YouTube channel"""
        print(f"🔍 Extracting video IDs from: {channel_url}")
        
        # Use yt-dlp to get just the video IDs (flat playlist)
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--dump-json",
            "--no-warnings",
            channel_url + "/videos"  # Get all videos from channel
        ]
        
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                raise RuntimeError(f"yt-dlp error: {proc.stderr}")
            
            # Parse the JSON output (one JSON object per line)
            video_ids = []
            for line in proc.stdout.strip().split('\n'):
                if line:
                    try:
                        video_info = json.loads(line)
                        if video_info.get('id'):
                            video_ids.append({
                                "video_id": video_info['id'],
                                "title": video_info.get('title', ''),
                                "url": f"https://www.youtube.com/watch?v={video_info['id']}"
                            })
                    except json.JSONDecodeError:
                        continue
            
            print(f"✅ Found {len(video_ids)} videos")
            return video_ids
            
        except Exception as e:
            print(f"❌ Error getting video IDs: {e}")
            return []
    
    def save_video_ids(self, video_ids):
        """Save video IDs to JSON file"""
        if not video_ids:
            print("❌ No video IDs to save")
            return
        
        # Save video IDs
        ids_file = os.path.join(self.youtube_dir, "youtube_video_ids.json")
        with open(ids_file, 'w', encoding='utf-8') as f:
            json.dump(video_ids, f, ensure_ascii=False, indent=2)
        
        # Save summary
        summary = {
            "extraction_date": datetime.now().isoformat(),
            "total_videos_found": len(video_ids),
            "channel": "Labellerr",
            "video_ids": [v["video_id"] for v in video_ids]
        }
        
        summary_file = os.path.join(self.youtube_dir, "video_ids_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"📁 Video IDs saved to: {ids_file}")
        print(f"📊 Summary saved to: {summary_file}")
        return ids_file
    
    def run(self):
        """Main execution method"""
        video_ids = self.get_channel_video_ids()
        if video_ids:
            return self.save_video_ids(video_ids)
        return None

def main():
    extractor = YouTubeVideoIDExtractor()
    extractor.run()

if __name__ == "__main__":
    main()
