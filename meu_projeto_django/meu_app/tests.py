from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import translation

from .forms import ProdutoForm
from .models import Produto, Cliente, Afiliado, Venda


class ProdutosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='admin', is_superuser=True, is_staff=True)
        cls.funcionario = User.objects.create_user(username='funcionario', is_staff=True)

    def test_admin_cadastra_produto_e_disponibiliza_na_venda(self):
        self.client.force_login(self.admin)
        with translation.override('pt-br'):
            response = self.client.post(reverse('produtos'), {
                'nome_produto': 'Pacote de viagem', 'marca': 'Point',
            })
        self.assertRedirects(response, reverse('produtos'), fetch_redirect_response=False)
        produto = Produto.objects.get()
        response = self.client.get(reverse('produtos'))
        self.assertContains(response, 'Produto cadastrado com sucesso!')
        self.assertContains(response, 'Pacote de viagem')
        self.assertContains(response, 'data-tab="produtos"')
        response = self.client.get(reverse('area_do_afiliado_logado'))
        self.assertIn(produto, response.context['produtos'])

    def test_dados_invalidos_preservados_sem_salvar(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('produtos'), {
            'nome_produto': ' ', 'comissao': '-1',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['produto_form'].errors)
        self.assertContains(response, 'value="Pacote"')
        self.assertFalse(Produto.objects.exists())

    def test_validacao_campos(self):
        for dados in [
            {'nome_produto': ' '},
            {'nome_produto': 'Teste', 'comissao': '-1'},
            {'nome_produto': 'Teste', 'comissao': 'abc'},
            {'nome_produto': 'Teste', 'comissao': '100000000'},
        ]:
            with self.subTest(dados=dados):
                self.assertFalse(ProdutoForm(dados).is_valid())

    def test_funcionario_nao_acessa_nem_cadastra(self):
        self.client.force_login(self.funcionario)
        for headers in [{}, {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}]:
            self.assertEqual(self.client.get(reverse('produtos'), **headers).status_code, 403)
        self.assertEqual(self.client.post(reverse('produtos'), {
            'nome_produto': 'Teste',
        }).status_code, 403)
        self.assertFalse(Produto.objects.exists())
        response = self.client.get(reverse('area_do_afiliado_logado'))
        self.assertNotContains(response, 'data-tab="produtos"')

    def test_anonimo_redirecionado(self):
        self.assertEqual(self.client.get(reverse('produtos')).status_code, 302)
        self.assertEqual(self.client.post(reverse('produtos')).status_code, 302)
        self.assertFalse(Produto.objects.exists())

    def test_cadastro_exige_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(reverse('produtos'), {
            'nome_produto': 'Teste',
        }).status_code, 403)
        self.assertFalse(Produto.objects.exists())


    def test_acentos_e_edicao_sem_duplicar_produto(self):
        self.client.force_login(self.admin)
        produto = Produto.objects.create(nome_produto='São João')
        url = reverse('editar_produto', args=[produto.pk])
        response = self.client.get(url)
        for texto in ['Descrição', 'São João', 'Salvar alterações']:
            self.assertContains(response, texto)
        response = self.client.post(url, {
            'nome_produto': 'Férias em São Luís',
            'descricao': 'Promoção de verão',
        })
        self.assertRedirects(response, reverse('produtos'), fetch_redirect_response=False)
        produto.refresh_from_db()
        self.assertEqual(produto.nome_produto, 'Férias em São Luís')
        self.assertEqual(produto.descricao, 'Promoção de verão')
        self.assertEqual(Produto.objects.count(), 1)
        response = self.client.get(reverse('produtos'))
        self.assertContains(response, 'Férias em São Luís')
        self.assertContains(response, 'Ações')

    def test_edicao_invalida_nao_altera_produto(self):
        self.client.force_login(self.admin)
        produto = Produto.objects.create(nome_produto='Original')
        response = self.client.post(reverse('editar_produto', args=[produto.pk]), {
            'nome_produto': 'Alterado',
        })
        self.assertContains(response, 'produtoEditDialog')
        self.assertTrue(response.context['produto_form'].errors)
        produto.refresh_from_db()
        self.assertEqual(produto.nome_produto, 'Original')

    def test_remocao_exige_post_e_remove_produto(self):
        self.client.force_login(self.admin)
        produto = Produto.objects.create(nome_produto='Teste')
        url = reverse('remover_produto', args=[produto.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertTrue(Produto.objects.filter(pk=produto.pk).exists())
        self.assertRedirects(self.client.post(url), reverse('produtos'), fetch_redirect_response=False)
        self.assertFalse(Produto.objects.filter(pk=produto.pk).exists())

    def test_produto_com_venda_nao_pode_ser_removido(self):
        self.client.force_login(self.admin)
        produto = Produto.objects.create(nome_produto='Vinculado')
        cliente = Cliente.objects.create(nome='Cliente')
        afiliado = Afiliado.objects.create(nome_afiliado='Afiliado', email='teste@example.com')
        venda = Venda.objects.create(
            codigo_venda='V1', cliente=cliente, afiliado=afiliado, produto=produto, valor='10',
        )
        response = self.client.post(reverse('remover_produto', args=[produto.pk]), follow=True)
        self.assertContains(response, 'Não é possível remover')
        self.assertTrue(Produto.objects.filter(pk=produto.pk).exists())
        self.assertTrue(Venda.objects.filter(pk=venda.pk).exists())

    def test_edicao_e_remocao_protegidas(self):
        produto = Produto.objects.create(nome_produto='Original')
        editar = reverse('editar_produto', args=[produto.pk])
        remover = reverse('remover_produto', args=[produto.pk])
        for url in [editar, remover]:
            self.assertEqual(self.client.post(url).status_code, 302)
        self.client.force_login(self.funcionario)
        self.assertEqual(self.client.get(editar).status_code, 403)
        for url in [editar, remover]:
            self.assertEqual(self.client.post(url).status_code, 403)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        for url in [editar, remover]:
            self.assertEqual(client.post(url).status_code, 403)
        produto.refresh_from_db()
        self.assertEqual(produto.nome_produto, 'Original')

    def test_produto_inexistente(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('editar_produto', args=[999])).status_code, 404)
        self.assertEqual(self.client.post(reverse('remover_produto', args=[999])).status_code, 404)


    def test_categoria_no_cadastro_edicao_e_limpeza(self):
        self.client.force_login(self.admin)
        dados = {'nome_produto': 'Pacote', 'categoria_id': 'Traslado'}
        self.assertEqual(self.client.post(reverse('produtos'), dados).status_code, 302)
        produto = Produto.objects.get()
        self.assertEqual(produto.categoria_id, 'Traslado')
        editar = reverse('editar_produto', args=[produto.pk])
        response = self.client.get(editar)
        self.assertContains(response, 'Categoria')
        self.assertEqual(response.context['produto_form']['categoria_id'].value(), 'Traslado')
        dados['categoria_id'] = 'Passeio'
        self.assertEqual(self.client.post(editar, dados).status_code, 302)
        produto.refresh_from_db()
        self.assertEqual(produto.categoria_id, 'Passeio')
        dados['categoria_id'] = ''
        self.assertEqual(self.client.post(editar, dados).status_code, 302)
        produto.refresh_from_db()
        self.assertIsNone(produto.categoria_id)

    def test_categoria_textual_com_acentos_e_limite(self):
        form = ProdutoForm({
            'nome_produto': 'Pacote',
            'categoria_id': 'Excurs\u00e3o',
        })
        self.assertTrue(form.is_valid(), form.errors)
        produto = form.save()
        produto.refresh_from_db()
        self.assertEqual(produto.categoria_id, 'Excurs\u00e3o')
        form = ProdutoForm({
            'nome_produto': 'Pacote', 'categoria_id': 'a' * 101,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('categoria_id', form.errors)
