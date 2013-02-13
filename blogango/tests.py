from django.test  import TestCase
from django.test.client import Client
from datetime import datetime
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage

from models import Blog, BlogEntry, Comment


class BlogTestCase(TestCase):

    def setUp(self):
        self.c = Client()

    def test_bloginstall_redirect(self):
        "check that the blog redirects to install page when there is no blog installed"
        response = self.c.get(reverse("blogango_index"))
        self.assertEqual(response.status_code, 302)

    def test_blogindex_access(self):
        Blog.objects.create(title='test', tag_line="blog",
                entries_per_page=10, recents=5, recent_comments=5)
        response = self.c.get(reverse("blogango_index"))
        self.assertEqual(response.status_code, 200)
        User.objects.create_user(username='foo', password='bar')
        self.c.login(username='foo', password='bar')
        response = self.c.get(reverse('blogango_install'))
        self.assertEqual(response.status_code, 302)

    def test_bloginstall(self):
        User.objects.create_user(username='foo', password='bar')
        response = self.c.get(reverse('blogango_install'))
        self.assertEqual(response.status_code, 302)
        self.c.login(username='foo', password='bar')
        response = self.c.get(reverse('blogango_install'))
        self.assertEqual(response.status_code, 200)

    def test_single_existence(self):
        """Test that the blog is created only once """
        self.blog = Blog(title="test", tag_line="new blog", entries_per_page=10,
                        recents=5, recent_comments=5)
        self.blog.save()
        blog = Blog(title="test", tag_line="new blog", entries_per_page=10,
                    recents=5, recent_comments=5)
        #should raise Exception when another blog is created
        self.assertRaises(Exception, blog.save)
        blog = Blog.objects.get()
        blog.title = 'edited'
        blog.save()
        self.assertEqual(Blog.objects.count(), 1)
        self.assertEqual(Blog.objects.get().title, 'edited')


class TestBlogEntry(TestCase):
    def setUp(self):
        self.blog = Blog(title="test", tag_line="new blog", entries_per_page=10,
                    recents=5, recent_comments=5)
        self.blog.save()
        self.c = Client()
        self.user = User.objects.create_user(username='gonecrazy', email='gonecrazy@gmail.com', password='gonecrazy')
        self.user.is_staff = True
        self.user.save()

    def test_blogentry_managers(self):
        """Test custom manager works as expected"""
        e1 = BlogEntry.objects.create(title="test", text='foo', created_by=self.user,
                    publish_date=datetime.today(), text_markup_type='plain',
                    is_published=False)
        e2 = BlogEntry.objects.create(title="test", text='foo', created_by=self.user,
                    publish_date=datetime.today(), text_markup_type='plain',
                    is_published=True)
        self.assertEqual(BlogEntry.default.count(), 2)
        self.assertEqual(BlogEntry.objects.count(), 1)


