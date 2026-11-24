
from django import forms
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
            'data_nascimento': forms.DateInput(
                attrs={'type': 'date'}
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
            self.fields['cidade'].initial = endereco.cidade,





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