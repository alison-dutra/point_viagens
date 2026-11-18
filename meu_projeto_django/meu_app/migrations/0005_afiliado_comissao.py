from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('meu_app', '0004_produto_comissao')]

    operations = [
        migrations.AddField(
            model_name='afiliado',
            name='comissao',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
    ]
