from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db.utils import IntegrityError
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.permissions import IsCliente, IsOrganizador, IsPortaria

User = get_user_model()

AUTH_REGISTER_URL = "/api/v1/auth/register/"
AUTH_LOGIN_URL = "/api/v1/auth/login/"
AUTH_LOGOUT_URL = "/api/v1/auth/logout/"
AUTH_REFRESH_URL = "/api/v1/auth/refresh/"
AUTH_ME_URL = "/api/v1/auth/me/"


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


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def cliente_user(db):
    return User.objects.create_user(
        email="cliente@example.com",
        first_name="Ana",
        last_name="Silva",
        password="senha123",
        role=User.Role.CLIENTE,
    )


@pytest.fixture
def organizador_user(db):
    return User.objects.create_user(
        email="organizador@example.com",
        first_name="Rafael",
        last_name="Casemiro",
        password="senha123",
        role=User.Role.ORGANIZADOR,
    )


@pytest.fixture
def portaria_user(db):
    return User.objects.create_user(
        email="portaria@example.com",
        first_name="Portaria",
        last_name="Um",
        password="senha123",
        role=User.Role.PORTARIA,
    )


@pytest.mark.django_db
class TestRegisterView:
    def test_creates_user_and_returns_201(self, api_client):
        response = api_client.post(
            AUTH_REGISTER_URL,
            {
                "email": "novo@example.com",
                "first_name": "Novo",
                "last_name": "Usuario",
                "password": "senha1234",
                "password_confirm": "senha1234",
            },
            format="json",
        )
        assert response.status_code == 201
        assert User.objects.filter(email="novo@example.com").exists()

    def test_created_user_defaults_to_role_cliente(self, api_client):
        api_client.post(
            AUTH_REGISTER_URL,
            {
                "email": "novo2@example.com",
                "first_name": "Novo",
                "last_name": "Usuario",
                "password": "senha1234",
                "password_confirm": "senha1234",
            },
            format="json",
        )
        user = User.objects.get(email="novo2@example.com")
        assert user.role == User.Role.CLIENTE

    def test_password_mismatch_returns_400(self, api_client):
        response = api_client.post(
            AUTH_REGISTER_URL,
            {
                "email": "novo3@example.com",
                "first_name": "Novo",
                "last_name": "Usuario",
                "password": "senha1234",
                "password_confirm": "outrasenha",
            },
            format="json",
        )
        assert response.status_code == 400
        assert not User.objects.filter(email="novo3@example.com").exists()

    def test_duplicate_email_returns_400(self, api_client, cliente_user):
        response = api_client.post(
            AUTH_REGISTER_URL,
            {
                "email": cliente_user.email,
                "first_name": "Outro",
                "last_name": "Usuario",
                "password": "senha1234",
                "password_confirm": "senha1234",
            },
            format="json",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestLoginView:
    def test_valid_credentials_sets_cookies_and_returns_user(self, api_client, cliente_user):
        response = api_client.post(
            AUTH_LOGIN_URL,
            {"email": cliente_user.email, "password": "senha123"},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["user"]["email"] == cliente_user.email
        assert "access" in response.cookies
        assert "refresh" in response.cookies
        assert response.cookies["access"]["httponly"] is True
        assert response.cookies["refresh"]["httponly"] is True

    def test_wrong_password_returns_400(self, api_client, cliente_user):
        response = api_client.post(
            AUTH_LOGIN_URL,
            {"email": cliente_user.email, "password": "senhaerrada"},
            format="json",
        )

        assert response.status_code == 400
        assert "access" not in response.cookies

    def test_nonexistent_email_returns_400(self, api_client):
        response = api_client.post(
            AUTH_LOGIN_URL,
            {"email": "naoexiste@example.com", "password": "senha123"},
            format="json",
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestRefreshView:
    def test_valid_refresh_cookie_issues_new_access_cookie(self, api_client, cliente_user):
        api_client.post(
            AUTH_LOGIN_URL,
            {"email": cliente_user.email, "password": "senha123"},
            format="json",
        )

        response = api_client.post(AUTH_REFRESH_URL)

        assert response.status_code == 200
        assert "access" in response.cookies

    def test_missing_refresh_cookie_returns_401(self, api_client):
        response = api_client.post(AUTH_REFRESH_URL)
        assert response.status_code == 401

    def test_invalid_refresh_cookie_returns_401(self, api_client):
        api_client.cookies["refresh"] = "token-invalido"
        response = api_client.post(AUTH_REFRESH_URL)
        assert response.status_code == 401

    def test_expired_access_cookie_does_not_block_refresh(self, api_client, cliente_user):
        refresh = RefreshToken.for_user(cliente_user)
        access = refresh.access_token
        access.set_exp(lifetime=timedelta(seconds=-10))

        api_client.cookies["access"] = str(access)
        api_client.cookies["refresh"] = str(refresh)

        response = api_client.post(AUTH_REFRESH_URL)

        assert response.status_code == 200
        assert "access" in response.cookies


@pytest.mark.django_db
class TestLogoutView:
    def test_deletes_access_and_refresh_cookies(self, api_client, cliente_user):
        api_client.post(
            AUTH_LOGIN_URL,
            {"email": cliente_user.email, "password": "senha123"},
            format="json",
        )

        response = api_client.post(AUTH_LOGOUT_URL)

        assert response.status_code == 200
        assert response.cookies["access"].value == ""
        assert response.cookies["refresh"].value == ""


@pytest.mark.django_db
class TestMeView:
    def test_authenticated_user_can_fetch_own_data(self, api_client, cliente_user):
        api_client.post(
            AUTH_LOGIN_URL,
            {"email": cliente_user.email, "password": "senha123"},
            format="json",
        )

        response = api_client.get(AUTH_ME_URL)

        assert response.status_code == 200
        assert response.data["user"]["email"] == cliente_user.email

    def test_unauthenticated_request_returns_401(self, api_client):
        response = api_client.get(AUTH_ME_URL)
        assert response.status_code == 401


@pytest.mark.django_db
class TestCsrfProtection:
    def test_unsafe_request_with_valid_cookie_but_no_csrf_token_is_rejected(self, cliente_user):
        strict_client = APIClient(enforce_csrf_checks=True)
        login_response = strict_client.post(
            AUTH_LOGIN_URL,
            {"email": cliente_user.email, "password": "senha123"},
            format="json",
        )
        assert login_response.status_code == 200

        response = strict_client.post(AUTH_LOGOUT_URL)

        assert response.status_code == 403


@pytest.mark.django_db
class TestRolePermissions:
    def test_is_organizador_allows_organizador_role(self, organizador_user):
        request = SimpleNamespace(user=organizador_user)
        assert IsOrganizador().has_permission(request, None) is True

    def test_is_organizador_blocks_cliente_role(self, cliente_user):
        request = SimpleNamespace(user=cliente_user)
        assert IsOrganizador().has_permission(request, None) is False

    def test_is_cliente_allows_cliente_role(self, cliente_user):
        request = SimpleNamespace(user=cliente_user)
        assert IsCliente().has_permission(request, None) is True

    def test_is_portaria_allows_portaria_role(self, portaria_user):
        request = SimpleNamespace(user=portaria_user)
        assert IsPortaria().has_permission(request, None) is True

    def test_is_portaria_blocks_organizador_role(self, organizador_user):
        request = SimpleNamespace(user=organizador_user)
        assert IsPortaria().has_permission(request, None) is False

    def test_denies_unauthenticated_user(self):
        request = SimpleNamespace(user=AnonymousUser())
        assert IsOrganizador().has_permission(request, None) is False
