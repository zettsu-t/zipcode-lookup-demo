from django import forms
from .models import Sender, Guest


class NamesWidget(forms.Textarea):
    """names（JSON list）を改行区切りテキストとして表示・入力するウィジェット"""


class NamesField(forms.CharField):
    widget = forms.Textarea(attrs={"rows": 3, "placeholder": "山田 太郎\n山田 花子"})

    def prepare_value(self, value):
        if isinstance(value, list):
            return "\n".join(value)
        return value or ""

    def to_python(self, value):
        text = super().to_python(value)
        names = [n.strip() for n in text.splitlines() if n.strip()]
        if not names:
            raise forms.ValidationError("名前を1名以上入力してください。")
        return names


class SenderForm(forms.ModelForm):
    names = NamesField(label="氏名（連名・1行1名）")

    class Meta:
        model = Sender
        fields = ["names", "zipcode", "address"]
        widgets = {
            "zipcode": forms.TextInput(attrs={"placeholder": "例: 231-0017", "maxlength": "8"}),
            "address": forms.TextInput(
                attrs={"placeholder": "郵便番号を入力すると自動補完されます"}
            ),
        }
        labels = {
            "zipcode": "郵便番号",
            "address": "住所",
        }


class GuestForm(forms.ModelForm):
    names = NamesField(label="氏名（連名・1行1名、最大5名）")

    class Meta:
        model = Guest
        fields = ["names", "zipcode", "address"]
        widgets = {
            "zipcode": forms.TextInput(attrs={"placeholder": "例: 231-0017", "maxlength": "8"}),
            "address": forms.TextInput(attrs={"placeholder": "住所"}),
        }
        labels = {
            "zipcode": "郵便番号",
            "address": "住所",
        }

    def clean_names(self):
        names = self.cleaned_data["names"]
        if len(names) > 5:
            raise forms.ValidationError("連名は最大5名までです。")
        return names
