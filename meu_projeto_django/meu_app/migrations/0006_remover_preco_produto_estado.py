from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("meu_app", "0005_afiliado_comissao")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveField(model_name="produto", name="preco"),
            ],
        ),
    ]
