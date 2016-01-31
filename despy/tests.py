# -*- coding: utf-8 -*-
import json
from datetime import timedelta

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from .models import User

TEST_USER = {
    "name": u"João da Silva",
    "email": "joao@silva.org",
    "password": "hunter2",
    "phones": [
        {
            "number": "+49348503945",
            "ddd": "21"
        }
    ]
}

ANOTHER_TEST_USER = {
    "name": "Joaquim Emanuel",
    "email": "Joaquim@example.com",
    "password": "J0!!!LaDoPo74#",
    "phones": [
        {
            "number": "+93790843443",
            "ddd": "22"
        },
        {
            "number": "+49342475092",
            "ddd": "22"
        }
    ]
}


class DespyTestCase(TestCase):

    def create_user(self, user_test_data):
            resp = self.client.post(
                reverse('create-user'),
                json.dumps(user_test_data),
                content_type="application/json")
            self.assertEqual(resp.status_code, 200)
            resp_data = json.loads(resp.content)
            self.assertLooksLikeUser(resp_data, user_test_data=user_test_data)
            return User.objects.get(id=resp_data['id'])

    def assertLooksLikeUser(self, resp, user_test_data=TEST_USER):
        resp_data = self._get_json(resp)
        for item in ['name', 'email']:
            self.assertEqual(resp_data[item], user_test_data[item])
        self.assertSequenceEqual(
            resp_data.keys(),
            ['name', 'created', 'phones', 'modified', 'email', 'token', 'last_login', 'id'])

    def assertResponseError(self, resp, error_type):
        resp_data = self._get_json(resp)
        self.assertEqual(resp_data['error'], error_type)

    def _get_json(self, resp):
        if isinstance(resp, dict):  # good enough for this use case
            return resp
        return json.loads(resp.content)


class UsersTestCase(DespyTestCase):

    def setUp(self):
        self.users = [
            self.create_user(TEST_USER),
            self.create_user(ANOTHER_TEST_USER)]
        self.username = TEST_USER['email']
        self.password = TEST_USER['password']
        self.endpoint = self.users[0].get_absolute_url()
        self.token = str(self.users[0].token)


class UserViewTestCase(UsersTestCase):

    def test_success(self):
        self.client.login(username=self.username, password=self.password)
        resp = self.client.get(self.endpoint,
                               HTTP_CONCRETESOLUTIONS_AUTH_TOKEN=self.token)
        self.assertEqual(resp.status_code, 200)
        self.assertLooksLikeUser(resp)

    def test_expired_login(self):
        the_past = timezone.now() - timedelta(minutes=30)
        with freeze_time(the_past):
            self.client.login(username=self.username, password=self.password)
        resp = self.client.get(self.endpoint,
                               HTTP_CONCRETESOLUTIONS_AUTH_TOKEN=self.token)
        self.assertEqual(resp.status_code, 403)
        self.assertResponseError(resp, 'SESSION_EXPIRED')

    def test_invalid_token(self):
        self.client.login(username=self.username, password=self.password)
        resp = self.client.get(self.endpoint,
                               HTTP_CONCRETESOLUTIONS_AUTH_TOKEN='my invalid token')
        self.assertEqual(resp.status_code, 403)
        self.assertResponseError(resp, 'INVALID_TOKEN')

    def test_no_token(self):
        self.client.login(username=self.username, password=self.password)
        resp = self.client.get(self.endpoint)
        self.assertEqual(resp.status_code, 403)
        self.assertResponseError(resp, 'NO_TOKEN')


class LoginTestCase(UsersTestCase):

    def test_success(self):
        resp = self.client.post(reverse('login'),
                                json.dumps(dict(email=self.username, password=self.password)),
                                content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        resp_data = json.loads(resp.content)
        self.assertLooksLikeUser(resp_data)

    def test_wrong_credentials(self):
        resp = self.client.post(reverse('login'),
                                json.dumps(dict(email=self.username, password='wrong pwd')),
                                content_type="application/json")
        self.assertEqual(resp.status_code, 401)
        self.assertResponseError(resp, 'WRONG_CREDENTIALS')


class UserCreateTestCase(DespyTestCase):

    def test_allowed_http_methods(self):
        resp = self.client.get(reverse('create-user'))
        self.assertEqual(resp.status_code, 405)
        self.assertEqual(resp.get('Allow'), 'POST')

    def test_success(self):
        resp = self.client.post(
            reverse('create-user'),
            json.dumps(TEST_USER),
            content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        resp_data = json.loads(resp.content)
        self.assertLooksLikeUser(resp_data)

    def test_validation_error(self):
        data = {
            "email": "fernando@example.com",
            "password": "FerFuFala4862",
            "phones": [
                {
                    "number": "XXX",
                    "ddd": "21X"}]}
        resp = self.client.post(reverse('create-user'),
                                json.dumps(data),
                                content_type="application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertResponseError(resp, 'VALIDATION_ERROR')

    def test_email_taken(self):
        self.create_user(TEST_USER)
        resp = self.client.post(
            reverse('create-user'),
            json.dumps(TEST_USER),
            content_type="application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertResponseError(resp, 'EMAIL_TAKEN')
