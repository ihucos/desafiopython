# -*- coding: utf-8 -*-
import json
from datetime import timedelta

from django.contrib.auth import authenticate, login
from django.http import HttpResponseBadRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import ProcessFormView

from .forms import UserCreateForm
from .models import User


class ConcreteSolutionsExampleAuthMixin(object):
    def dispatch(self, request, *args, **kw):
        token = self.request.META.get('HTTP_CONCRETESOLUTIONS_AUTH_TOKEN')
        if token is None:
            return JsonResponse({'mensagem': u"Não autorizado", 'error': 'NO_TOKEN'},
                                status=403)

        default_response = super(BaseDetailView, self).dispatch(request, *args, **kw)

        if token != str(self.object.token):
            return JsonResponse({'mensagem': u"Não autorizado", 'error': 'INVALID_TOKEN'},
                                status=403)
        timeout = timezone.now() - self.object.last_login > timedelta(minutes=30)
        if not self.object.last_login or timeout:
            return JsonResponse({'mensagem': u"Sessão inválida", 'error': 'SESSION_EXPIRED'},
                                status=403)

        return default_response


class UserView(ConcreteSolutionsExampleAuthMixin, BaseDetailView):
    model = User

    def render_to_response(self, context):
        return JsonResponse(self.object.dictify())


class UserCreate(ProcessFormView):
    http_method_names = ['post']

    def get_form(self):
        try:
            json_data = json.loads(self.request.body)
        except ValueError:
            return HttpResponseBadRequest()
        UserCreateForm.flatten_phones(json_data)
        return UserCreateForm(json_data)

    def form_invalid(self, form):
        validation_errors = {f: e.get_json_data() for f, e in form.errors.items()}
        if any(i['code'] == 'not_unique' for i in validation_errors.get('email', [])):
            return JsonResponse({
                'mensagem': u'E-mail já existente',
                'validation_errors': validation_errors,
                'error': 'EMAIL_TAKEN'}, status=400)
        else:
            return JsonResponse({
                'mensagem': u'Error de validação',
                'validation_errors': validation_errors,
                'error': 'VALIDATION_ERROR'}, status=400)

    def form_valid(self, form):
        form.save()
        return JsonResponse(form.instance.dictify())


# @require_http_methods(["POST"])
def login_view(request):
    try:
        json_data = json.loads(request.body)
    except ValueError:
        return HttpResponseBadRequest()
    user = authenticate(
        username=json_data['email'],
        password=json_data['password'])
    if user is not None and user.is_active:
        login(request, user)
        return JsonResponse(user.dictify())
    return JsonResponse(
        {"mensagem": u"Usuário e/ou senha inválidos",
         "error": "WRONG_CREDENTIALS"}, status=401)
