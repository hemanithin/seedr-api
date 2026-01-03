"""
VLC Playback Test Script

This script demonstrates how to use the VLC playback API endpoint.
"""

import requests
import json

BASE_URL = "http://localhost:5000/api/v1"


def check_vlc_config():
    """Check VLC configuration"""
    print("Checking VLC configuration...")
    response = requests.get(f"{BASE_URL}/vlc/config")
    print(json.dumps(response.json(), indent=2))
    return response.json()


def play_in_vlc(url, enqueue=False):
    """Play a URL in VLC"""
    print(f"\nPlaying in VLC (enqueue={enqueue})...")
    print(f"URL: {url}")
    
    response = requests.post(
        f"{BASE_URL}/vlc/play",
        json={
            "url": url,
            "enqueue": enqueue
        }
    )
    
    result = response.json()
    print(f"Status Code: {response.status_code}")
    print(json.dumps(result, indent=2))
    return result


def main():
    print("=" * 60)
    print("VLC Playback API Test")
    print("=" * 60)
    
    # Check VLC configuration
    config = check_vlc_config()
    
    if not config.get('vlc_exists'):
        print("\n⚠️  WARNING: VLC not found at the configured path!")
        print(f"Path: {config.get('vlc_path')}")
        print("Please install VLC or update VLC_PATH in routes/vlc.py")
        return
    
    print("\n✅ VLC found and ready!")
    
    # Example: Play a sample video URL
    # Replace this with an actual download URL from Seedr
    sample_url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    
    print("\n" + "=" * 60)
    print("Test 1: Play immediately")
    print("=" * 60)
    play_in_vlc(sample_url, enqueue=False)
    
    # Uncomment to test playlist enqueue
    # print("\n" + "=" * 60)
    # print("Test 2: Add to playlist (enqueue)")
    # print("=" * 60)
    # play_in_vlc(sample_url, enqueue=True)


if __name__ == "__main__":
    main()
