from django.db import models
from django.core.validators import MinValueValidator

# Create your models here.

class Cidade(models.Model):
    cidade = models.CharField(max_length = 100, verbose_name="cidade do endereço")
    uf = models.CharField(max_length = 2, verbose_name="estado do endereço(UF)")

    class Meta:
        verbose_name = "Cidade"
        verbose_name_plural = "Cidades"
    def __str__(self):
        return f"{self.cidade}, {self.uf}"
    
class Endereco(models.Model):
    rua = models.CharField(max_length = 100, verbose_name="nome da rua")
    numero = models.IntegerField(verbose_name="Número do endereço")
    bairro = models.CharField(max_length = 100, verbose_name="bairro do endereço")
    cidade = models.ForeignKey(Cidade, on_delete = models.CASCADE, verbose_name="Cidade do endereço")
    
    class Meta:
        verbose_name="Endereco"
        verbose_name_plural="Enderecos"
    def __str__(self):
        return f"{self.rua}, {self.bairro}"

class Cliente(models.Model):
    nome = models.CharField(max_length = 20, verbose_name="Nome do cliente")
    sobrenome = models.CharField(max_length = 100, verbose_name="Sobrenome do cliente")
    cpf = models.CharField(max_length = 14, verbose_name="CPF do cliente com . . -")
    contato = models.CharField(max_length = 20,verbose_name = "Número de contato do cliente")
    data_nascimento = models.DateField(verbose_name= "data de nascimento do cliente")
    endereco = models.ForeignKey(Endereco, on_delete = models.CASCADE, verbose_name="endereço do cliente")

    class Meta: 
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
    
    def __str__(self):
        return self.nome


class Especie(models.Model):
    nome = models.CharField(max_length = 100, verbose_name="Refere-se ao nome dos adjetivos que cada grupo recebe")
   
    class Meta:
        verbose_name = "Especie"
        verbose_name_plural = "Especies"
    
    def __str__(self):
        return self.nome

class Raca(models.Model):
    nome = models.CharField(max_length = 100, verbose_name="Raça de animais")
    especie = models.ForeignKey(Especie, on_delete = models.CASCADE, verbose_name="Especie da raça")

    class Meta:
        verbose_name = "Raca"
        verbose_name_plural = "Racas"

    def __str__(self):
        return self.nome


class Animal(models.Model):
    nome = models.CharField(max_length=20, verbose_name="Nome do animal")
    sobrenome = models.CharField(max_length = 100, blank=True, null=True, verbose_name = "sobrenome do animal (se tiver)")
    rg = models.CharField(max_length = 15, verbose_name="RG do animal", blank=True, null=True)
    data_nasc = models.DateField(verbose_name = "data de nascimento do animal")
    peso = models.FloatField(validators=[MinValueValidator(0.0)], verbose_name="Peso do animal")
    raca = models.ForeignKey(Raca, on_delete = models.CASCADE, verbose_name= "raça do animal")
    tutor = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name = "dono do animal")

    class Meta:
        verbose_name = "Animai"
        verbose_name_plural = "Animais"
        
    def __str__(self):
        return f"{self.nome}, {self.tutor}"



class Fornecedor(models.Model):
    nome = models.CharField(max_length=100, verbose_name = "nome do fornecedor")
    cnpj = models.CharField(max_length = 18, verbose_name = "cnpj do fornecedor")
    contato = models.CharField(max_length = 20, verbose_name = "Número de contato do fornecedor")
    endereco = models.ForeignKey(Endereco, on_delete = models.CASCADE, verbose_name="endereço do fornecedor")

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"

    def __str__(self):
        return self.nome

class Produto(models.Model):
    nome = models.CharField(max_length=100, verbose_name = "Nome do produto")
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de custo")
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de venda")
    estoque = models.FloatField(validators = [MinValueValidator(0.0)], verbose_name = "estoque atual do produto")
    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"

    def __str__(self):
        return self.nome

class Lote(models.Model): 
    numero = models.CharField(max_length = 20, verbose_name="número do lote")
    data_validade = models.DateField(verbose_name="data de validade do lote")
    quantidade = models.FloatField(validators=[MinValueValidator(0.0)], verbose_name = "Quantidade que veio no lote")
    fornecedor = models.ForeignKey(Fornecedor, on_delete = models.CASCADE, verbose_name="fornecedores do lote")
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, verbose_name="produto deste lote")
    
    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"

    def __str__(self):
        return self.numero
    




class Servico(models.Model):
    nome = models.CharField(max_length=100, verbose_name="nome do serviço/taxa")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço do serviço/taxa")

    class Meta:
        verbose_name = "Servico"
        verbose_name_plural = "Servicos"

    def __str__(self):
        return self.nome

class Funcionario(models.Model):
    nome = models.CharField(max_length = 20, verbose_name="Nome do funcionario")
    sobrenome = models.CharField(max_length = 100, verbose_name="Sobrenome do funcionario")
    cpf = models.CharField(max_length = 14, verbose_name="CPF do funcionario com . . -")
    contato = models.CharField(max_length = 20,verbose_name = "Número de contato do funcionario")
    data_nascimento = models.DateField(verbose_name= "data de nascimento do funcionario")
    endereco = models.ForeignKey(Endereco, on_delete = models.CASCADE, verbose_name="endereço do funcionario")
    funcao = models.TextField(verbose_name="Breve descrição da funcionalidade do funcionário")

    class Meta:
        verbose_name = "Funcionario"
        verbose_name_plural = "Funcionarios"

    def __str__(self):
        return self.nome

class Atendimento(models.Model):
    data = models.DateField(verbose_name="data do atendimento")
    status = models.CharField(max_length = 20, verbose_name="status do atendimento")
    observacao = models.TextField(blank=True, null=True, verbose_name="observação")
    valor_servico = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="valor da taxa")
    valor_materiais = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="alor dos materiais")
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="valor total")

    servico = models.ForeignKey(Servico, on_delete = models.CASCADE, verbose_name="serviço do atendimento")
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, verbose_name = "animal em atendimento")
    funcionario = models.ForeignKey(Funcionario, on_delete = models.CASCADE, verbose_name="funcionario do atendimento")

    class Meta:
        verbose_name = "Atendimento"
        verbose_name_plural = "Atendimentos"

    def __str__(self):
        return self.status


class Produto_atendimento(models.Model):
    quantidade = models.FloatField(validators = [MinValueValidator(0.0)], verbose_name = "quantidade utilizada na venda")
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de custo")
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de venda")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="soma dos produtos")
    produto = models.ForeignKey(Produto, on_delete = models.CASCADE, verbose_name="produtos do atendimento")
    lote = models.ForeignKey(Lote, on_delete = models.CASCADE, verbose_name="lote dos produtos do atendimento")
    atendimento = models.ForeignKey(Atendimento, on_delete = models.CASCADE, verbose_name="atendimento")

    class Meta:
        verbose_name = "Produto_atendimento"
        verbose_name_plural = "Produto_atendimentos"

    


class Fatura(models.Model):
    valor_final = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="valor final")
    status_pagamento = models.CharField(max_length=20, verbose_name = "status do pagamento")
    atendimento = models.ForeignKey(Atendimento, on_delete = models.CASCADE, verbose_name="fatura do atendimento")
    cliente = models.ForeignKey(Cliente, on_delete = models.CASCADE, verbose_name="fatura do cliente")

    class Meta:
        verbose_name = "Fatura"
        verbose_name_plural = "Faturas"

    def __str__(self):
        return self.status_pagamento





    




