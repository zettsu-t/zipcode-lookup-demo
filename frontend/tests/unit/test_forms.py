"""NamesFieldのユニットテスト"""

import pytest
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "app",
        ],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
    )
    django.setup()

from django import forms
from app.forms import NamesField


def test_empty_input_raises_validation_error():
    field = NamesField()
    with pytest.raises(forms.ValidationError) as exc_info:
        field.clean("")
    assert "1名以上" in str(exc_info.value)


def test_single_name_returns_list():
    field = NamesField()
    result = field.clean("山田 太郎")
    assert result == ["山田 太郎"]


def test_multiline_input_returns_list():
    field = NamesField()
    result = field.clean("山田 太郎\n山田 花子")
    assert result == ["山田 太郎", "山田 花子"]


def test_whitespace_only_lines_are_ignored():
    field = NamesField()
    result = field.clean("山田 太郎\n\n  \n山田 花子")
    assert result == ["山田 太郎", "山田 花子"]


def test_over_five_names_raises_validation_error():
    from app.forms import GuestForm

    data = {
        "names": "名前1\n名前2\n名前3\n名前4\n名前5\n名前6",
        "zipcode": "",
        "address": "",
    }
    form = GuestForm(data=data)
    assert not form.is_valid()
    assert "5名まで" in str(form.errors["names"])
