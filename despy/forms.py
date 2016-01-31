from django import forms

from .models import User, Phone


class UserCreateForm(forms.ModelForm):

    name = forms.CharField(max_length=100)
    email = forms.CharField(max_length=100)
    password = forms.CharField(max_length=100)

    def __init__(self, input, *args, **kwargs):
        super(UserCreateForm, self).__init__(input, *args, **kwargs)

        # create fields for extra phone numbers
        self._phone_numbers_num = sum(1 for i in input if i.startswith(u'phone_number_'))
        for i in range(self._phone_numbers_num):
            for field_name in ['ddd', 'number']:
                model_field = Phone._meta.get_field(field_name)
                form_field = model_field.formfield()
                self.fields[u'phone_{}_{}'.format(field_name, i)] = form_field

    @staticmethod
    def flatten_phones(input):
        for i, entry in enumerate(input.pop('phones', [])):
            input[u'phone_ddd_{}'.format(i)] = entry.get('ddd', '')
            input[u'phone_number_{}'.format(i)] = entry.get('number', '')

    @property
    def phones(self):
        return [
            dict(
                number=self.cleaned_data['phone_number_{}'.format(i)],
                ddd=self.cleaned_data['phone_ddd_{}'.format(i)])
            for i in range(self._phone_numbers_num)]

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError('Email already exists', code='not_unique')
        return email

    def save(self, commit=True):
        instance = super(UserCreateForm, self).save(commit=False)
        if commit:
            instance.first_name, instance.last_name = self.cleaned_data['name'].split(None, 1)
            instance.username = self.cleaned_data['email']
            instance.set_password(self.cleaned_data['password'])
            instance.save()
            for phone in self.phones:
                instance.phones.create(**phone)
        return instance

    class Meta:
        model = User

        # TODO: figure out why we need this
        fields = ['password']
