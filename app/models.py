from decimal import Decimal

from django.db import models, transaction
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.conf import settings
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
    genero = models.CharField(max_length=20, default='nenhum', verbose_name="genero do cliente (opcional)")
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
        return f"{self.nome}, {self.especie.nome}"


class Animal(models.Model):
    nome = models.CharField(max_length=20, verbose_name="Nome do animal")
    sobrenome = models.CharField(max_length = 100, blank=True, null=True, verbose_name = "sobrenome do animal (se tiver)")
    rg = models.CharField(max_length = 15, verbose_name="RG do animal", blank=True, null=True)
    data_nasc = models.DateField(verbose_name = "data de nascimento do animal")
    peso = models.FloatField(validators=[MinValueValidator(0.0)], verbose_name="Peso do animal")
    raca = models.ForeignKey(Raca, on_delete = models.CASCADE, verbose_name= "raça do animal")
    # PROTECT: apagar um cliente não pode apagar animais (e, por tabela, atendimentos e faturas)
    tutor = models.ForeignKey(Cliente, on_delete=models.PROTECT, verbose_name = "dono do animal")

    class Meta:
        verbose_name = "Animai"
        verbose_name_plural = "Animais"
        
    def __str__(self):
        return f"{self.nome}, {self.tutor}"



class Fornecedor(models.Model):
    nome = models.CharField(max_length=100, verbose_name = "nome do fornecedor")
    cnpj = models.CharField(max_length = 18, verbose_name = "cnpj do fornecedor")
    contato = models.CharField(max_length = 20, verbose_name = "Número de contato do fornecedor")
    email = models.EmailField(max_length=100, verbose_name="E-mail")
    endereco = models.ForeignKey(Endereco, on_delete = models.CASCADE, verbose_name="endereço do fornecedor")

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"

    def __str__(self):
        return self.nome

class Produto(models.Model):
    class Unidade(models.TextChoices):
        UNIDADE = "un", "unidade"
        ML = "ml", "ml"
        LITRO = "l", "litro"
        GRAMA = "g", "grama"
        KG = "kg", "kg"
        METRO = "m", "metro"
        CENTIMETRO = "cm", "centimetro"

    nome = models.CharField(max_length=100, verbose_name = "Nome do produto")
    unidade = models.CharField(max_length=10, choices=Unidade.choices, default=Unidade.UNIDADE, verbose_name="unidade de venda")
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
    nome = models.CharField(max_length=20, verbose_name="Nome")
    sobrenome = models.CharField(max_length=100, verbose_name="Sobrenome")
    cpf = models.CharField(max_length=14, verbose_name="CPF")
    contato = models.CharField(max_length=20, verbose_name="Contato")
    email = models.EmailField(max_length=100, verbose_name="E-mail")

    data_nascimento = models.DateField(verbose_name="Data de nascimento")

    endereco = models.ForeignKey(Endereco,on_delete=models.CASCADE,verbose_name="Endereço")

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,null=True,blank=True)
    
    descricao = models.TextField(verbose_name="Descrição da função")

    class Meta:
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"

    def __str__(self):
        return self.nome

# class Funcionario(models.Model):
#     # ... seus campos atuais ...
    # usuario = models.OneToOneField(
    #     settings.AUTH_USER_MODEL,
    #     on_delete=models.CASCADE,
    #     null=True,
    #     blank=True,
    # )


class StatusPagamento(models.TextChoices):
    PENDENTE = "pendente", "Pendente"
    PARCIAL = "parcial", "Parcial"
    PAGO = "pago", "Pago"


class Atendimento(models.Model):
    class Status(models.TextChoices):
        ABERTO = "aberto", "Aberto"
        CONCLUIDO = "concluido", "Concluído"
        CANCELADO = "cancelado", "Cancelado"

    data = models.DateField(verbose_name="data do atendimento")
    status = models.CharField(max_length = 20, choices=Status.choices, default=Status.ABERTO, verbose_name="status do atendimento")
    observacao = models.TextField(blank=True, null=True, verbose_name="observação")
    # valor_servico, valor_materiais e valor_total funcionam como "foto" do preço no momento
    # do atendimento. Para atualizar, use sempre recalcular_totais().
    valor_servico = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="valor da taxa")
    valor_materiais = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="valor dos materiais")
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="valor total")

    servico = models.ForeignKey(Servico, on_delete = models.PROTECT, verbose_name="serviço do atendimento")
    animal = models.ForeignKey(Animal, on_delete=models.PROTECT, verbose_name = "animal em atendimento")
    funcionario = models.ForeignKey(Funcionario, on_delete = models.PROTECT, verbose_name="funcionario do atendimento")
    # Um atendimento pertence a no máximo uma fatura (evita cobrança duplicada)
    fatura = models.ForeignKey("Fatura", null=True, blank=True, on_delete=models.PROTECT,
                               related_name="atendimentos", verbose_name="fatura do atendimento")

    class Meta:
        verbose_name = "Atendimento"
        verbose_name_plural = "Atendimentos"

    def __str__(self):
        return self.status

    @property
    def status_pagamento(self):
        # O status financeiro do atendimento é o da fatura a que ele pertence
        if self.fatura_id is None:
            return StatusPagamento.PENDENTE
        return self.fatura.status_pagamento

    def clean(self):
        # A fatura só pode reunir atendimentos do mesmo tutor
        if self.fatura_id and self.animal_id and self.animal.tutor_id != self.fatura.cliente_id:
            raise ValidationError("O tutor do animal deste atendimento não é o cliente da fatura.")

    def recalcular_totais(self):
        """Único ponto que deve alterar valor_materiais e valor_total."""
        if self.fatura_id and self.fatura.status_pagamento == StatusPagamento.PAGO:
            raise ValidationError("Atendimento de fatura já paga não pode ser alterado.")
        materiais = self.produto_atendimento_set.aggregate(t=Sum("subtotal"))["t"] or Decimal("0.00")
        self.valor_materiais = materiais
        self.valor_total = self.valor_servico + materiais
        self.save(update_fields=["valor_materiais", "valor_total"])


