
import unittest
from app import create_app, db, bcrypt
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.services.role_service import RoleService
from app.services.permission_service import PermissionService

class RBACCoreTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create permissions
        self.perm_view = Permission(name='inventory.view', module='inventory', description='View inventory')
        self.perm_edit = Permission(name='inventory.edit', module='inventory', description='Edit inventory')
        db.session.add_all([self.perm_view, self.perm_edit])
        db.session.commit()
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def test_user_creation(self):
        """Test user creation and password hashing"""
        u = User(username='test', email='test@example.com')
        u.set_password('password')
        db.session.add(u)
        db.session.commit()
        
        self.assertTrue(u.check_password('password'))
        self.assertFalse(u.check_password('wrong'))
        
    def test_role_creation(self):
        """Test role creation"""
        r = Role(name='admin', display_name='Administrator')
        db.session.add(r)
        db.session.commit()
        
        self.assertEqual(Role.query.count(), 1)
        self.assertEqual(Role.query.first().name, 'admin')
        
    def test_assign_role_permission(self):
        """Test assigning permissions to roles and roles to users"""
        # Create User
        u = User(username='staff', email='staff@example.com')
        u.set_password('password')
        db.session.add(u)
        
        # Create Role
        r = Role(name='staff', display_name='Staff')
        db.session.add(r)
        db.session.commit()
        
        # Assign Permission to Role
        RoleService.sync_permissions(r.id, ['inventory.view'])
        
        # Assign Role to User
        RoleService.assign_role_to_user(u.id, r.id, 1) # 1 is mocked admin id
        
        # Check permissions
        self.assertTrue(u.has_permission('inventory.view'))
        self.assertFalse(u.has_permission('inventory.edit'))
        self.assertTrue(u.has_role('staff'))
        
    def test_multiple_roles(self):
        """Test user permissions with multiple roles"""
        u = User(username='manager', email='manager@example.com')
        u.set_password('password')
        
        r1 = Role(name='viewer', display_name='Viewer')
        r2 = Role(name='editor', display_name='Editor')
        db.session.add_all([u, r1, r2])
        db.session.commit()
        
        RoleService.sync_permissions(r1.id, ['inventory.view'])
        RoleService.sync_permissions(r2.id, ['inventory.edit'])
        
        RoleService.assign_role_to_user(u.id, r1.id, 1)
        RoleService.assign_role_to_user(u.id, r2.id, 1)
        
        # Should have both permissions
        self.assertTrue(u.has_permission('inventory.view'))
        self.assertTrue(u.has_permission('inventory.edit'))

if __name__ == '__main__':
    unittest.main()
