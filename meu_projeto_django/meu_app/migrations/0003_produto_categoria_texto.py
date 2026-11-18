from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('meu_app', '0002_todolist_afiliadodocumento_comissaopagamento_item_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='produto',
            name='categoria_id',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
    ]