class Produto_atendimento(models.Model):
    quantidade = models.FloatField(validators = [MinValueValidator(0.0)], verbose_name = "quantidade utilizada na venda")
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de custo")
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de venda")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="soma dos produtos")
    produto = models.ForeignKey(Produto, on_delete = models.PROTECT, verbose_name="produtos do atendimento")
    lote = models.ForeignKey(Lote, on_delete = models.PROTECT, verbose_name="lote dos produtos do atendimento")
    atendimento = models.ForeignKey(Atendimento, on_delete = models.CASCADE, verbose_name="atendimento")

    class Meta:
        verbose_name = "Produto_atendimento"
        verbose_name_plural = "Produto_atendimentos"

    


class Fatura(models.Model):
    data_emissao = models.DateField(auto_now_add=True, verbose_name="data de emissão")
    valor_final = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="valor final")
    cliente = models.ForeignKey(Cliente, on_delete = models.PROTECT, verbose_name="fatura do cliente")

    class Meta:
        verbose_name = "Fatura"
        verbose_name_plural = "Faturas"

    def __str__(self):
        return f"Fatura {self.pk} - {self.status_pagamento}"

    # Valores derivados dos pagamentos: não são armazenados, para nunca divergirem.
    # Pagamentos estornados não contam.
    @property
    def total_pago(self):
        return self.pagamentos.filter(estornado=False).aggregate(t=Sum("valor"))["t"] or Decimal("0.00")

    @property
    def saldo(self):
        return self.valor_final - self.total_pago

    @property
    def status_pagamento(self):
        if self.total_pago <= 0:
            return StatusPagamento.PENDENTE
        if self.saldo <= 0:
            return StatusPagamento.PAGO
        return StatusPagamento.PARCIAL

    def recalcular_valor_final(self):
        """Soma o valor_total dos atendimentos da fatura. Chamar na emissão."""
        total = self.atendimentos.aggregate(t=Sum("valor_total"))["t"] or Decimal("0.00")
        self.valor_final = total
        self.save(update_fields=["valor_final"])

    def registrar_pagamento(self, valor, funcionario, forma):
        """Único ponto para registrar pagamento. Trava a fatura para evitar
        dois pagamentos simultâneos estourarem o saldo."""
        valor = Decimal(valor)
        if valor <= 0:
            raise ValidationError("O valor do pagamento deve ser maior que zero.")
        with transaction.atomic():
            fatura = Fatura.objects.select_for_update().get(pk=self.pk)
            if valor > fatura.saldo:
                raise ValidationError("O pagamento não pode ser maior que o saldo da fatura.")
            return Pagamento.objects.create(
                fatura=fatura, valor=valor, funcionario=funcionario, forma=forma
            )


class Pagamento(models.Model):
    class Forma(models.TextChoices):
        DINHEIRO = "dinheiro", "Dinheiro"
        PIX = "pix", "Pix"
        DEBITO = "debito", "Cartão de débito"
        CREDITO = "credito", "Cartão de crédito"

    fatura = models.ForeignKey(Fatura, on_delete=models.PROTECT, related_name="pagamentos", verbose_name="fatura paga")
    funcionario = models.ForeignKey(Funcionario, on_delete=models.PROTECT, verbose_name="funcionário que recebeu")
    valor = models.DecimalField(max_digits=10, decimal_places=2,
                                validators=[MinValueValidator(Decimal("0.01"))], verbose_name="valor recebido")
    forma = models.CharField(max_length=20, choices=Forma.choices, verbose_name="forma de pagamento")
    data_pagamento = models.DateTimeField(auto_now_add=True, verbose_name="data e hora do recebimento")
    # Pagamento não deve ser editado nem apagado: para corrigir erro, marque como estornado
    estornado = models.BooleanField(default=False, verbose_name="pagamento estornado")

    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"

    def __str__(self):
        return f"R$ {self.valor} - fatura {self.fatura_id}"
