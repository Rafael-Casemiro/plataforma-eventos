import pytest
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

User = get_user_model()


@pytest.mark.django_db
class TestCreateUser:
    def test_creates_user_with_default_role_cliente(self):
        user = User.objects.create_user(
            email="cliente@example.com",
            first_name="Ana",
            last_name="Silva",
            password="senha123",
        )
        assert user.role == User.Role.CLIENTE

    def test_hashes_the_password(self):
        user = User.objects.create_user(
            email="cliente2@example.com",
            first_name="Ana",
            last_name="Silva",
            password="senha123",
        )
        assert user.password != "senha123"
        assert user.check_password("senha123")

    def test_normalizes_email_domain(self):
        user = User.objects.create_user(
            email="Cliente@EXAMPLE.COM",
            first_name="Ana",
            last_name="Silva",
            password="senha123",
        )
        assert user.email == "Cliente@example.com"

    def test_without_email_raises_value_error(self):
        with pytest.raises(ValueError):
            User.objects.create_user(
                email="", first_name="Ana", last_name="Silva", password="senha123"
            )

    def test_without_first_name_raises_value_error(self):
        with pytest.raises(ValueError):
            User.objects.create_user(
                email="cliente3@example.com",
                first_name="",
                last_name="Silva",
                password="senha123",
            )

    def test_without_last_name_raises_value_error(self):
        with pytest.raises(ValueError):
            User.objects.create_user(
                email="cliente4@example.com",
                first_name="Ana",
                last_name="",
                password="senha123",
            )

    def test_duplicate_email_raises_integrity_error(self):
        User.objects.create_user(
            email="duplicado@example.com",
            first_name="Ana",
            last_name="Silva",
            password="senha123",
        )
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email="duplicado@example.com",
                first_name="Outra",
                last_name="Pessoa",
                password="senha456",
            )


@pytest.mark.django_db
class TestCreateSuperuser:
    def test_sets_staff_superuser_and_role_organizador(self):
        admin = User.objects.create_superuser(
            email="admin@example.com",
            first_name="Admin",
            last_name="Root",
            password="senha123",
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.role == User.Role.ORGANIZADOR

    def test_with_is_staff_false_raises_value_error(self):
        with pytest.raises(ValueError):
            User.objects.create_superuser(
                email="admin2@example.com",
                first_name="Admin",
                last_name="Root",
                password="senha123",
                is_staff=False,
            )

    def test_with_is_superuser_false_raises_value_error(self):
        with pytest.raises(ValueError):
            User.objects.create_superuser(
                email="admin3@example.com",
                first_name="Admin",
                last_name="Root",
                password="senha123",
                is_superuser=False,
            )


@pytest.mark.django_db
class TestUserModel:
    def test_role_choices_are_limited_to_three_values(self):
        valid_values = {choice.value for choice in User.Role}
        assert valid_values == {"organizador", "cliente", "portaria"}

    def test_string_representation_is_the_email(self):
        user = User.objects.create_user(
            email="strrepr@example.com",
            first_name="Ana",
            last_name="Silva",
            password="senha123",
        )
        assert str(user) == "strrepr@example.com"
