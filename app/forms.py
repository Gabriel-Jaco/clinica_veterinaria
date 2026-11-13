from django import forms
from .models import Funcionario

class FuncionarioForm(forms.ModelForm):

    class Meta:
        model = Funcionario
        fields = [
            'nome',
            'sobrenome',
            'cpf',
            'contato',
            'email',
            'data_nascimento',
            'endereco',
            'funcao'
        ]

        widgets = {
            'data_nascimento': forms.DateInput(
                attrs={'type': 'date'}
            ),

            'funcao': forms.Textarea(
                attrs={'rows': 3}
            )
        }