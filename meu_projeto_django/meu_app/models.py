from django.db import models
from django.conf import settings
from decimal import Decimal
import unicodedata


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
    comissao = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'cadastro_afiliado'
        managed = True

    def __str__(self):
        return self.nome_afiliado

    def comissao_para(self, produto):
        return self.comissao if self.comissao is not None else (produto.comissao or Decimal('0'))

class Produto(models.Model):
    nome_produto = models.CharField(max_length=100)
    categoria_id = models.CharField(max_length=100, null=True, blank=True)
    descricao = models.TextField(null=True, blank=True)
    imagem_url = models.CharField(max_length=500, null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    comissao = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00, 
        null=True, 
        blank=True,
        verbose_name="Comissão (%)"
    )

    class Meta:
        db_table = 'produtos'
        managed = True

    def __str__(self):
        return self.nome_produto

    @property
    def is_passagem_aerea(self):
        texto = f'{self.nome_produto or ""} {self.categoria_id or ""} {self.descricao or ""}'
        normalizado = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii').casefold()
        return 'passagem aerea' in normalizado

    

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
    comissao_personalizada = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    data_hora_ida = models.DateTimeField(null=True, blank=True)
    data_hora_volta = models.DateTimeField(null=True, blank=True)
    localizador_reserva = models.CharField(max_length=100, null=True, blank=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='vendas_criadas')
    status_venda = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    data_venda = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vendas'
        managed = True

    def __str__(self):
        return self.codigo_venda

    @property
    def comissao_percentual(self):
        if self.comissao_personalizada is not None:
            return self.comissao_personalizada
        return self.afiliado.comissao_para(self.produto)

    @property
    def comissao_valor(self):
        percentual = self.comissao_percentual or Decimal('0')
        return (self.valor * percentual / Decimal('100')).quantize(Decimal('0.01'))
    
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
