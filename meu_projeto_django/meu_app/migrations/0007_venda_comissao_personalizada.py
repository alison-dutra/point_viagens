from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("meu_app", "0006_remover_preco_produto_estado")]

    operations = [
        migrations.AddField(
            model_name="venda",
            name="comissao_personalizada",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
    ]
