from colorfield.fields import ColorField
from django.core.validators import MinValueValidator
from django.db import models
from users.models import User

MAX_NAME_LENGTH = 200
MAX_COLOR_LENGTH = 7
MIN_TIME_COOK = MinValueValidator(1)
MIN_AMOUNT_INGR = 1


class Ingredient(models.Model):
    name = models.CharField(
        'Название',
        max_length=MAX_NAME_LENGTH
    )
    measurement_unit = models.CharField(
        max_length=MAX_NAME_LENGTH
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        unique=True
    )
    color = ColorField(
        'Цветовой HEX-код',
        max_length=MAX_COLOR_LENGTH,
        unique=True,
        default='#FF0000'
    )
    slug = models.SlugField(
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        unique_together = ('name', 'slug')

    def __str__(self):
        return f'{self.name}, {self.slug}'


class Recipes(models.Model):
    name = models.CharField(
        'Название рецепта',
        max_length=MAX_NAME_LENGTH
    )
    text = models.TextField(
        'Описание',
        blank=False
    )
    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='recipes',
        verbose_name='Автор'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        through='recipes.IngredientsList',
        verbose_name='Ингредиенты'
    )
    image = models.ImageField(
        upload_to='media',
        null=True,
        blank=False
    )
    tags = models.ManyToManyField(
        Tag,
        blank=False,
        related_name='recipes'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MIN_TIME_COOK]
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)


class IngredientsList(models.Model):
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='ingredient'
    )
    ingredients = models.ForeignKey(
        Ingredient,
        related_name='recipe',
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MIN_TIME_COOK]
    )

    class Meta:
        ordering = ('recipe__name',)

    def __str__(self):
        return f'{self.recipe}, {self.ingredients}, {self.amount}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        related_name='favorites',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipes,
        related_name='favorites',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_cart'

    def __str__(self):
        return f'{self.user} - {self.recipe}'
