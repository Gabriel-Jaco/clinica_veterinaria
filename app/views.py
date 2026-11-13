from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .mixins import GrupoRequeridoMixin
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django import forms
from django.urls import reverse_lazy
from django.views.generic import FormView
from .models import Funcionario

User = get_user_model()

class FuncionarioFormFront(forms.ModelForm):
    # Campos diretos para preencher o endereço na hora
    rua = forms.CharField(max_length=100, label="Nome da rua")
    numero = forms.IntegerField(label="Número do endereço")
    bairro = forms.CharField(max_length=100, label="Bairro do endereço")
    cidade = forms.ModelChoiceField(queryset=Cidade.objects.all(), label="Cidade")

    # Campos de autenticação do usuário
    username = forms.CharField(max_length=150, label="Nome de usuário")
    password1 = forms.CharField(label="Senha", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirme a senha", widget=forms.PasswordInput)
    grupo = forms.ModelChoiceField(queryset=Group.objects.all(), label="Grupo de acesso")

    class Meta:
        model = Funcionario
        # Excluímos 'usuario' e 'endereco' porque vamos criá-los manualmente no post
        exclude = ("usuario", "endereco")

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "As senhas não coincidem.")
        return cleaned_data

class FuncionarioCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = FuncionarioFormFront()
        return render(request, "cadastro_funcionario.html", {"form": form})

    def post(self, request):
        form = FuncionarioFormFront(request.POST)
        if form.is_valid():
            dados = form.cleaned_data
            
            # 1. Cria o Endereço novo no banco automaticamente com os dados preenchidos
            novo_endereco = Endereco.objects.create(
                rua=dados["rua"],
                numero=dados["numero"],
                bairro=dados["bairro"],
                cidade=dados["cidade"]
            )

            # 2. Cria o usuário do sistema (login)
            usuario = User.objects.create_user(
                username=dados["username"],
                email=form.instance.email,
                password=dados["password1"]
            )
            usuario.groups.set([dados["grupo"]])

            # 3. Salva o funcionário vinculando o novo endereço e o usuário criado
            funcionario = form.save(commit=False)
            funcionario.endereco = novo_endereco
            funcionario.usuario = usuario
            funcionario.save()

            messages.success(request, "Funcionário cadastrado com sucesso!")
            return redirect("index")
        
        return render(request, "cadastro_funcionario.html", {"form": form})
    
class IndexView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, "index.html")

    def post(self, request):
        pass


class ClienteView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        clientes = Cliente.objects.all()
        return render(request, "cliente.html", {"clientes": clientes})

    def post(self, request):
        pass

class FuncionarioView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        funcionarios = Funcionario.objects.all()
        return render(request, "funcionario.html", {"funcionarios": funcionarios})

    def post(self, request):
        pass

    

