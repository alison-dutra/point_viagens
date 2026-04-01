from django.db import models


class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=100)
    nascimento = models.CharField(max_length=100)
    celular = models.CharField(max_length=100)
    email = models.CharField(max_length=100)

    class Meta:
        db_table = 'cadastro_cliente'
        managed = True

    def __str__(self):
        return self.nome


class Afiliado(models.Model):
    nome_afiliado = models.CharField(max_length=100)
    cpf = models.CharField(max_length=100)
    rg = models.CharField(max_length=100)
    endereco = models.CharField(max_length=100, db_column='endereço')
    celular = models.CharField(max_length=100)
    email = models.CharField(max_length=100, unique=True)
    documento_foto = models.FileField(upload_to='documentos_afiliados/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
    ('pendente', 'Pendente'),
    ('aprovado', 'Aprovado'),
    ('reprovado', 'Reprovado'),
    ], default='pendente')

    class Meta:
        db_table = 'cadastro_afiliado'
        managed = True

    def __str__(self):
        return self.nome_afiliado

class Produto(models.Model):
    nome_produto = models.CharField(max_length=100)
    categoria_id = models.IntegerField(null=True, blank=True)
    marca = models.CharField(max_length=100, null=True, blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    descricao = models.TextField(null=True, blank=True)
    imagem_url = models.CharField(max_length=500, null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'produtos'
        managed = True

    def __str__(self):
        return self.nome_produto


class Venda(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('reprovado', 'Reprovado'),
        ('aprovado', 'Aprovado'),
    ]

    codigo_venda = models.CharField(max_length=100)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, db_column='cliente_id')
    afiliado = models.ForeignKey(Afiliado, on_delete=models.PROTECT, db_column='afiliado_id')
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, db_column='produto_id')
    descricao_venda = models.CharField(max_length=100)
    tipo_venda = models.CharField(max_length=100)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    status_venda = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    data_venda = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vendas'
        managed = True

    def __str__(self):
        return self.codigo_venda
    
class ComissaoPagamento(models.Model):
    afiliado = models.ForeignKey(Afiliado, on_delete=models.PROTECT, db_column='afiliado_id')
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_pagamento = models.DateField()
    descricao = models.TextField(null=True, blank=True)
    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comissoes_pagamentos'
        managed = True

    def __str__(self):
        return f'{self.afiliado.nome_afiliado} - R$ {self.valor} - {self.data_pagamento}'


class ToDoList(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Item(models.Model):
    todolsit = models.ForeignKey(ToDoList, on_delete=models.CASCADE)
    text = models.CharField(max_length=300)
    complete = models.BooleanField()

    def __str__(self):
        return self.text
    
class AfiliadoDocumento(models.Model):
    afiliado = models.ForeignKey(Afiliado, on_delete=models.CASCADE, db_column='afiliado_id', related_name='documentos')
    arquivo = models.FileField(upload_to='documentos_afiliados/')
    data_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'afiliado_documentos'
        managed = True

    def __str__(self):
        return f'{self.afiliado.nome_afiliado} - {self.arquivo.name}'