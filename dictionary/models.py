from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models, transaction
from django.db.models import F, Q, QuerySet
from django.forms import ValidationError


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email),
            **extra_fields,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given email and password.
        """
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        user = self.create_user(email, password, **extra_fields)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"

    def __str__(self):
        return self.email

    @property
    def is_staff(self):
        "Each superuser is a staff member."
        return self.is_superuser

    def add_word_to_dictionary(
            self, 
            source_language: str, 
            target_language: str,
            word: str, 
            translation: str
    ) -> None:
        """
        Add a word to the user's dictionary.

        Args:
            source_language (str): source language code
            target_language (str): target language code
            word (str): word to translate
            translation (str): translation of the word

        Returns:
            None
        """
        dictionary = self.dictionaries.get(
                user=self,
                source_language__code=source_language,
                target_language__code=target_language,
            )
        with transaction.atomic():
            dictionary.add_translation(word, translation)

    def get_word_translations(self, word, source_language, target_language):
        """
        Return translations of a word in user's dictionary.

        Args:
            word (str): word to translate
            source_language (str): source language code
            target_language (str): target language code

        Returns:
            list: list of translations
        """
        dictionary = self.dictionaries.get(
            source_language__code=source_language,
            target_language__code=target_language,
        )
        return dictionary.get_translations(word)

    def get_total_translations(self):
        """
        Return the total number of translations in all user's dictionaries.

        Returns:
            int: total number of user's translations
        """
        dictionaries = self.dictionaries.annotate(
            translations_count=models.Count('translations')
        )
        total_translations = dictionaries.aggregate(
            total=models.Sum('translations_count')
        )['total']

        return total_translations if total_translations else 0
        
        
class Word(models.Model):
    word = models.TextField()
    language = models.ForeignKey("Language", on_delete=models.CASCADE)
    translations = models.ManyToManyField(
        "self",
        through="Translation",
        symmetrical=False,
        related_name="translated_words",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["word", "language"], name="unique_word_language"
            )
        ]

    def __str__(self):
        return self.word

    def save(self, *args, **kwargs):
        self.word = self.word.lower()
        super().save(*args, **kwargs)


class Language(models.Model):
    code = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Translation(models.Model):
    from_word = models.ForeignKey(
        Word, on_delete=models.CASCADE, related_name="source_word"
    )
    to_word = models.ForeignKey(
        Word, on_delete=models.CASCADE, related_name="target_word"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["to_word", "from_word"],
                name="unique_translation_pair_reverse"
            ),
        ]

    def __str__(self):
        return f"{self.from_word} -> {self.to_word}"
    
    def save(self, *args, **kwargs):
        if self.from_word.language == self.to_word.language:
            raise ValidationError("from_word and to_word cannot have the same language.")
        super().save(*args, **kwargs)
        
    @classmethod
    def get_approved_translations(cls, word, source_language, target_language):
        return cls.objects.filter(
            from_word__word=word,
            from_word__language__code=source_language,
            to_word__language__code=target_language,
            is_approved=True
        )


class Dictionary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="dictionaries")
    translations = models.ManyToManyField(Translation, related_name="+")
    source_language = models.ForeignKey(
        Language, related_name="+", on_delete=models.CASCADE
    )
    target_language = models.ForeignKey(
        Language, related_name="+", on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~Q(source_language=F('target_language')),
                name='different_languages',
                violation_error_message='Source and target languages must be different.'
            ),
            models.UniqueConstraint(
                fields=['user', 'source_language', 'target_language'],
                name='unique_language_pair_per_user'
            )
        ]

    def __str__(self):
        return f"{self.user}'s dictionary"

    def add_translation(self, from_word: str, to_word: str) -> None:
        """
        Add a translation to the user's dictionary.

        Args:
            from_word (str): word to translate
            to_word (str): translation of the word

        Returns:
            bool: True if the translation was added, False otherwise.
        """
        from_word = Word.objects.get_or_create(
            word=from_word, 
            language=self.source_language
        )[0]
        to_word = Word.objects.get_or_create(
            word=to_word, 
            language=self.target_language
        )[0]
        translation = Translation.objects.get_or_create(
            from_word=from_word, 
            to_word=to_word
        )[0]
        self.translations.add(translation)

    def get_translations(self, word: str) -> QuerySet:
        """
        Return translations of a word in the user's dictionary.

        Args:
            word (str): word to translate

        Returns:
            QuerySet: QuerySet of translations for a word in particular dictionary.
        """
        return self.translations.filter(from_word__word=word)