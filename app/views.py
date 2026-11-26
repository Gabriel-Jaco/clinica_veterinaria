from decimal import Decimal, ROUND_HALF_UP
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum, ProtectedError, Q, Value, DecimalField
from django.db.models.functions import Coalesce
from django.urls import reverse

from django import forms

from .models import *
from .forms import *
from .mixins import PermissaoComRedirecionamentoMixin


def atualizar_estoque(produto_id):
    estoque_total = Lote.objects.filter(
        produto_id=produto_id
    ).aggregate(
        total=Sum('quantidade')
    )['total'] or 0.0

    Produto.objects.filter(pk=produto_id).update(
        estoque=estoque_total
    )


def registrar_produtos_atendimento(atendimento, formset):
    """
    Deve ser chamada dentro de transaction.atomic().
    Levanta ValidationError se faltar estoque no lote ou se a fatura já estiver paga;
    quem chama deve capturar e exibir a mensagem.
    """
    if atendimento.fatura_id and atendimento.fatura.status_pagamento == StatusPagamento.PAGO:
        raise ValidationError("Atendimento de fatura já paga não pode ser alterado.")

    itens = formset.save(commit=False)
    produtos_alterados = set()

    # Itens removidos: devolve a quantidade ao lote e apaga
    for item in formset.deleted_objects:
        if item.pk:
            lote = Lote.objects.select_for_update().get(pk=item.lote_id)
            lote.quantidade += item.quantidade
            lote.save(update_fields=["quantidade"])
            produtos_alterados.add(lote.produto_id)
        item.delete()

    for item in itens:
        # Estado anterior do item (None se for novo)
        anterior = None
        if item.pk:
            anterior = Produto_atendimento.objects.select_for_update().get(pk=item.pk)

        lote = Lote.objects.select_for_update().get(pk=item.lote_id)

        if anterior and anterior.lote_id == lote.pk:
            # Mesmo lote: baixa apenas a diferença
            diferenca = item.quantidade - anterior.quantidade
        else:
            # Item novo ou lote trocado: devolve o lote antigo e baixa a quantidade inteira
            if anterior:
                lote_antigo = Lote.objects.select_for_update().get(pk=anterior.lote_id)
                lote_antigo.quantidade += anterior.quantidade
                lote_antigo.save(update_fields=["quantidade"])
                produtos_alterados.add(lote_antigo.produto_id)
            diferenca = item.quantidade

        if diferenca > lote.quantidade:
            raise ValidationError(
                f"Estoque insuficiente no lote {lote.numero}: "
                f"disponível {lote.quantidade}, solicitado {diferenca}."
            )

        lote.quantidade -= diferenca
        lote.save(update_fields=["quantidade"])

        item.atendimento = atendimento
        item.produto = lote.produto

        # Preço é "foto" do momento: só define para item novo ou se o produto mudou
        if not anterior or anterior.produto_id != lote.produto_id:
            item.preco_custo = lote.produto.preco_custo
            item.preco_venda = lote.produto.preco_venda

        # quantidade é float e preco_venda é Decimal: precisa converter
        item.subtotal = (
            Decimal(str(item.quantidade)) * item.preco_venda
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        item.save()

        produtos_alterados.add(lote.produto_id)

    for produto_id in produtos_alterados:
        atualizar_estoque(produto_id)

    atendimento.recalcular_totais()


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

    def clean_username(self):
        username = self.cleaned_data["username"]

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nome de usuário já está em uso.")

        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "As senhas não coincidem.")
        elif password1:
            try:
                validate_password(password1)
            except ValidationError as e:
                self.add_error("password1", e)
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

            # atomic: se algo falhar, não sobra endereço ou usuário órfão
            with transaction.atomic():
                novo_endereco = Endereco.objects.create(
                    rua=dados["rua"],
                    numero=dados["numero"],
                    bairro=dados["bairro"],
                    cidade=dados["cidade"]
                )

                usuario = User.objects.create_user(
                    username=dados["username"],
                    email=dados["email"],
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

    def get(self, request, pk):
        funcionario = get_object_or_404(Funcionario, pk=pk)

        return render(request, "excluir_funcionario.html", {
            "funcionario": funcionario
        })

    def post(self, request, pk):
        funcionario = get_object_or_404(Funcionario, pk=pk)

        if (
            Atendimento.objects.filter(funcionario=funcionario).exists()
            or Pagamento.objects.filter(funcionario=funcionario).exists()
        ):
            messages.error(
                request,
                "Não é possível excluir este funcionário, pois existem atendimentos ou pagamentos vinculados a ele."
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
        pesquisa = request.GET.get('q', '').strip()

        atendimentos_base = Atendimento.objects.filter(
            status=Atendimento.Status.ABERTO
        ).select_related(
            'animal',
            'animal__tutor',
            'servico',
            'funcionario'
        ).order_by('-data', '-pk')

        atendimentos_abertos_total = atendimentos_base.count()

        atendimentos = atendimentos_base

        if pesquisa:
            atendimentos = atendimentos.filter(
                Q(animal__nome__icontains=pesquisa) |
                Q(animal__sobrenome__icontains=pesquisa) |
                Q(animal__tutor__nome__icontains=pesquisa) |
                Q(animal__tutor__sobrenome__icontains=pesquisa) |
                Q(funcionario__nome__icontains=pesquisa) |
                Q(funcionario__sobrenome__icontains=pesquisa) |
                Q(servico__nome__icontains=pesquisa)
            )

        faturas = Fatura.objects.annotate(
            pago_calc=Coalesce(
                Sum(
                    'pagamentos__valor',
                    filter=Q(pagamentos__estornado=False)
                ),
                Value(Decimal('0.00')),
                output_field=DecimalField(
                    max_digits=10,
                    decimal_places=2
                )
            )
        ).values_list('valor_final', 'pago_calc')

        faturas_pendentes = 0
        saldo_total = Decimal('0.00')

        for valor_final, pago in faturas:
            saldo = valor_final - pago

            if saldo > 0:
                faturas_pendentes += 1
                saldo_total += saldo

        funcionario = Funcionario.objects.filter(
            usuario=request.user
        ).first()

        if funcionario:
            nome_usuario = f"{funcionario.nome} {funcionario.sobrenome}"
        else:
            nome_usuario = request.user.get_full_name() or request.user.username

        return render(request, 'index.html', {
            'atendimentos': atendimentos,
            'atendimentos_abertos_total': atendimentos_abertos_total,
            'faturas_pendentes': faturas_pendentes,
            'saldo_total': saldo_total,
            'pesquisa': pesquisa,
            'nome_usuario': nome_usuario
        })


class ClienteView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        pesquisa = request.GET.get('q', '').strip()

        clientes = Cliente.objects.select_related(
            'endereco__cidade'
        ).all().order_by('nome', 'sobrenome')

        if pesquisa:
            clientes = clientes.filter(
                Q(nome__icontains=pesquisa) |
                Q(sobrenome__icontains=pesquisa) |
                Q(cpf__icontains=pesquisa) |
                Q(contato__icontains=pesquisa)
            )

        return render(request, "cliente.html", {
            "clientes": clientes,
            "pesquisa": pesquisa
        })
class FuncionarioView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.view_funcionario'

    def get(self, request, *args, **kwargs):
        funcionarios = Funcionario.objects.all()
        return render(request, "funcionario.html", {"funcionarios": funcionarios})



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

                # Atualiza o endereço existente (antes criava um novo a cada edição)
                endereco = cliente.endereco
                endereco.rua = dados['rua']
                endereco.numero = dados['numero']
                endereco.bairro = dados['bairro']
                endereco.cidade = dados['cidade']
                endereco.save()

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

        try:
            cliente.delete()
        except ProtectedError:
            messages.error(
                request,
                "Não é possível excluir este cliente, pois existem animais ou faturas vinculados a ele."
            )
            return redirect("cliente")

        messages.success(request, "Cliente excluído com sucesso!")
        return redirect("cliente")


class AnimalView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.view_animal'

    def get(self, request):
        pesquisa = request.GET.get('q', '').strip()

        animais = Animal.objects.select_related(
            'raca__especie',
            'tutor'
        ).all().order_by('nome', 'sobrenome')

        if pesquisa:
            animais = animais.filter(
                Q(nome__icontains=pesquisa) |
                Q(sobrenome__icontains=pesquisa) |
                Q(rg__icontains=pesquisa) |
                Q(raca__nome__icontains=pesquisa) |
                Q(raca__especie__nome__icontains=pesquisa) |
                Q(tutor__nome__icontains=pesquisa) |
                Q(tutor__sobrenome__icontains=pesquisa)
            )

        return render(request, 'animal.html', {
            'animais': animais,
            'pesquisa': pesquisa
        })


class AnimalCreateView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.add_animal'

    def get(self, request):
        form = AnimalForm()
        return render(request, 'cadastro_animal.html', {
            'form': form
        })

    def post(self, request):
        form = AnimalForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                form.save()

            messages.success(request, 'Animal cadastrado com sucesso!')
            return redirect('animal')

        return render(request, 'cadastro_animal.html', {
            'form': form
        })

class AnimalEditView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.change_animal'

    def get(self, request, pk):
        animal = get_object_or_404(Animal, pk=pk)
        form = AnimalForm(instance=animal)

        return render(request, 'editar_animal.html', {
            'form': form,
            'animal': animal
        })

    def post(self, request, pk):
        animal = get_object_or_404(Animal, pk=pk)
        form = AnimalForm(request.POST, instance=animal)

        if form.is_valid():
            with transaction.atomic():
                form.save()

            messages.success(request, 'Animal atualizado com sucesso!')
            return redirect('animal')

        return render(request, 'editar_animal.html', {
            'form': form,
            'animal': animal
        })

class AnimalDeleteView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.delete_animal'

    def get(self, request, pk):
        animal = get_object_or_404(Animal, pk=pk)

        return render(request, 'excluir_animal.html', {'animal': animal})

    def post(self, request, pk):
        animal = get_object_or_404(Animal, pk=pk)

        try:
            animal.delete()
        except ProtectedError:
            messages.error(
                request,
                "Não é possível excluir este animal, pois existem atendimentos vinculados a ele."
            )
            return redirect('animal')

        messages.success(request, "Animal excluído com sucesso!")

        return redirect('animal')


class RacaCreateView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.add_raca'

    def get(self, request):
        form = RacaForm()

        return render(request, 'cadastro_raca.html', {
            'form': form
        })

    def post(self, request):
        form = RacaForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                form.save()

            messages.success(request, "Raça cadastrada com sucesso!")
            return redirect('animal')

        return render(request, 'cadastro_raca.html', {
            'form': form
        })



class RacaDeleteView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.delete_raca'

    def get(self, request, pk):
        raca = get_object_or_404(Raca, pk=pk)

        return render(request, 'excluir_raca.html', {
            'raca': raca
        })

    def post(self, request, pk):
        raca = get_object_or_404(Raca, pk=pk)

        if Animal.objects.filter(raca=raca).exists():
            messages.error(
                request,
                "Não é possível excluir esta raça, pois existem animais vinculados a ela."
            )
            return redirect('animal')

        raca.delete()

        messages.success(request, "Raça excluída com sucesso!")

        return redirect('animal')

class RacaView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.view_raca'

    def get(self, request):
        racas = Raca.objects.select_related('especie').all()

        return render(request, 'raca.html', {
            'racas': racas
        })


class FornecedorView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.view_fornecedor'

    def get(self, request):
        fornecedores = Fornecedor.objects.all()

        return render(request, 'fornecedor.html', {
            'fornecedores': fornecedores
        })


class FornecedorCreateView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.add_fornecedor'

    def get(self, request):
        form = FornecedorForm()

        return render(request, 'cadastro_fornecedor.html', {
            'form': form
        })

    def post(self, request):
        form = FornecedorForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                form.save()

            messages.success(request, "Fornecedor cadastrado com sucesso!")
            return redirect('fornecedor')

        return render(request, 'cadastro_fornecedor.html', {
            'form': form
        })


class FornecedorEditView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.change_fornecedor'

    def get(self, request, pk):
        fornecedor = get_object_or_404(Fornecedor, pk=pk)
        form = FornecedorForm(instance=fornecedor)

        return render(request, 'editar_fornecedor.html', {
            'form': form,
            'fornecedor': fornecedor
        })

    def post(self, request, pk):
        fornecedor = get_object_or_404(Fornecedor, pk=pk)
        form = FornecedorForm(request.POST, instance=fornecedor)

        if form.is_valid():
            with transaction.atomic():
                form.save()

            messages.success(request, "Fornecedor atualizado com sucesso!")
            return redirect('fornecedor')

        return render(request, 'editar_fornecedor.html', {
            'form': form,
            'fornecedor': fornecedor
        })


class FornecedorDeleteView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.delete_fornecedor'

    def get(self, request, pk):
        fornecedor = get_object_or_404(Fornecedor, pk=pk)

        return render(request, 'excluir_fornecedor.html', {
            'fornecedor': fornecedor
        })

    def post(self, request, pk):
        fornecedor = get_object_or_404(Fornecedor, pk=pk)

        # Lote.fornecedor é CASCADE: sem esta checagem, apagar o fornecedor apagaria os lotes
        if Lote.objects.filter(fornecedor=fornecedor).exists():
            messages.error(
                request,
                "Não é possível excluir este fornecedor, "
                "pois existem lotes vinculados a ele."
            )
            return redirect('fornecedor')

        fornecedor.delete()

        messages.success(request, "Fornecedor excluído com sucesso!")
        return redirect('fornecedor')


class ProdutoView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.view_produto'

    def get(self, request):
        produtos = Produto.objects.all().order_by('nome')

        return render(request, 'produto.html', {
            'produtos': produtos
        })
class ProdutoCreateView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.add_produto'

    def get(self, request):
        form = ProdutoForm()

        return render(request, 'cadastro_produto.html', {
            'form': form
        })

    def post(self, request):
        form = ProdutoForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                produto = form.save(commit=False)
                produto.estoque = 0
                produto.save()

            messages.success(
                request,
                "Produto cadastrado com sucesso!"
            )

            return redirect('produto')

        return render(request, 'cadastro_produto.html', {
            'form': form
        })
class ProdutoDetailView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.view_produto'

    def get(self, request, pk):
        produto = get_object_or_404(Produto, pk=pk)

        lotes = Lote.objects.filter(
            produto=produto
        ).select_related('fornecedor').order_by('data_validade')

        return render(request, 'visualizar_produto.html', {
            'produto': produto,
            'lotes': lotes
        })
class ProdutoEditView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.change_produto'

    def get(self, request, pk):
        produto = get_object_or_404(Produto, pk=pk)
        form = ProdutoForm(instance=produto)

        return render(request, 'editar_produto.html', {
            'form': form,
            'produto': produto
        })

    def post(self, request, pk):
        produto = get_object_or_404(Produto, pk=pk)
        form = ProdutoForm(request.POST, instance=produto)

        if form.is_valid():
            with transaction.atomic():
                form.save()

            messages.success(
                request,
                "Produto atualizado com sucesso!"
            )

            return redirect('produto')

        return render(request, 'editar_produto.html', {
            'form': form,
            'produto': produto
        })
class ProdutoDeleteView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.delete_produto'

    def get(self, request, pk):
        produto = get_object_or_404(Produto, pk=pk)

        return render(request, 'excluir_produto.html', {
            'produto': produto
        })

    def post(self, request, pk):
        produto = get_object_or_404(Produto, pk=pk)

        if Lote.objects.filter(produto=produto).exists():
            messages.error(
                request,
                "Não é possível excluir este produto, "
                "pois existem lotes vinculados a ele."
            )
            return redirect('produto')

        if Produto_atendimento.objects.filter(produto=produto).exists():
            messages.error(
                request,
                "Não é possível excluir este produto, "
                "pois existem registros de atendimento vinculados a ele."
            )
            return redirect('produto')

        with transaction.atomic():
            produto.delete()

        messages.success(
            request,
            "Produto excluído com sucesso!"
        )

        return redirect('produto')
class LoteView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.view_lote'

    def get(self, request):
        lotes = Lote.objects.select_related(
            'produto',
            'fornecedor'
        ).all().order_by('data_validade')

        produto_id = request.GET.get('produto')

        if produto_id:
            lotes = lotes.filter(produto_id=produto_id)

        return render(request, 'lote.html', {
            'lotes': lotes,
            'produto_id': produto_id
        })
class LoteCreateView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.add_lote'

    def get(self, request):
        produto_id = request.GET.get('produto')

        form = LoteForm(initial={
            'produto': produto_id
        })

        return render(request, 'cadastro_lote.html', {
            'form': form
        })

    def post(self, request):
        form = LoteForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                lote = form.save()
                atualizar_estoque(lote.produto_id)

            messages.success(
                request,
                "Lote cadastrado com sucesso!"
            )

            return redirect('lote')

        return render(request, 'cadastro_lote.html', {
            'form': form
        })
class LoteDetailView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.view_lote'

    def get(self, request, pk):
        lote = get_object_or_404(
            Lote.objects.select_related(
                'produto',
                'fornecedor'
            ),
            pk=pk
        )

        return render(request, 'visualizar_lote.html', {
            'lote': lote
        })
class LoteEditView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.change_lote'

    def get(self, request, pk):
        lote = get_object_or_404(Lote, pk=pk)
        form = LoteForm(instance=lote)

        return render(request, 'editar_lote.html', {
            'form': form,
            'lote': lote
        })

    def post(self, request, pk):
        lote = get_object_or_404(Lote, pk=pk)
        produto_antigo = lote.produto_id

        form = LoteForm(request.POST, instance=lote)

        if form.is_valid():
            # Lote já usado em atendimento não pode mudar de produto (corromperia o histórico)
            if (
                form.cleaned_data['produto'].pk != produto_antigo
                and Produto_atendimento.objects.filter(lote=lote).exists()
            ):
                form.add_error(
                    'produto',
                    "Este lote já foi utilizado em atendimentos e não pode mudar de produto."
                )
                return render(request, 'editar_lote.html', {
                    'form': form,
                    'lote': lote
                })

            with transaction.atomic():
                lote = form.save()

                atualizar_estoque(produto_antigo)
                atualizar_estoque(lote.produto_id)

            messages.success(
                request,
                "Lote atualizado com sucesso!"
            )

            return redirect('lote')

        return render(request, 'editar_lote.html', {
            'form': form,
            'lote': lote
        })
class LoteDeleteView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.delete_lote'

    def get(self, request, pk):
        lote = get_object_or_404(
            Lote.objects.select_related('produto'),
            pk=pk
        )

        return render(request, 'excluir_lote.html', {
            'lote': lote
        })

    def post(self, request, pk):
        lote = get_object_or_404(Lote, pk=pk)

        if Produto_atendimento.objects.filter(lote=lote).exists():
            messages.error(
                request,
                "Não é possível excluir este lote, "
                "pois ele já foi utilizado em um atendimento."
            )

            return redirect('lote')

        produto_id = lote.produto_id

        with transaction.atomic():
            lote.delete()
            atualizar_estoque(produto_id)

        messages.success(
            request,
            "Lote excluído com sucesso!"
        )

        return redirect('lote')

# ======================================================================
# COLE ESTE BLOCO NO FINAL DO views.py
# (todos os imports necessários já existem no topo do views.py corrigido)
# ======================================================================


def devolver_itens_ao_estoque(atendimento):
    """Devolve aos lotes tudo que o atendimento consumiu. Chamar dentro de transaction.atomic()."""
    produtos_alterados = set()

    for item in Produto_atendimento.objects.filter(atendimento=atendimento):
        lote = Lote.objects.select_for_update().get(pk=item.lote_id)
        lote.quantidade += item.quantidade
        lote.save(update_fields=["quantidade"])
        produtos_alterados.add(lote.produto_id)

    for produto_id in produtos_alterados:
        atualizar_estoque(produto_id)


def motivo_bloqueio_edicao(atendimento):
    """Retorna a mensagem de bloqueio, ou None se o atendimento pode ser alterado."""
    if atendimento.status == Atendimento.Status.CANCELADO:
        return "Atendimento cancelado não pode ser alterado."

    if atendimento.fatura_id:
        return "Atendimento já incluído em fatura não pode ser alterado."

    return None


def validar_atendimento(form, formset):
    """Valida form e formset juntos (para exibir todos os erros) e impede
    cancelar pelo select de status, já que o cancelamento precisa devolver o estoque."""
    form_ok = form.is_valid()

    if form_ok and form.cleaned_data["status"] == Atendimento.Status.CANCELADO:
        form.add_error("status", "Para cancelar, use a opção Cancelar atendimento.")
        form_ok = False

    formset_ok = formset.is_valid()

    return form_ok and formset_ok


class AtendimentoView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.view_atendimento'

    def get(self, request):
        pesquisa = request.GET.get('q', '').strip()
        status = request.GET.get('status', '')

        atendimentos = Atendimento.objects.select_related(
            'animal__tutor',
            'servico',
            'funcionario',
            'fatura'
        ).order_by('-data', '-pk')

        if pesquisa:
            atendimentos = atendimentos.filter(
                Q(animal__nome__icontains=pesquisa) |
                Q(animal__sobrenome__icontains=pesquisa) |
                Q(animal__tutor__nome__icontains=pesquisa) |
                Q(animal__tutor__sobrenome__icontains=pesquisa) |
                Q(servico__nome__icontains=pesquisa) |
                Q(funcionario__nome__icontains=pesquisa) |
                Q(funcionario__sobrenome__icontains=pesquisa) |
                Q(observacao__icontains=pesquisa)
            )

        if status:
            atendimentos = atendimentos.filter(status=status)

        return render(request, 'atendimento.html', {
            'atendimentos': atendimentos,
            'pesquisa': pesquisa,
            'status_selecionado': status,
            'status_opcoes': Atendimento.Status.choices
        })


class AtendimentoCreateView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.add_atendimento'

    def get(self, request):
        return render(request, 'cadastro_atendimento.html', {
            'form': AtendimentoForm(),
            'formset': ProdutoAtendimentoFormSet(instance=Atendimento())
        })

    def post(self, request):
        form = AtendimentoForm(request.POST)
        formset = ProdutoAtendimentoFormSet(request.POST, instance=form.instance)

        if validar_atendimento(form, formset):
            try:
                with transaction.atomic():
                    atendimento = form.save()
                    registrar_produtos_atendimento(atendimento, formset)
            except ValidationError as e:
                # o atomic desfaz tudo, inclusive o atendimento
                messages.error(request, " ".join(e.messages))
            else:
                messages.success(request, "Atendimento cadastrado com sucesso!")
                return redirect('atendimento_detalhe', pk=atendimento.pk)

        return render(request, 'cadastro_atendimento.html', {
            'form': form,
            'formset': formset
        })


class AtendimentoEditView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.change_atendimento'

    def get(self, request, pk):
        atendimento = get_object_or_404(Atendimento, pk=pk)

        motivo = motivo_bloqueio_edicao(atendimento)
        if motivo:
            messages.error(request, motivo)
            return redirect('atendimento_detalhe', pk=pk)

        return render(request, 'editar_atendimento.html', {
            'form': AtendimentoForm(instance=atendimento),
            'formset': ProdutoAtendimentoFormSet(instance=atendimento),
            'atendimento': atendimento
        })

    def post(self, request, pk):
        atendimento = get_object_or_404(Atendimento, pk=pk)

        # verifica antes de montar o form, que altera a instância
        motivo = motivo_bloqueio_edicao(atendimento)
        if motivo:
            messages.error(request, motivo)
            return redirect('atendimento_detalhe', pk=pk)

        form = AtendimentoForm(request.POST, instance=atendimento)
        formset = ProdutoAtendimentoFormSet(request.POST, instance=atendimento)

        if validar_atendimento(form, formset):
            try:
                with transaction.atomic():
                    atendimento = form.save()
                    registrar_produtos_atendimento(atendimento, formset)
            except ValidationError as e:
                messages.error(request, " ".join(e.messages))
            else:
                messages.success(request, "Atendimento atualizado com sucesso!")
                return redirect('atendimento_detalhe', pk=atendimento.pk)

        return render(request, 'editar_atendimento.html', {
            'form': form,
            'formset': formset,
            'atendimento': atendimento
        })


class AtendimentoDetailView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.view_atendimento'

    def get(self, request, pk):
        atendimento = get_object_or_404(
            Atendimento.objects.select_related(
                'animal__tutor',
                'servico',
                'funcionario',
                'fatura'
            ),
            pk=pk
        )

        itens = Produto_atendimento.objects.filter(
            atendimento=atendimento
        ).select_related('produto', 'lote')

        return render(request, 'visualizar_atendimento.html', {
            'atendimento': atendimento,
            'itens': itens,
            'pode_alterar': motivo_bloqueio_edicao(atendimento) is None
        })


class AtendimentoCancelView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.change_atendimento'

    def get(self, request, pk):
        atendimento = get_object_or_404(
            Atendimento.objects.select_related('animal__tutor', 'servico'),
            pk=pk
        )

        return render(request, 'cancelar_atendimento.html', {
            'atendimento': atendimento
        })

    def post(self, request, pk):
        with transaction.atomic():
            # trava o atendimento: dois cancelamentos simultâneos não devolvem o estoque duas vezes
            atendimento = get_object_or_404(
                Atendimento.objects.select_for_update(),
                pk=pk
            )

            if atendimento.status == Atendimento.Status.CANCELADO:
                messages.error(request, "Este atendimento já está cancelado.")
                return redirect('atendimento_detalhe', pk=pk)

            if atendimento.fatura_id:
                messages.error(
                    request,
                    "Não é possível cancelar um atendimento que já está em uma fatura."
                )
                return redirect('atendimento_detalhe', pk=pk)

            devolver_itens_ao_estoque(atendimento)

            atendimento.status = Atendimento.Status.CANCELADO
            atendimento.save(update_fields=["status"])

        messages.success(request, "Atendimento cancelado e materiais devolvidos ao estoque!")
        return redirect('atendimento_detalhe', pk=pk)


class ServicoView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.view_servico'

    def get(self, request):
        servicos = Servico.objects.all().order_by('nome')

        return render(request, 'servico.html', {
            'servicos': servicos
        })


class ServicoCreateView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.add_servico'

    def get(self, request):
        form = ServicoForm()

        return render(request, 'cadastro_servico.html', {
            'form': form
        })

    def post(self, request):
        form = ServicoForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                form.save()

            messages.success(request, "Serviço cadastrado com sucesso!")
            return redirect('servico')

        return render(request, 'cadastro_servico.html', {
            'form': form
        })


class ServicoEditView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.change_servico'

    def get(self, request, pk):
        servico = get_object_or_404(Servico, pk=pk)
        form = ServicoForm(instance=servico)

        return render(request, 'editar_servico.html', {
            'form': form,
            'servico': servico
        })

    def post(self, request, pk):
        servico = get_object_or_404(Servico, pk=pk)
        form = ServicoForm(request.POST, instance=servico)

        if form.is_valid():
            with transaction.atomic():
                form.save()

            messages.success(request, "Serviço atualizado com sucesso!")
            return redirect('servico')

        return render(request, 'editar_servico.html', {
            'form': form,
            'servico': servico
        })


class ServicoDeleteView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.delete_servico'

    def get(self, request, pk):
        servico = get_object_or_404(Servico, pk=pk)

        return render(request, 'excluir_servico.html', {
            'servico': servico
        })

    def post(self, request, pk):
        servico = get_object_or_404(Servico, pk=pk)

        if Atendimento.objects.filter(servico=servico).exists():
            messages.error(
                request,
                "Não é possível excluir este serviço, "
                "pois existem atendimentos vinculados a ele."
            )
            return redirect('servico')

        try:
            servico.delete()
        except ProtectedError:
            messages.error(
                request,
                "Não é possível excluir este serviço, "
                "pois existem registros vinculados a ele."
            )
            return redirect('servico')

        messages.success(request, "Serviço excluído com sucesso!")
        return redirect('servico')




def atendimentos_faturaveis(cliente):
    """Atendimentos concluídos do tutor que ainda não estão em nenhuma fatura."""
    return Atendimento.objects.filter(
        animal__tutor=cliente,
        status=Atendimento.Status.CONCLUIDO,
        fatura__isnull=True
    ).select_related('animal', 'servico').order_by('data', 'pk')


class FaturaView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.view_fatura'

    def get(self, request):
        pesquisa = request.GET.get('q', '').strip()
        status = request.GET.get('status', '')

        faturas = Fatura.objects.select_related(
            'cliente'
        ).annotate(
            pago_calc=Coalesce(
                Sum(
                    'pagamentos__valor',
                    filter=Q(pagamentos__estornado=False)
                ),
                Value(Decimal('0.00')),
                output_field=DecimalField(
                    max_digits=10,
                    decimal_places=2
                )
            )
        ).order_by('-data_emissao', '-pk')

        if pesquisa:
            faturas = faturas.filter(
                Q(cliente__nome__icontains=pesquisa) |
                Q(cliente__sobrenome__icontains=pesquisa) |
                Q(cliente__cpf__icontains=pesquisa)
            )

        lista = []

        for fatura in faturas:
            fatura.saldo_calc = fatura.valor_final - fatura.pago_calc

            if fatura.pago_calc <= 0:
                fatura.status_calc = StatusPagamento.PENDENTE
            elif fatura.saldo_calc <= 0:
                fatura.status_calc = StatusPagamento.PAGO
            else:
                fatura.status_calc = StatusPagamento.PARCIAL

            if not status or fatura.status_calc == status:
                lista.append(fatura)

        return render(request, 'fatura.html', {
            'faturas': lista,
            'pesquisa': pesquisa,
            'status_selecionado': status,
            'status_opcoes': StatusPagamento.choices
        })


class FaturaCreateView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.add_fatura'

    def get(self, request):
        cliente_id = request.GET.get('cliente')
        cliente = None
        atendimentos = []

        if cliente_id and cliente_id.isdigit():
            cliente = get_object_or_404(Cliente, pk=cliente_id)
            atendimentos = atendimentos_faturaveis(cliente)

        # só clientes que têm algo para faturar
        clientes = Cliente.objects.filter(
            animal__atendimento__status=Atendimento.Status.CONCLUIDO,
            animal__atendimento__fatura__isnull=True
        ).distinct().order_by('nome')

        return render(request, 'cadastro_fatura.html', {
            'clientes': clientes,
            'cliente': cliente,
            'atendimentos': atendimentos
        })

    def post(self, request):
        cliente_id = request.POST.get('cliente', '')

        if not cliente_id.isdigit():
            messages.error(request, "Selecione um cliente.")
            return redirect('fatura_cadastro')

        cliente = get_object_or_404(Cliente, pk=cliente_id)
        voltar = reverse('fatura_cadastro') + f'?cliente={cliente.pk}'

        ids = {int(i) for i in request.POST.getlist('atendimentos') if i.isdigit()}

        if not ids:
            messages.error(request, "Selecione pelo menos um atendimento.")
            return redirect(voltar)

        with transaction.atomic():
            # trava os atendimentos: duas emissões simultâneas não pegam o mesmo atendimento
            selecionados = list(
                Atendimento.objects.select_for_update(of=('self',)).filter(
                    pk__in=ids,
                    animal__tutor=cliente,
                    status=Atendimento.Status.CONCLUIDO,
                    fatura__isnull=True
                )
            )

            if len(selecionados) != len(ids):
                messages.error(
                    request,
                    "Algum atendimento selecionado não pode ser faturado "
                    "(já está em outra fatura, não está concluído ou é de outro tutor)."
                )
                return redirect(voltar)

            fatura = Fatura.objects.create(cliente=cliente, valor_final=Decimal('0.00'))
            Atendimento.objects.filter(
                pk__in=[a.pk for a in selecionados]
            ).update(fatura=fatura)
            fatura.recalcular_valor_final()

        messages.success(request, "Fatura emitida com sucesso!")
        return redirect('fatura_detalhe', pk=fatura.pk)


class FaturaDetailView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.view_fatura'

    def get(self, request, pk):
        fatura = get_object_or_404(Fatura.objects.select_related('cliente'), pk=pk)

        atendimentos = fatura.atendimentos.select_related('animal', 'servico').order_by('data', 'pk')
        pagamentos = list(
            fatura.pagamentos.select_related('funcionario').order_by('-data_pagamento')
        )

        total_pago = fatura.total_pago
        saldo = fatura.valor_final - total_pago

        return render(request, 'visualizar_fatura.html', {
            'fatura': fatura,
            'atendimentos': atendimentos,
            'pagamentos': pagamentos,
            'total_pago': total_pago,
            'saldo': saldo,
            'status_pagamento': fatura.status_pagamento,
            'form': PagamentoForm(initial={'valor': saldo if saldo > 0 else None}),
            'pode_excluir': len(pagamentos) == 0
        })


class FaturaDeleteView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.delete_fatura'

    def get(self, request, pk):
        fatura = get_object_or_404(Fatura.objects.select_related('cliente'), pk=pk)

        return render(request, 'excluir_fatura.html', {
            'fatura': fatura
        })

    def post(self, request, pk):
        with transaction.atomic():
            fatura = get_object_or_404(Fatura.objects.select_for_update(), pk=pk)

            # Fatura com qualquer pagamento (inclusive estornado) mantém o histórico financeiro
            if fatura.pagamentos.exists():
                messages.error(
                    request,
                    "Não é possível excluir uma fatura que já tem pagamentos registrados."
                )
                return redirect('fatura_detalhe', pk=pk)

            # Libera os atendimentos para entrarem em outra fatura
            fatura.atendimentos.update(fatura=None)
            fatura.delete()

        messages.success(request, "Fatura excluída. Os atendimentos voltaram a ficar sem fatura.")
        return redirect('fatura')


class PagamentoCreateView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.add_pagamento'

    # só aceita POST (o formulário fica na tela da fatura)
    def post(self, request, pk):
        fatura = get_object_or_404(Fatura, pk=pk)

        funcionario = Funcionario.objects.filter(usuario=request.user).first()
        if funcionario is None:
            messages.error(
                request,
                "Seu usuário não está vinculado a um funcionário, "
                "então não é possível registrar pagamentos."
            )
            return redirect('fatura_detalhe', pk=pk)

        form = PagamentoForm(request.POST)

        if form.is_valid():
            try:
                fatura.registrar_pagamento(
                    form.cleaned_data['valor'],
                    funcionario,
                    form.cleaned_data['forma']
                )
            except ValidationError as e:
                messages.error(request, " ".join(e.messages))
            else:
                messages.success(request, "Pagamento registrado com sucesso!")
        else:
            for campo, erros in form.errors.items():
                messages.error(request, f"{form.fields[campo].label}: {' '.join(erros)}")

        return redirect('fatura_detalhe', pk=pk)


class PagamentoEstornarView(PermissaoComRedirecionamentoMixin, View):
    permission_required = 'app.change_pagamento'

    # só aceita POST
    def post(self, request, pk):
        with transaction.atomic():
            pagamento = get_object_or_404(Pagamento.objects.select_for_update(), pk=pk)

            if pagamento.estornado:
                messages.error(request, "Este pagamento já foi estornado.")
            else:
                pagamento.estornado = True
                pagamento.save(update_fields=['estornado'])
                messages.success(request, "Pagamento estornado. O saldo da fatura foi atualizado.")

        return redirect('fatura_detalhe', pk=pagamento.fatura_id)



