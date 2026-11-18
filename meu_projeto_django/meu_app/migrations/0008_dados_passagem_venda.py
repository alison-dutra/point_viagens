from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("meu_app", "0007_venda_comissao_personalizada")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(model_name="venda", name="data_hora_ida", field=models.DateTimeField(blank=True, null=True)),
                migrations.AddField(model_name="venda", name="data_hora_volta", field=models.DateTimeField(blank=True, null=True)),
                migrations.AddField(model_name="venda", name="localizador_reserva", field=models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
    ]
