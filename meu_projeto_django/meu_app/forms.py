from decimal import Decimal

from django import forms

from .models import Produto


class ProdutoForm(forms.ModelForm):
    comissao = forms.DecimalField(
        label='Comissão (%)', max_digits=5, decimal_places=2,
        min_value=Decimal('0.00'), localize=True, required=False,
        widget=forms.TextInput(attrs={'inputmode': 'decimal', 'placeholder': '0,00'}),
    )

    class Meta:
        model = Produto
        fields = ['nome_produto', 'categoria_id', 'comissao', 'descricao']
        labels = {
            'nome_produto': 'Nome do produto',
            'categoria_id': 'Categoria',
            'comissao': 'Comissão (%)',
            'descricao': 'Descrição',
        }
        widgets = {
            'categoria_id': forms.TextInput(attrs={'placeholder': 'Ex.: Traslado'}),
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }