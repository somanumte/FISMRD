
import unittest
from datetime import datetime, timedelta
from app import create_app, db
from app.models.user import User
from app.models.user_session import UserSession
from app.utils.security import validate_password_strength
from app.utils.session_manager import create_session, validate_session, terminate_current_session
from flask import session

class SecurityTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()
        
        # Helper User
        self.user = User(username='test', email='test@example.com')
        self.user.set_password('StrongPass1!')
        db.session.add(self.user)
        db.session.commit()
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def test_password_policy(self):
        """Test password strength validation logic"""
        # Weak
        self.assertFalse(validate_password_strength('weak')[0])
        self.assertFalse(validate_password_strength('NoNumber')[0])
        self.assertFalse(validate_password_strength('nocaps123')[0])
        self.assertFalse(validate_password_strength('NoSpecial1')[0])
        
        # Strong
        self.assertTrue(validate_password_strength('StrongPass1!')[0])
        
    def test_session_management_flow(self):
        """Test full session lifecycle"""
        with self.client as c:
            # Login logic (simulated by creating session directly)
            with c.session_transaction() as sess:
                user_sess = create_session(self.user)
                
            # Verify DB entry
            self.assertEqual(UserSession.query.count(), 1)
            self.assertTrue(UserSession.query.first().is_active)
            
            # Verify session validation
            with c.session_transaction() as sess:
                # Flask session should have token
                self.assertIn('session_token', sess)
                self.assertTrue(validate_session())
                
            # Logout
            terminate_current_session()
            
            # Verify DB entry is inactive
            self.assertFalse(UserSession.query.first().is_active)
            
            # Verify validation fails
            self.assertFalse(validate_session())
            
    def test_session_expiration(self):
        """Test that expired sessions are invalid"""
        # Create session manually with past expiry
        us = UserSession(
            user_id=self.user.id,
            session_token='expired_token',
            expires_at=datetime.utcnow() - timedelta(hours=1),
            is_active=True
        )
        db.session.add(us)
        db.session.commit()
        
        self.assertTrue(us.is_expired())
        self.assertFalse(us.is_valid())

if __name__ == '__main__':
    unittest.main()
