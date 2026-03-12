# CogniWatch Avatar Integration
# D-ID + edge-tts for talking security analyst

import requests
import uuid
import os
import time
from pathlib import Path

class DIdAvatar:
    """D-ID integration for talking avatar videos"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('DID_API_KEY')
        self.base_url = "https://api.d-id.com"
        self.headers = {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def create_talking_video(self, text, image_url=None, presenter_id=None, voice="americano"):
        """
        Create a talking head video from text
        
        Args:
            text: Script to speak
            image_url: URL of avatar image (or use default presenter)
            presenter_id: D-ID presenter ID (optional)
            voice: Voice ID (default: americano)
            
        Returns:
            dict: { 'id': video_id, 'status': 'created', 'result_url': url }
        """
        if not self.api_key:
            return {'error': 'D-ID API key not configured'}
        
        # Create talking head
        payload = {
            "script": {
                "type": "text",
                "input": text,
                "provider": {
                    "type": "microsoft",
                    "voice_id": voice
                }
            },
            "config": {
                "fluent": True,
                "pad_audio": 0.0
            }
        }
        
        # Use presenter or custom image
        if presenter_id:
            payload["source_url"] = presenter_id
        elif image_url:
            payload["source_url"] = image_url
        else:
            # Default D-ID presenter
            payload["source_url"] = "https://d-id-public-bucket.s3.amazonaws.com/alan.jpg"
        
        response = requests.post(
            f"{self.base_url}/talks",
            headers=self.headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 201:
            return {'error': f'D-ID API error: {response.status_code}', 'details': response.text}
        
        result = response.json()
        talk_id = result.get('id')
        
        # Poll for completion
        return self.wait_for_completion(talk_id)
    
    def wait_for_completion(self, talk_id, max_attempts=30):
        """Poll D-ID until video is ready"""
        for i in range(max_attempts):
            time.sleep(2)  # Wait 2 seconds between polls
            
            response = requests.get(
                f"{self.base_url}/talks/{talk_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code != 200:
                continue
            
            result = response.json()
            status = result.get('status')
            
            if status == 'done':
                return {
                    'id': talk_id,
                    'status': 'completed',
                    'result_url': result.get('result_url'),
                    'duration': result.get('duration')
                }
            elif status == 'error':
                return {'error': 'D-ID processing failed', 'details': result}
        
        return {'error': 'Timeout waiting for D-ID', 'id': talk_id}
    
    def download_video(self, result_url, save_path):
        """Download video to local path"""
        if not result_url:
            return {'error': 'No result URL provided'}
        
        response = requests.get(result_url, timeout=60)
        if response.status_code == 200:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return {'status': 'saved', 'path': save_path}
        else:
            return {'error': f'Download failed: {response.status_code}'}


# Convenience function for CogniWatch
def generate_avatar_response(message, save_as="latest_avatar.mp4"):
    """Quick helper to generate avatar video for a message"""
    avatar = DIdAvatar()
    
    print(f"🎬 Generating avatar video: '{message[:50]}...'")
    result = avatar.create_talking_video(message)
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return None
    
    # Download video
    save_path = f"/home/neo/cogniwatch/webui/static/avatars/{save_as}"
    download_result = avatar.download_video(result['result_url'], save_path)
    
    if download_result.get('status') == 'saved':
        print(f"✅ Video saved: {save_path}")
        return save_path
    else:
        print(f"❌ Download failed: {download_result}")
        return None


if __name__ == '__main__':
    # Test
    test_message = "Scan complete! I found 3 AI agents on your network: OpenClaw on port 18789, CrewAI on 192.168.0.45, and LangGraph on port 8080."
    generate_avatar_response(test_message)
