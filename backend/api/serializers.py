from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import (Favorite, Ingredient, IngredientsList, Recipes,
                            ShoppingCart, Tag)
from users.models import Subscribe, User

MIN_COOK_TIME = 1


# class Base64ImageField(serializers.ImageField):
#     def to_internal_value(self, data):
#         if isinstance(data, str) and data.startswith('data:image'):
#             format, imgstr = data.split(';base64,')
#             ext = format.split('/')[-1]
#             data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
#         return super().to_internal_value(data)


class CreateUserSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        ]


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        ]

    def get_is_subscribed(self, object):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscribe.objects.filter(user=user, author=object.id).exists()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = [
            'id',
            'name',
            'measurement_unit',]


class IngredientListSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredients.id')
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientsList
        fields = [
            'id',
            'name',
            'measurement_unit',
            'amount'
        ]


class RecipeSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = IngredientListSerializer(
        read_only=True,
        many=True,
        source='ingredient'
    )
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipes
        fields = [
            'id',
            'tags',
            'ingredients',
            'author',
            'name',
            'image',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        ]

    def get_is_favorited(self, object):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return object.favorites.filter(user=user).exists()

    def get_is_in_shopping_cart(self, object):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return object.shopping_cart.filter(user=user).exists()


class RecipeAddList(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientsList
        fields = [
            'id',
            'amount'
        ]


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipes
        fields = [
            'id',
            'name',
            'image',
            'cooking_time'
        ]


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = RecipeAddList(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=True
    )
    image = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = Recipes
        fields = [
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        ]

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data

    def validate(self, attrs):
        ingredients = attrs.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Выберите хотя бы 1 ингредиент!'
            )
        unique_ingredients = []
        for ingredient in ingredients:
            unique_ingredients.append(ingredient.get('id'))
        if len(unique_ingredients) != len(set(unique_ingredients)):
            raise ValidationError(
                {'error': 'Ингредиенты не должны повторяться'}
            )
        if not unique_ingredients:
            raise serializers.ValidationError('Добавьте ингредиент')
        return attrs

    def validate_tags(self, tags):
        unique_tags = []
        if not tags:
            raise serializers.ValidationError(
                'Выберите хотя бы 1 тег!'
            )
        for tag in tags:
            if tag in unique_tags:
                raise serializers.ValidationError(
                    'Теги не должны повторяться!'
                )
            unique_tags.append(tag)
        return tags

    def validate_cooking_time(self, value):
        if value < MIN_COOK_TIME:
            raise serializers.ValidationError(
                'Время готовки не может быть меньше минуты!'
            )
        return value

    def create_ingredient(self, ingredients_list, recipe):
        IngredientsList.objects.bulk_create(
            IngredientsList(
                ingredients=ingredient['id'],
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients_list
        )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = self.validate_tags(validated_data.pop('tags'))
        author = self.context.get('request').user
        recipe = Recipes.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredient(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        if 'tags' not in validated_data:
            raise serializers.ValidationError(
                'Поле "tags" обязательно для обновления!'
            )
        tags = validated_data.pop('tags')
        IngredientsList.objects.filter(recipe=instance).delete()
        instance.tags.set(tags)
        self.create_ingredient(ingredients, instance)
        return super().update(instance, validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        user, recipe = data.get('user'), data.get('recipe')
        if self.Meta.model.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError(
                {'error': 'Этот рецепт уже добавлен'}
            )
        return data

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return ShortRecipeSerializer(instance.recipe, context=context).data


class ShoppingListSerializer(FavoriteSerializer):
    class Meta(FavoriteSerializer.Meta):
        model = ShoppingCart


class SubscribeSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, object):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = object.recipes.all()
        if limit:
            queryset = queryset[:int(limit)]
        return ShortRecipeSerializer(queryset, many=True).data

    def get_is_subscribed(self, object):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscribe.objects.filter(user=user, author=object.id).exists()

    def get_recipes_count(self, object):
        return object.recipes.count()
