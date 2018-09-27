from django.db import models
from django.conf import settings
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _ 
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin, Group as BaseGroup
)
from django.contrib.auth.validators import UnicodeUsernameValidator
from webauth.email import dispatch_email, EmailDispatcher
from webauth import tokens

def mass_translated_email(users, subject_template_name, 
        context=None, rcpt_context_object_name='user', 
        attachments=None, override_email=None, **kwargs):
    """
    Mass-email users. Context can be a one-argument callable, 
    to which the user will be passed, or a static dict.
    The context dict passed to the email dispatcher will
    always include the user object.
    Other kwargs will be passed to the EmailDispatcher's __init__.

    This method will work with any model with a .lang and .email attribute.
    """

    def dynamic_data():
        for user in users:
            if callable(context):
                the_context = context(user)
            else:
                the_context = {} if context is None else context
            the_context[rcpt_context_object_name] = user
            # necessary for email reset functionality
            email = override_email or user.email
            yield email, user.lang, the_context

    # we have to consume the generator, otherwise pickle complains
    EmailDispatcher(
        subject_template_name, **kwargs
    ).send_dynamic_emails(list(dynamic_data()), attachments=attachments)

ACTIVATION_EMAIL_SUBJECT_TEMPLATE = 'mail/activation_email_subject.txt'
ACTIVATION_EMAIL_TEMPLATE = 'mail/activation_email.html'
UNLOCK_EMAIL_SUBJECT_TEMPLATE = 'mail/unlock_email_subject.txt'
UNLOCK_EMAIL_TEMPLATE = 'mail/unlock_email.html'
ACTIVATION_EMAIL_SUBJECT_TEMPLATE = 'mail/activation_email_subject.txt'
ACTIVATION_EMAIL_TEMPLATE = 'mail/activation_email.html'
PASSWORD_RESET_EMAIL_SUBJECT_TEMPLATE = 'mail/password_reset_subject.txt'
PASSWORD_RESET_EMAIL_TEMPLATE = 'mail/password_reset_email.html'

def dispatch_token_email(users, token_generator, subject_template_name, 
        email_template_name, html_email_template_name, 
        **kwargs):

    def context(user):
        token, valid_until = token_generator(user).make_token()
        return {
            'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
            'user': user,
            'token': token,
            'valid_until': valid_until
        }

    mass_translated_email(
        users,
        subject_template_name, 
        email_template_name=email_template_name,
        html_email_template_name=html_email_template_name,
        context=context, **kwargs
    )

def send_activation_email(users,
        subject_template_name=ACTIVATION_EMAIL_SUBJECT_TEMPLATE,
        email_template_name=None,
        html_email_template_name=ACTIVATION_EMAIL_TEMPLATE,
        token_generator=tokens.ActivationTokenGenerator,
        **kwargs):
    dispatch_token_email(
        users, token_generator=token_generator,
        subject_template_name=subject_template_name,
        email_template_name=email_template_name,
        html_email_template_name=html_email_template_name,
        **kwargs
    )

def send_unlock_email(users,
        subject_template_name=UNLOCK_EMAIL_SUBJECT_TEMPLATE,
        email_template_name=None,
        html_email_template_name=UNLOCK_EMAIL_TEMPLATE,
        token_generator=tokens.UnlockTokenGenerator,
        **kwargs):
    dispatch_token_email(
        users, token_generator=token_generator,
        subject_template_name=subject_template_name,
        email_template_name=email_template_name,
        html_email_template_name=html_email_template_name,
        **kwargs
    )

def send_password_reset_email(users,
        subject_template_name=PASSWORD_RESET_EMAIL_SUBJECT_TEMPLATE,
        email_template_name=None,
        html_email_template_name=PASSWORD_RESET_EMAIL_TEMPLATE,
        token_generator=tokens.PasswordResetTokenGenerator,
        **kwargs):
    dispatch_token_email(
        users, token_generator=token_generator,
        subject_template_name=subject_template_name,
        email_template_name=email_template_name,
        html_email_template_name=html_email_template_name,
        **kwargs
    )

class UserQuerySet(models.QuerySet):
    
    # wrappers around the functions defined above
    def mass_email(self, *args, **kwargs):
        mass_translated_email(self, *args, **kwargs)

    def send_activation_email(self, *args, **kwargs):
        send_activation_email(self, *args, **kwargs)



class UserManager(BaseUserManager):
    """
    Replaces django.contrib.auth.models.UserManager.
    Mostly copied from there, we only did away with the username
    requirement, and made email mandatory instead.
    """

    use_in_migrations = True

    def get_queryset(self):
        return UserQuerySet(self.model, using=self._db)

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError(_('An email address must be set.'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        if extra_fields.get('is_active') is not True:
            raise ValueError(_('Superuser must have is_active=True.'))

        return self._create_user(email, password, **extra_fields)
    

class User(AbstractBaseUser, PermissionsMixin):
    """
    User class with email authentication.
    Partly based on django.contrib.auth.models.AbstractUser, with a few changes.
    """
    
    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    # Apparently, it is an error to include the USERNAME_FIELD in REQUIRED_FIELDS
    REQUIRED_FIELDS = []

    email = models.EmailField(
        verbose_name = _('email address'),
        unique = True,
        error_messages={
            'unique': _(
                'A user with this email address '
                'already exists'
            )
        }
    )
 
    is_staff = models.BooleanField(
        verbose_name=_('staff'),
        help_text=_(
            'Marks whether or not a user has access '
            'to the admin console.'
        ),
        default=False
    )

    is_superuser = models.BooleanField(
        verbose_name=_('superuser'),
        help_text=_('Marks whether or not a user has root access.'),
        default=False
    )

    is_active = models.BooleanField(
        verbose_name=_('active'),
        help_text=_(
            'Indicates whether this account is active. '
            'Please use this setting instead of deleting accounts.'
        ),
        # Users start out as inactive, until they click the link
        # in their sign-up email
        default=False
    )

    lang = models.CharField(
        verbose_name=_('communication language'),
        help_text=_(
            'Controls the language of all automatically generated '
            'communication.' 
        ),
        max_length=10,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGES[0][0]
    )

    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    @property
    def username(self):
        """
        Some packages assume that users have a username attribute.
        """
        return self.email

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def send_email(self, subject_template_name, 
            email_template_name=None, html_email_template_name=None, **kwargs):
        # add user to context, if applicable
        context = kwargs.pop('context', {})
        context['user'] = self
        kwargs['context'] = context
        dispatch_email(
            subject_template_name, email_template_name=email_template_name,
            html_email_template_name=html_email_template_name,
            to_email=self.email, lang=self.lang,
            **kwargs
        )

    def send_activation_email(self, *args, **kwargs): 
        send_activation_email([self], *args, **kwargs)

    def send_unlock_email(self, *args, **kwargs):
        send_unlock_email([self], *args, **kwargs)

    def send_password_reset_email(self, *args, **kwargs):
        send_password_reset_email([self], *args, **kwargs)

# for future extensibility and admin consistency
class Group(BaseGroup): 
    class Meta:
        proxy = True
        verbose_name = _('group')
        verbose_name_plural = _('groups')
