from django.contrib import admin
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import *


User = get_user_model()


class FuncionarioForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        label="Nome de usuário"
    )

    password1 = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput,
        required=False
    )

    password2 = forms.CharField(
        label="Confirme a senha",
        widget=forms.PasswordInput,
        required=False
    )

    grupo = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Grupo de acesso"
    )

    class Meta:
        model = Funcionario
        exclude = ("usuario",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        funcionario = self.instance

        if funcionario.pk and funcionario.usuario:
            self.fields["username"].initial = funcionario.usuario.username
            self.fields["grupo"].initial = funcionario.usuario.groups.first()

    def clean(self):
        cleaned_data = super().clean()

        username = cleaned_data.get("username")
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        usuario_atual = self.instance.usuario

        if username:
            usuarios = User.objects.filter(username=username)

            if usuario_atual:
                usuarios = usuarios.exclude(pk=usuario_atual.pk)

            if usuarios.exists():
                self.add_error("username", "Este nome de usuário já está em uso.")

        if not self.instance.pk and not password1:
            self.add_error("password1", "Informe uma senha para o novo usuário.")

        if password1 or password2:
            if password1 != password2:
                self.add_error("password2", "As senhas não coincidem.")
            elif password1:
                try:
                    validate_password(password1, user=usuario_atual)
                except ValidationError as erro:
                    self.add_error("password1", erro)

        return cleaned_data


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    form = FuncionarioForm

    def save_model(self, request, obj, form, change):
        dados = form.cleaned_data

        if obj.usuario:
            usuario = obj.usuario
            usuario.username = dados["username"]
            usuario.email = obj.email

            if dados["password1"]:
                usuario.set_password(dados["password1"])

            usuario.save()

        else:
            usuario = User.objects.create_user(
                username=dados["username"],
                email=obj.email,
                password=dados["password1"]
            )

        obj.usuario = usuario

        super().save_model(request, obj, form, change)

        usuario.groups.set([dados["grupo"]])


admin.site.register(Cidade)
admin.site.register(Endereco)
admin.site.register(Cliente)
admin.site.register(Especie)
admin.site.register(Raca)
admin.site.register(Animal)
admin.site.register(Fornecedor)
admin.site.register(Lote)
admin.site.register(Produto)
admin.site.register(Servico)
admin.site.register(Atendimento)
admin.site.register(Produto_atendimento)
admin.site.register(Fatura)
