import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from .forms import GuestForm, SenderForm
from .models import Guest, Sender


class SenderView(View):
    template_name = "app/sender.html"

    def get_sender(self):
        return Sender.objects.first()

    def get(self, request):
        sender = self.get_sender()
        form = SenderForm(instance=sender)
        return render(request, self.template_name, {"form": form, "sender": sender})

    def post(self, request):
        sender = self.get_sender()
        form = SenderForm(request.POST, instance=sender)
        if form.is_valid():
            form.save()
            return redirect("sender")
        return render(request, self.template_name, {"form": form, "sender": sender})


class GuestListView(View):
    template_name = "app/guest_list.html"

    def get(self, request):
        guests = Guest.objects.all()
        return render(request, self.template_name, {"guests": guests})


class GuestCreateView(View):
    template_name = "app/guest_form.html"

    def get(self, request):
        return render(request, self.template_name, {"form": GuestForm(), "action": "追加"})

    def post(self, request):
        form = GuestForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("guest_list")
        return render(request, self.template_name, {"form": form, "action": "追加"})


class GuestUpdateView(View):
    template_name = "app/guest_form.html"

    def get(self, request, pk):
        guest = get_object_or_404(Guest, pk=pk)
        return render(
            request,
            self.template_name,
            {"form": GuestForm(instance=guest), "action": "編集", "guest": guest},
        )

    def post(self, request, pk):
        guest = get_object_or_404(Guest, pk=pk)
        form = GuestForm(request.POST, instance=guest)
        if form.is_valid():
            form.save()
            return redirect("guest_list")
        return render(request, self.template_name, {"form": form, "action": "編集", "guest": guest})


class GuestDeleteView(View):
    template_name = "app/guest_confirm_delete.html"

    def get(self, request, pk):
        guest = get_object_or_404(Guest, pk=pk)
        return render(request, self.template_name, {"guest": guest})

    def post(self, request, pk):
        guest = get_object_or_404(Guest, pk=pk)
        guest.delete()
        return redirect("guest_list")


class ZipLookupView(View):
    """郵便番号→住所をFastAPIにプロキシする"""

    def get(self, request):
        code = request.GET.get("code", "")
        try:
            resp = requests.get(
                f"{settings.BACKEND_URL}/api/v1/zip",
                params={"code": code},
                timeout=5,
            )
            return JsonResponse(resp.json(), status=resp.status_code)
        except requests.RequestException as e:
            return JsonResponse({"detail": f"バックエンドに接続できません: {e}"}, status=503)


class AddressLookupView(View):
    """住所→郵便番号をFastAPIにプロキシする"""

    def get(self, request):
        q = request.GET.get("q", "")
        try:
            resp = requests.get(
                f"{settings.BACKEND_URL}/api/v2/address",
                params={"q": q},
                timeout=5,
            )
            return JsonResponse(resp.json(), status=resp.status_code, safe=False)
        except requests.RequestException as e:
            return JsonResponse({"detail": f"バックエンドに接続できません: {e}"}, status=503)
