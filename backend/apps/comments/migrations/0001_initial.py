import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('author_name', models.CharField(max_length=150)),
                ('author_email', models.EmailField(max_length=254)),
                ('homepage', models.URLField(blank=True)),
                ('html_text', models.TextField()),
                ('search_text', models.TextField()),
                ('depth', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='comments.comment')),
                ('root', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='branch_comments', to='comments.comment')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='comments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at', '-id'],
                'indexes': [models.Index(fields=['parent', 'created_at'], name='comments_co_parent__10bc81_idx'), models.Index(fields=['root', 'created_at'], name='comments_co_root_id_45b474_idx'), models.Index(condition=models.Q(('parent__isnull', True)), fields=['-created_at', '-id'], name='comment_root_date_idx'), models.Index(condition=models.Q(('parent__isnull', True)), fields=['author_name', 'id'], name='comment_root_name_idx'), models.Index(condition=models.Q(('parent__isnull', True)), fields=['author_email', 'id'], name='comment_root_email_idx')],
                'constraints': [models.CheckConstraint(condition=models.Q(('parent__isnull', False), ('depth', 0), _connector='OR'), name='root_comment_depth_zero')],
            },
        ),
    ]
