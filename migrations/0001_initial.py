# Generated by Django 2.1 on 2018-09-12 23:46

import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.utils.timezone
import webauth.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('email', models.EmailField(error_messages={'unique': 'A user with this email address already exists'}, max_length=254, unique=True, verbose_name='email address')),
                ('legacy_username', models.CharField(editable=False, help_text="The user's username on the old website, if applicable", max_length=100, null=True, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator(), webauth.models.no_at_in_uname], verbose_name='legacy username')),
                ('is_staff', models.BooleanField(default=False, help_text='Marks whether or not a user has access to the admin console.', verbose_name='staff')),
                ('is_superuser', models.BooleanField(default=False, help_text='Marks whether or not a user has root access.', verbose_name='superuser')),
                ('is_active', models.BooleanField(default=False, help_text='Indicates whether this account is active. Please use this setting instead of deleting accounts.', verbose_name='active')),
                ('lang', models.CharField(choices=[('nl-be', 'Nederlands'), ('en-gb', 'English')], default='nl-be', help_text='Controls the language of all automatically generated communication.', max_length=10, verbose_name='communication language')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            managers=[
                ('objects', webauth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
            ],
            options={
                'verbose_name': 'group',
                'verbose_name_plural': 'groups',
                'proxy': True,
                'indexes': [],
            },
            bases=('auth.group',),
            managers=[
                ('objects', django.contrib.auth.models.GroupManager()),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
    ]