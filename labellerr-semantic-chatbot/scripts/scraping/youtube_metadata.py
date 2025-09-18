#!/usr/bin/env python3
"""
Get full metadata for YouTube videos
"""
import os
import json
import subprocess
from datetime import datetime

class YouTubeMetadataExtractor:
    def __init__(self, output_dir="data_ingest/raw/youtube"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def load_video_ids(self):
        """Load video IDs from the previous step"""
        ids_file = os.path.join(self.output_dir, "youtube_video_ids.json")
        
        if not os.path.exists(ids_file):
            print(f"❌ Video IDs file not found: {ids_file}")
            print("Run youtube_video_ids.py first!")
            return []
        
        with open(ids_file, 'r', encoding='utf-8') as f:
            video_data = json.load(f)
        
        return [item["video_id"] for item in video_data]
    
    def fetch_full_metadata(self, video_id):
        """Get full metadata for a single video"""
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--no-warnings",
            "--dump-json",
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                raise RuntimeError(f"yt-dlp error: {proc.stderr.strip()}")
            
            return json.loads(proc.stdout)
        except Exception as e:
            print(f"❌ Failed to get metadata for {video_id}: {e}")
            return None
    
    def extract_all_metadata(self):
        """Extract metadata for all videos"""
        video_ids = self.load_video_ids()
        if not video_ids:
            return
        
        print(f"🚀 Getting metadata for {len(video_ids)} videos...")
        
        videos = []
        failed_videos = []
        
        for i, video_id in enumerate(video_ids, 1):
            print(f"[{i}/{len(video_ids)}] Getting metadata for: {video_id}")
            
            metadata = self.fetch_full_metadata(video_id)
            if metadata:
                video_data = {
                    "video_id": metadata["id"],
                    "title": metadata.get("title", ""),
                    "description": metadata.get("description", ""),
                    "video_url": metadata.get("webpage_url", ""),
                    "embed_url": metadata.get("embed_url", f"https://www.youtube.com/embed/{metadata['id']}"),
                    "duration": metadata.get("duration"),
                    "view_count": metadata.get("view_count"),
                    "upload_date": metadata.get("upload_date"),
                    "uploader": metadata.get("uploader"),
                    "tags": metadata.get("tags", []),
                    "categories": metadata.get("categories", [])
                }
                videos.append(video_data)
                print(f"  ✅ {metadata.get('title', 'Untitled')[:50]}...")
            else:
                failed_videos.append(video_id)
        
        # Save results
        self.save_metadata(videos, failed_videos)
        return videos
    
    def save_metadata(self, videos, failed_videos):
        """Save metadata to files"""
        # Main metadata file
        metadata_file = os.path.join(self.output_dir, "youtube_videos_metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(videos, f, ensure_ascii=False, indent=2)
        
        # Failed videos
        if failed_videos:
            failed_file = os.path.join(self.output_dir, "failed_metadata.json")
            with open(failed_file, 'w', encoding='utf-8') as f:
                json.dump(failed_videos, f, ensure_ascii=False, indent=2)
        
        # Summary
        summary = {
            "extraction_completed_at": datetime.now().isoformat(),
            "total_videos_processed": len(videos) + len(failed_videos),
            "successful_metadata": len(videos),
            "failed_metadata": len(failed_videos),
            "total_duration_seconds": sum(v.get("duration", 0) or 0 for v in videos),
            "average_duration_minutes": (sum(v.get("duration", 0) or 0 for v in videos) / len(videos) / 60) if videos else 0
        }
        
        summary_file = os.path.join(self.output_dir, "metadata_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎉 Metadata extraction completed!")
        print(f"📊 Successfully processed: {len(videos)} videos")
        print(f"❌ Failed: {len(failed_videos)} videos")
        print(f"📁 Saved to: {metadata_file}")

def main():
    extractor = YouTubeMetadataExtractor()
    extractor.extract_all_metadata()

if __name__ == "__main__":
    main()