class TestViews(TestCase):
    """Test Views  of the blog"""

    def setUp(self):
        self.blog = Blog(title="test", tag_line="new blog", entries_per_page=10,
                    recents=5, recent_comments=5)
        self.blog.save()
        self.c = Client()
        self.user = User.objects.create_user(username='gonecrazy', email='gonecrazy@gmail.com', password='gonecrazy')
        self.user.is_staff = True
        self.user.save()

    def test_first_page(self):
        response = self.c.get(reverse("blogango_index"))
        #it should return 200 for all users
        self.assertEqual(response.status_code, 200)

    def test_entries_pagination(self):
        num_entries = 15
        for each in range(num_entries):
            BlogEntry.objects.create(title="test", text='foo', created_by=self.user,
                    publish_date=datetime.today(), text_markup_type='plain')
        self.assertEqual(BlogEntry.objects.count(), 15)
        response = self.c.get(reverse('blogango_page', args=[1]))
        self.assertEqual(response.status_code, 200)
        response = self.c.get(reverse('blogango_page', args=[2]))
        self.assertEqual(response.status_code, 200)
        response = self.c.get(reverse('blogango_page', args=[3]))
        self.assertEqual(response.status_code, 302)

    def test_entries_slug(self):
        e1 = BlogEntry.objects.create(title="test", text='foo', created_by=self.user,
                    publish_date=datetime.today(), text_markup_type='plain')
        e2 = BlogEntry.objects.create(title="test", text='foo', created_by=self.user,
                    publish_date=datetime.today(), text_markup_type='plain')
        self.assertNotEqual(e1.slug, e2.slug)
        e1 = BlogEntry.objects.get(pk=e1.pk)
        e2 = BlogEntry.objects.get(pk=e2.pk)
        e1.save()
        self.assertNotEqual(e1.slug, e2.slug)

    def test_tags_url(self):
        e1 = BlogEntry.objects.create(title="test", text='foo', created_by=self.user,
                    publish_date=datetime.today(), text_markup_type='plain')
        e2 = BlogEntry.objects.create(title="test", text='foo', created_by=self.user,
                    publish_date=datetime.today(), text_markup_type='plain')
        e1.tags.add("test1", "test2")
        e2.tags.add("test1")
        response = self.c.get(reverse('blogango_tag_details', args=['test1']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['entries']), 2)
        response = self.c.get(reverse('blogango_tag_details', args=['test2']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['entries']), 1)

    def test_add_entry(self):
        """Test whether a entry can be added to the blog """
        response = self.c.login(username='gonecrazy', password='gonecrazy')
        response = self.c.post(reverse("blogango_admin_entry_new"), {'title': 'test post',
            'text': 'this is the test post', 'publish_date_0': '2011-09-22',
            'publish_date_1': '17:17:55', 'text_markup_type': "html",
            'created_by': self.user.pk, 'publish': 'Save and Publish',
            'tags': "testing"})
        #check for successful posting of entry
        self.assertEqual(response.status_code, 302)
        entries = BlogEntry.default.all()
        self.assertEqual(1, entries.count())

    def test_entry_existence(self):
        """Test for the existence of entry"""
        BlogEntry.objects.create(**{'title': 'test post',
            'text': 'this is the test post',
            'publish_date': datetime.strptime("2011-09-22", "%Y-%m-%d"),
            'text_markup_type': "html",
            'created_by': self.user})
        response = self.c.get(reverse('blogango_details', args=['2011', '09', 'test-post']))
        self.assertEqual(response.status_code, 200)

    def test_edit_entry(self):
        """Test for editing a entry in the blog"""
        create_test_blog_entry(self.user)
        self.c.login(username='gonecrazy', password='gonecrazy')
        #edit a post .. the title is changed
        post = BlogEntry.objects.create(**{'title': 'test post',
                    'text': 'this is the test post',
                    'publish_date': datetime.strptime("2011-09-22", "%Y-%m-%d"),
                    'text_markup_type': "html",
                    'created_by': self.user})
        response = self.c.post("/blog/admin/entry/edit/%s/" % post.pk,
                {'title': 'the new test post', 'text': 'this is the test post',
                'publish_date_0': '2011-09-22', 'publish_date_1': '17:17:55',
                'text_markup_type': "html", 'created_by': self.user.pk, 'publish': 'Save and Publish',
                'tags': 'testing'})
        self.assertEqual(response.status_code, 302)
        entry = BlogEntry.default.get(pk=post.pk)
        self.assertEqual(entry.title, "the new test post")

    def test_add_comment(self):
        #test if a comment can be added to entry
        create_test_blog_entry(self.user)
        entry = BlogEntry.default.all()[0]
        reponse = self.c.post(entry.get_absolute_url(), {'name': 'gonecrazy', 'email': 'plaban@agiliq.com',
                                                          'text': 'this is a comment', 'button': 'Comment'})
        comment = Comment.objects.get(comment_for=entry)
        comments = Comment.objects.filter(comment_for=entry)
        self.assertEqual(1, comments.count())
        self.assertEqual(comment.text, 'this is a comment')

    def test_author_details(self):
        create_test_blog_entry(self.user)
        response = self.c.get("/blog/author/%s/" % self.user.username)
        author_posts = response.context['author_posts']
        self.assertEqual(1, author_posts.count())

    def tearDown(self):
        self.blog.delete()
        self.user.delete()


class TestAdminActions(TestCase):
    """check for admin action on the blog"""
    def setUp(self):
        self.c = Client()
        self.blog = Blog(title="test", tag_line="new blog", entries_per_page=10, recents=5, recent_comments=5)
        self.blog.save()
        self.user = User.objects.create_user(username='gonecrazy', email='gonecrazy@gmail.com', password='gonecrazy')
        self.user.is_staff = True
        self.user.save()
        response = self.c.login(username='gonecrazy', password='gonecrazy')
        entry = create_test_blog_entry(self.user)
        create_test_comment(entry)

    def test_check_adminpage(self):
        """Check that the admin page is accessible to everyone"""
        response = self.c.get(reverse('blogango_admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_change_preferences(self):
        """check if the admin can change the preferences of blog """
        response = self.c.post(reverse('blogango_admin_edit_preferences'), {'title': 'new Blog', 'tag_line': 'my new blog',
                                                                           'entries_per_page': 10, 'recents': 5, 'recent_comments': 5})
        blog = Blog.objects.all()[0]
        self.assertEqual(blog.title, 'new Blog')

    def test_admin_entrymanage(self):
        """Check if all the entries are retrieved to manage"""
        response = self.c.get(reverse('blogango_admin_entry_manage'))
        entries = response.context['entries']
        self.assertEqual(1, entries.count())

    def test_admin_commentmanage(self):
        """check if all the comments are retrieved to manage"""
        response = self.c.get(reverse('blogango_admin_comments_manage'))
        comments = response.context['comments']
        self.assertEqual(1, comments.count())


class TestStaticFiles(TestCase):
    """Check if app contains required static files"""
    def test_images(self):
        abs_path = finders.find('blogango/images/agiliq_blog_logo.png')
        self.assertTrue(staticfiles_storage.exists(abs_path))
        abs_path = finders.find('blogango/images/person_default.jpg')
        self.assertTrue(staticfiles_storage.exists(abs_path))

    def test_css(self):
        abs_path = finders.find('blogango/css/as_blog_styles.css')
        self.assertTrue(staticfiles_storage.exists(abs_path))
        abs_path = finders.find('blogango/css/prettify.css')


def create_test_blog_entry(user):
    return BlogEntry.objects.create(**{'title': 'example post',
            'text': 'this is the test post',
            'publish_date': datetime.strptime("2011-09-22", "%Y-%m-%d"),
            'text_markup_type': "html",
            'created_by': user})


def create_test_comment(entry):
    Comment.objects.create(text="foo", comment_for=entry)
