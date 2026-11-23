from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from django import forms
from .forms import ClienteForm

from django.urls import reverse_lazy
from django.views.generic import FormView
from .models import Funcionario


from .mixins import PermissaoComRedirecionamentoMixin


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            endereco = self.instance.endereco

            self.fields['rua'].initial = endereco.rua
            self.fields['numero'].initial = endereco.numero
            self.fields['bairro'].initial = endereco.bairro
            self.fields['cidade'].initial = endereco.cidade

class FuncionarioEditForm(FuncionarioFormFront):
    password1 = forms.CharField(
        label="Nova senha (deixe em branco para manter a atual)",
        widget=forms.PasswordInput,
        required=False
    )

    password2 = forms.CharField(
        label="Confirme a nova senha",
        widget=forms.PasswordInput,
        required=False
    )

    grupo = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Grupo de acesso",
        required=False
    )

    def clean_username(self):
        username = self.cleaned_data["username"]

        usuarios = User.objects.filter(username=username)

        if self.instance.usuario_id:
            usuarios = usuarios.exclude(pk=self.instance.usuario_id)

        if usuarios.exists():
            raise forms.ValidationError("Este nome de usuário já está em uso.")

        return username


class FuncionarioCreateView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.add_funcionario'
    def get(self, request):
        form = FuncionarioFormFront()
        return render(request, "cadastro_funcionario.html", {"form": form})

    def post(self, request):
        form = FuncionarioFormFront(request.POST)

        if form.is_valid():
            dados = form.cleaned_data

            novo_endereco = Endereco.objects.create(
                rua=dados["rua"],
                numero=dados["numero"],
                bairro=dados["bairro"],
                cidade=dados["cidade"]
            )

            usuario = User.objects.create_user(
                username=dados["username"],
                email=form.instance.email,
                password=dados["password1"]
            )

            usuario.groups.set([dados["grupo"]])

            funcionario = form.save(commit=False)
            funcionario.endereco = novo_endereco
            funcionario.usuario = usuario
            funcionario.save()

            messages.success(request, "Funcionário cadastrado com sucesso!")
            return redirect("index")

        return render(request, "cadastro_funcionario.html", {"form": form})



class FuncionarioEditView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.change_funcionario'

    def get(self, request, pk):
        funcionario = get_object_or_404(Funcionario, pk=pk)
        form = FuncionarioEditForm(instance=funcionario)

        if funcionario.usuario:
            form.fields["username"].initial = funcionario.usuario.username
            form.fields["grupo"].initial = funcionario.usuario.groups.first()

        return render(request, "editar_funcionario.html", {
            "form": form,
            "funcionario": funcionario
        })

    def post(self, request, pk):
        funcionario = get_object_or_404(Funcionario, pk=pk)
        form = FuncionarioEditForm(request.POST, instance=funcionario)

        if form.is_valid():
            with transaction.atomic():
                dados = form.cleaned_data

                endereco = funcionario.endereco
                endereco.rua = dados["rua"]
                endereco.numero = dados["numero"]
                endereco.bairro = dados["bairro"]
                endereco.cidade = dados["cidade"]
                endereco.save()

                funcionario = form.save(commit=False)
                funcionario.endereco = endereco
                funcionario.save()

                usuario = funcionario.usuario

                if usuario:
                    usuario.username = dados["username"]
                    usuario.email = funcionario.email

                    if dados["password1"]:
                        usuario.set_password(dados["password1"])

                    usuario.save()

                    if dados["grupo"]:
                        usuario.groups.set([dados["grupo"]])

            messages.success(request, "Funcionário atualizado com sucesso!")
            return redirect("funcionario")

        return render(request, "editar_funcionario.html", {
            "form": form,
            "funcionario": funcionario
        })


class FuncionarioDeleteView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.delete_funcionario'

    def post(self, request, pk):
        funcionario = get_object_or_404(Funcionario, pk=pk)

        # Evita excluir funcionários que possuem atendimentos.
        if Atendimento.objects.filter(funcionario=funcionario).exists():
            messages.error(
                request,
                "Não é possível excluir este funcionário, pois existem atendimentos vinculados a ele."
            )
            return redirect("funcionario")

        with transaction.atomic():
            usuario = funcionario.usuario
            funcionario.delete()

            if usuario:
                usuario.delete()

        messages.success(request, "Funcionário excluído com sucesso!")
        return redirect("funcionario")
    
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

class FuncionarioView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.view_funcionario'

    def get(self, request, *args, **kwargs):
        funcionarios = Funcionario.objects.all()
        return render(request, "funcionario.html", {"funcionarios": funcionarios})
    
    def post(self, request):
        pass



class ClienteCreateView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.add_cliente'

    def get(self, request):
        form = ClienteForm()
        return render(request, "cadastro_cliente.html", {"form": form})

    def post(self, request):
        form = ClienteForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                dados = form.cleaned_data

                endereco = Endereco.objects.create(
                    rua=dados['rua'],
                    numero=dados['numero'],
                    bairro=dados['bairro'],
                    cidade=dados['cidade']
                )

                cliente = form.save(commit=False)
                cliente.endereco = endereco
                cliente.save()

            messages.success(request, "Cliente cadastrado com sucesso!")
            return redirect("cliente")

        return render(request, "cadastro_cliente.html", {"form": form})


class ClienteEditView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.change_cliente'

    def get(self, request, pk):
        cliente = get_object_or_404(Cliente, pk=pk)
        form = ClienteForm(instance=cliente)

        return render(request, "editar_cliente.html", {
            "form": form,
            "cliente": cliente
        })

    def post(self, request, pk):
        cliente = get_object_or_404(Cliente, pk=pk)
        form = ClienteForm(request.POST, instance=cliente)

        if form.is_valid():
            with transaction.atomic():
                dados = form.cleaned_data

                endereco = Endereco.objects.create(
                    rua=dados['rua'],
                    numero=dados['numero'],
                    bairro=dados['bairro'],
                    cidade=dados['cidade']
                )

                cliente = form.save(commit=False)
                cliente.endereco = endereco
                cliente.save()

            messages.success(request, "Cliente atualizado com sucesso!")
            return redirect("cliente")

        return render(request, "editar_cliente.html", {
            "form": form,
            "cliente": cliente
        })


class ClienteDeleteView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.delete_cliente'

    def get(self, request, pk):
        cliente = get_object_or_404(Cliente, pk=pk)

        return render(request, "excluir_cliente.html", {
            "cliente": cliente
        })

    def post(self, request, pk):
        cliente = get_object_or_404(Cliente, pk=pk)

        cliente.delete()

        messages.success(request, "Cliente excluído com sucesso!")
        return redirect("cliente")
