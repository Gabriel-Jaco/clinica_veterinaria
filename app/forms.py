from django import forms
from django.db.models import Q
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.utils import timezone

from .models import *


class FuncionarioForm(forms.ModelForm):

    rua = forms.CharField(label="Nome da rua")
    numero = forms.IntegerField(label="Número do endereço")
    bairro = forms.CharField(label="Bairro do endereço")
    cidade = forms.ModelChoiceField(
        queryset=Cidade.objects.all(),
        label="Cidade"
    )

    class Meta:
        model = Funcionario
        fields = [
            'nome',
            'sobrenome',
            'cpf',
            'contato',
            'email',
            'data_nascimento',
            'rua',
            'numero',
            'bairro',
            'cidade',
            'descricao'
        ]

        widgets = {
            # format ISO: sem ele o campo type=date aparece vazio na edição
            'data_nascimento': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'descricao': forms.Textarea(
                attrs={'rows': 3}
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            endereco = self.instance.endereco

            self.fields['rua'].initial = endereco.rua
            self.fields['numero'].initial = endereco.numero
            self.fields['bairro'].initial = endereco.bairro
            self.fields['cidade'].initial = endereco.cidade

    def save(self, commit=True):
        funcionario = super().save(commit=False)

        if funcionario.pk:
            endereco = funcionario.endereco
        else:
            endereco = Endereco()

        endereco.rua = self.cleaned_data['rua']
        endereco.numero = self.cleaned_data['numero']
        endereco.bairro = self.cleaned_data['bairro']
        endereco.cidade = self.cleaned_data['cidade']

        if commit:
            endereco.save()
            funcionario.endereco = endereco
            funcionario.save()
            self.save_m2m()

        return funcionario
    




class ClienteForm(forms.ModelForm):

    rua = forms.CharField(
        max_length=100,
        label="Nome da rua"
    )

    numero = forms.IntegerField(
        label="Número do endereço"
    )

    bairro = forms.CharField(
        max_length=100,
        label="Bairro do endereço"
    )

    cidade = forms.ModelChoiceField(
        queryset=Cidade.objects.all(),
        label="Cidade"
    )

    data_nascimento = forms.DateField(
        widget=forms.DateInput(
            attrs={'type': 'date'},
            format='%Y-%m-%d'
        ),
        input_formats=['%Y-%m-%d']
    )

    class Meta:
        model = Cliente
        fields = [
            'nome',
            'sobrenome',
            'cpf',
            'contato',
            'data_nascimento',
            'genero',
            'rua',
            'numero',
            'bairro',
            'cidade'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            endereco = self.instance.endereco

            self.fields['rua'].initial = endereco.rua
            self.fields['numero'].initial = endereco.numero
            self.fields['bairro'].initial = endereco.bairro
            # Havia uma vírgula no final, que transformava o valor em tupla
            # e impedia a cidade de vir selecionada na edição
            self.fields['cidade'].initial = endereco.cidade





class AnimalForm(forms.ModelForm):

    raca = forms.ModelChoiceField(
        queryset=Raca.objects.all(),
        label="Raça"
    )

    tutor = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        label="Tutor"
    )

    class Meta:
        model = Animal
        fields = [
            'nome',
            'sobrenome',
            'rg',
            'data_nasc',
            'peso',
            'raca',
            'tutor'
        ]

        widgets = {
            'data_nasc': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'peso': forms.NumberInput(
                attrs={'step': 'any', 'min': '0'}
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['data_nasc'].input_formats = ['%Y-%m-%d']

class RacaForm(forms.ModelForm):

    class Meta:
        model = Raca
        fields = ['nome', 'especie']
        labels = {
            'nome': 'Nome da raça',
            'especie': 'Espécie do animal'
        }


class FornecedorForm(forms.ModelForm):

    rua = forms.CharField(
        max_length=100,
        label="Nome da rua"
    )

    numero = forms.IntegerField(
        label="Número do endereço"
    )

    bairro = forms.CharField(
        max_length=100,
        label="Bairro do endereço"
    )

    cidade = forms.ModelChoiceField(
        queryset=Cidade.objects.all(),
        label="Cidade"
    )

    class Meta:
        model = Fornecedor
        fields = [
            'nome',
            'cnpj',
            'contato',
            'email',
            'rua',
            'numero',
            'bairro',
            'cidade'
        ]

        labels = {
            'nome': 'Nome do fornecedor',
            'cnpj': 'CNPJ',
            'contato': 'Número de contato',
            'email': 'E-mail'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            endereco = self.instance.endereco

            self.fields['rua'].initial = endereco.rua
            self.fields['numero'].initial = endereco.numero
            self.fields['bairro'].initial = endereco.bairro
            self.fields['cidade'].initial = endereco.cidade

    def save(self, commit=True):
        fornecedor = super().save(commit=False)

        if fornecedor.pk:
            endereco = fornecedor.endereco
        else:
            endereco = Endereco()

        endereco.rua = self.cleaned_data['rua']
        endereco.numero = self.cleaned_data['numero']
        endereco.bairro = self.cleaned_data['bairro']
        endereco.cidade = self.cleaned_data['cidade']

        if commit:
            endereco.save()
            fornecedor.endereco = endereco
            fornecedor.save()
            self.save_m2m()

        return fornecedor

class ProdutoForm(forms.ModelForm):

    class Meta:
        model = Produto

        fields = [
            'nome',
            'unidade',
            'preco_custo',
            'preco_venda'
        ]

        labels = {
            'nome': 'Nome do produto',
            'unidade': 'Unidade de venda',
            'preco_custo': 'Preço de custo (por unidade de venda)',
            'preco_venda': 'Preço de venda (por unidade de venda)'
        }

        widgets = {
            'preco_custo': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0'
            }),

            'preco_venda': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0'
            })
        }

class LoteForm(forms.ModelForm):

    class Meta:
        model = Lote

        fields = [
            'numero',
            'data_validade',
            'quantidade',
            'fornecedor',
            'produto'
        ]

        labels = {
            'numero': 'Número do lote',
            'data_validade': 'Data de validade',
            'quantidade': 'Quantidade',
            'fornecedor': 'Fornecedor',
            'produto': 'Produto'
        }

        widgets = {
            # format ISO: sem ele o campo type=date aparece vazio na edição
            'data_validade': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),

            'quantidade': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['fornecedor'].queryset = Fornecedor.objects.all().order_by('nome')
        self.fields['produto'].queryset = Produto.objects.all().order_by('nome')


# ======================================================================
# forms.py -> SUBSTITUA a classe AtendimentoForm inteira por esta.
# No topo do forms.py já existem os imports necessários (timezone etc.).
# ======================================================================

class AtendimentoForm(forms.ModelForm):
    class Meta:
        model = Atendimento
        # valor_servico saiu do formulário: é definido pelo sistema a partir do Servico
        fields = [
            'data',
            'status',
            'observacao',
            'servico',
            'animal',
            'funcionario'
        ]

        labels = {
            'data': 'Data do atendimento',
            'status': 'Status',
            'observacao': 'Observações',
            'servico': 'Serviço',
            'animal': 'Animal',
            'funcionario': 'Funcionário'
        }

        widgets = {
            'data': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['data'].input_formats = ['%Y-%m-%d']

        # Data de hoje já preenchida, mas editável. Na edição, vale a data salva.
        self.fields['data'].initial = timezone.localdate

        # Mostra o valor de cada serviço no select
        self.fields['servico'].label_from_instance = lambda s: (
            f"{s.nome} — R$ {s.valor:.2f}".replace('.', ',')
        )

    def save(self, commit=True):
        atendimento = super().save(commit=False)

        # Atendimento novo, ou serviço trocado: pega o valor atual do serviço.
        # Se o serviço não mudou, mantém o valor que o atendimento já tinha.
        if not atendimento.pk or 'servico' in self.changed_data:
            atendimento.valor_servico = atendimento.servico.valor

        if commit:
            atendimento.save()

        return atendimento

class ProdutoAtendimentoForm(forms.ModelForm):
    class Meta:
        model = Produto_atendimento
        fields = ['lote', 'quantidade']

        labels = {
            'lote': 'Lote utilizado',
            'quantidade': 'Quantidade utilizada'
        }

        widgets = {
            'quantidade': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0.01'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Só lotes com saldo e dentro da validade.
        # Em edição, o lote já usado pelo item continua na lista mesmo que o saldo
        # tenha chegado a zero ou o lote tenha vencido; senão o form ficaria inválido.
        filtro = Q(quantidade__gt=0, data_validade__gte=timezone.localdate())

        if self.instance.pk:
            filtro |= Q(pk=self.instance.lote_id)

        self.fields['lote'].queryset = Lote.objects.filter(
            filtro
        ).select_related('produto', 'fornecedor').order_by('produto__nome', 'data_validade')

        # Ex.: "Agulha (unidade) — lote 1 — saldo 50 — val. 31/12/2026"
        self.fields['lote'].label_from_instance = lambda l: (
            f"{l.produto.nome} ({l.produto.get_unidade_display()}) — "
            f"lote {l.numero} — saldo {l.quantidade:g} — "
            f"val. {l.data_validade:%d/%m/%Y}"
        )

    def clean_quantidade(self):
        # O min=0.01 do widget só vale no navegador; o validator do model aceita 0
        quantidade = self.cleaned_data['quantidade']

        if quantidade is not None and quantidade <= 0:
            raise forms.ValidationError("A quantidade deve ser maior que zero.")

        return quantidade


class BaseProdutoAtendimentoFormSet(BaseInlineFormSet):

    def clean(self):
        super().clean()

        # Estado original dos itens já salvos, lido do banco. Não dá para usar
        # form.instance: na validação ele já foi sobrescrito com os valores novos.
        ids_existentes = [
            form.instance.pk for form in self.initial_forms if form.instance.pk
        ]

        devolvido = {}
        originais = Produto_atendimento.objects.filter(
            pk__in=ids_existentes
        ).values('lote_id', 'quantidade')

        # Lote.quantidade já tem o consumo desses itens descontado; ao editar ou
        # remover, essa quantidade volta a ficar disponível.
        for original in originais:
            devolvido[original['lote_id']] = (
                devolvido.get(original['lote_id'], 0) + original['quantidade']
            )

        necessario = {}
        lotes = {}

        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue

            dados = form.cleaned_data

            if not dados or dados.get('DELETE'):
                continue

            lote = dados.get('lote')
            quantidade = dados.get('quantidade')

            if lote and quantidade:
                necessario[lote.pk] = necessario.get(lote.pk, 0) + quantidade
                lotes[lote.pk] = lote

        for lote_pk, total in necessario.items():
            lote = lotes[lote_pk]
            disponivel = lote.quantidade + devolvido.get(lote_pk, 0)

            # tolerância pequena por causa de float
            if total > disponivel + 1e-9:
                raise forms.ValidationError(
                    f"Quantidade insuficiente no lote {lote.numero}. "
                    f"Disponível: {disponivel}."
                )


ProdutoAtendimentoFormSet = inlineformset_factory(
    Atendimento,
    Produto_atendimento,
    form=ProdutoAtendimentoForm,
    formset=BaseProdutoAtendimentoFormSet,
    extra=1,
    can_delete=True
)

class ServicoForm(forms.ModelForm):

    class Meta:
        model = Servico
        fields = ['nome', 'valor']

        labels = {
            'nome': 'Nome do serviço/taxa',
            'valor': 'Valor (R$)'
        }

        widgets = {
            'valor': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0'
            })
        }

    def clean_valor(self):
        valor = self.cleaned_data['valor']

        if valor is not None and valor < 0:
            raise forms.ValidationError("O valor não pode ser negativo.")

        return valor

class PagamentoForm(forms.Form):
    valor = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        label="Valor recebido (R$)",
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'})
    )

    forma = forms.ChoiceField(
        choices=Pagamento.Forma.choices,
        label="Forma de pagamento"
    )

