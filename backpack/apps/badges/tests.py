from pymongo import Connection
from django.test import TestCase
from django.conf import settings
from models import Badge

def setup_test_database():
    """
    Take the defined name of the database, append _test.
    """
    name = (settings.MONGO_DB['NAME'] + '_test')
    host = settings.MONGO_DB['HOST']
    port = settings.MONGO_DB['PORT']
    CONNECTION = Connection(host=(host if host else None), port=(port if port else None))
    CONNECTION.drop_database(name)
    settings.MONGO_DB['NAME'] = name

class BasicTests(TestCase):
    def setUp(self):
        self.valid_badge = {
            'url': 'http://localhost/audio.badge',
            'name': 'Audo Expert',
            'description': "For rockin' beats",
            'recipient': 'test@example.com',
            'evidence': '/badges/audio.html',
            'expires': '2020-1-1',
            'icons': {'128': '/images/audio_128.png',},
            'ttl': 60 * 60 * 24,
        }
        self.valid = Badge(self.valid_badge)
    
    def tearDown(self):
        # remove all created badges
        map(lambda b: b.delete(), Badge.objects.all())
    
    def test_validation(self):
        missing_recipient_badge = self.valid_badge.copy()
        del missing_recipient_badge['recipient']
        missing_recipient = Badge(missing_recipient_badge)

        self.assertTrue(self.valid.is_valid(), "Valid badge should be valid")
        self.assertFalse(missing_recipient.is_valid(), "Invalid badge should be invalid")

    def test_error_messaging(self):
        missing_recipient_badge = self.valid_badge.copy()
        missing_description_badge = self.valid_badge.copy()
        invalid_expires_badge = self.valid_badge.copy()
        del missing_recipient_badge['recipient']
        del missing_description_badge['description']
        invalid_expires_badge['expires'] = 'jalji12!'
        
        missing_recipient = Badge(missing_recipient_badge)
        missing_description = Badge(missing_description_badge)
        invalid_expires = Badge(invalid_expires_badge)

        self.assertIn('expires', invalid_expires.errors().keys())
        self.assertIn('recipient', missing_recipient.errors().keys())
        self.assertIn('description', missing_description.errors().keys())
        
    def test_save_and_delete(self):
        self.assertRaises(AssertionError, self.valid.delete)
        self.assertTrue(self.valid.save())
        self.assertEqual(Badge.objects.all().count(), 1)
        
        self.valid.delete()
        self.assertEqual(Badge.objects.all().count(), 0)
        self.assertRaises(AssertionError, self.valid.delete)
    
    def test_save_and_retrieve(self):
        self.assertTrue(self.valid.save())
        
        all_items = Badge.objects.all()
        self.assertEqual(all_items.count(), 1)
        
        badge = all_items.next()
        self.assertEqual(self.valid, badge)

    def test_filtering(self):
        other_badge = self.valid_badge.copy()
        other_badge['recipient'] = 'blurgh@example.com'
        
        self.valid.save()
        Badge(other_badge).save()
        
        badges = Badge.objects.filter(recipient='test@example.com')
        self.assertEqual(badges.count(), 1)
        self.assertEqual(badges.next(), self.valid)

    def test_find_one(self):
        self.valid.save()
        self.assertEqual(self.valid, Badge.objects.get(pk=self.valid.fields['_id']))
    
    def test_grouping(self):
        # add to group
        self.valid.add_to_group('linkedin')
        self.valid.save()
        badge = Badge.objects.get(pk=self.valid.fields['_id'])
        self.assertIn('linkedin', badge.groups())
        
        # remove from group
        badge.remove_from_group('linkedin')
        badge.save()
        
        badge_again = Badge.objects.get(pk=badge.fields['_id'])
        self.assertNotIn('linkedin', badge_again.groups())
        
        # find by group?
        
setup_test_database()
