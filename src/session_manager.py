# File: src\session_manager.py
"""
Session manager for tracking visitor presence
"""
import time
from typing import Dict, Optional
from datetime import datetime
from src.config import SESSION_TIMEOUT


class SessionManager:
    """Manage active visitor sessions"""
    
    def __init__(self):
        self.active_sessions = {}  # profile_id -> session_data
        self.timeout = SESSION_TIMEOUT
        print(f"✅ Session manager initialized (timeout: {self.timeout}s)")
    
    def start_session(self, profile_id: int, profile_data: Dict) -> Dict:
        """
        Start or resume a session
        
        Args:
            profile_id: Profile ID
            profile_data: Profile information
        
        Returns:
            Session dictionary
        """
        now = time.time()
        
        # Check if session already exists
        if profile_id in self.active_sessions:
            session = self.active_sessions[profile_id]
            session['last_seen'] = now
            session['frames_detected'] += 1
            return session
        
        # Create new session
        session = {
            'profile_id': profile_id,
            'profile_data': profile_data,
            'start_time': now,
            'last_seen': now,
            'frames_detected': 1,
            'last_analysis_time': 0,
            'current_analysis': None,
            'ai_message': None,
            'message_shown': False
        }
        
        self.active_sessions[profile_id] = session
        print(f"🆕 New session started for profile {profile_id}")
        
        return session
    
    def update_session(self, profile_id: int, analysis: Optional[Dict] = None, 
                      ai_message: Optional[str] = None):
        """
        Update session with new data
        
        Args:
            profile_id: Profile ID
            analysis: Latest analysis results
            ai_message: Generated AI message
        """
        if profile_id not in self.active_sessions:
            return
        
        session = self.active_sessions[profile_id]
        now = time.time()
        
        session['last_seen'] = now
        
        if analysis:
            session['current_analysis'] = analysis
            session['last_analysis_time'] = now
        
        if ai_message:
            session['ai_message'] = ai_message
            session['message_shown'] = False
    
    def get_session(self, profile_id: int) -> Optional[Dict]:
        """Get active session"""
        return self.active_sessions.get(profile_id)
    
    def is_active(self, profile_id: int) -> bool:
        """Check if session is still active"""
        if profile_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[profile_id]
        time_since_last = time.time() - session['last_seen']
        
        return time_since_last < self.timeout
    
    def should_analyze(self, profile_id: int, interval: float = 2.5) -> bool:
        """
        Check if enough time has passed for new analysis
        
        Args:
            profile_id: Profile ID
            interval: Minimum seconds between analyses
        
        Returns:
            True if analysis should be performed
        """
        if profile_id not in self.active_sessions:
            return True
        
        session = self.active_sessions[profile_id]
        time_since_analysis = time.time() - session['last_analysis_time']
        
        return time_since_analysis >= interval
    
    def cleanup_sessions(self) -> list:
        """
        Remove expired sessions
        
        Returns:
            List of ended profile IDs
        """
        now = time.time()
        ended_sessions = []
        
        for profile_id, session in list(self.active_sessions.items()):
            time_since_last = now - session['last_seen']
            
            if time_since_last >= self.timeout:
                # Calculate session duration
                duration = int(session['last_seen'] - session['start_time'])
                
                print(f"⏱️  Session ended for profile {profile_id} (duration: {duration}s)")
                
                ended_sessions.append({
                    'profile_id': profile_id,
                    'duration': duration,
                    'frames_detected': session['frames_detected']
                })
                
                # Remove from active sessions
                del self.active_sessions[profile_id]
        
        return ended_sessions
    
    def get_active_count(self) -> int:
        """Get number of active sessions"""
        return len(self.active_sessions)
    
    def get_all_active(self) -> Dict[int, Dict]:
        """Get all active sessions"""
        return self.active_sessions.copy()
    
    def mark_message_shown(self, profile_id: int):
        """Mark that AI message has been displayed"""
        if profile_id in self.active_sessions:
            self.active_sessions[profile_id]['message_shown'] = True
    
    def get_session_duration(self, profile_id: int) -> float:
        """Get current session duration in seconds"""
        if profile_id not in self.active_sessions:
            return 0.0
        
        session = self.active_sessions[profile_id]
        return time.time() - session['start_time']
    
    def clear_all(self):
        """Clear all sessions (for shutdown)"""
        count = len(self.active_sessions)
        self.active_sessions.clear()
        print(f"🧹 Cleared {count} active sessions")


# Test
if __name__ == "__main__":
    manager = SessionManager()
    
    # Test session lifecycle
    print("\n=== Test 1: Start session ===")
    session = manager.start_session(1, {'name': 'Test User'})
    print(f"Session: {session}")
    
    print("\n=== Test 2: Check if should analyze ===")
    print(f"Should analyze? {manager.should_analyze(1)}")
    
    print("\n=== Test 3: Update session ===")
    time.sleep(1)
    manager.update_session(1, analysis={'age': 25}, ai_message="سلام!")
    print(f"Session: {manager.get_session(1)}")
    
    print("\n=== Test 4: Check timeout ===")
    time.sleep(2)
    print(f"Is active? {manager.is_active(1)}")
    
    print("\n=== Test 5: Cleanup ===")
    time.sleep(4)
    ended = manager.cleanup_sessions()
    print(f"Ended sessions: {ended}")
    print(f"Active sessions: {manager.get_active_count()}")