from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('area-do-afiliado-logado/produtos/<int:produto_id>/editar/', views.area_do_afiliado_logado, {'tab_slug': 'produtos'}, name='editar_produto'),
    path('area-do-afiliado-logado/produtos/<int:produto_id>/remover/', views.remover_produto, name='remover_produto'),
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('area-do-afiliado/', views.area_do_afiliado, name='area_do_afiliado'),
    path('area-do-afiliado/<slug:tab_slug>/', views.area_do_afiliado, name='area_do_afiliado_tab'),
    path('cadastro_afiliado/', views.cadastro_afiliado, name='cadastro_afiliado'),
    path('salvar_afiliado/', views.salvar_afiliado, name='salvar_afiliado'),
    path('area-do-afiliado-logado/', views.area_do_afiliado_logado, name='area_do_afiliado_logado'),
    path('area-do-afiliado-logado/nova-venda/', views.nova_venda, name='nova_venda'),
    path('area-do-afiliado-logado/produtos/', views.area_do_afiliado_logado, {'tab_slug': 'produtos'}, name='produtos'),
    path('area-do-afiliado-logado/<slug:tab_slug>/', views.area_do_afiliado_logado, name='area_do_afiliado_tab'),
    path('salvar_cliente/', views.salvar_cliente, name='salvar_cliente'),
    path('minhas-vendas/', views.minhas_vendas, name='minhas_vendas'),
    path('alterar_venda/<int:venda_id>/', views.alterar_venda, name='alterar_venda'),
    path('alterar_afiliado/<int:afiliado_id>/', views.alterar_afiliado, name='alterar_afiliado'),
    path('remover_afiliado/<int:afiliado_id>/', views.remover_afiliado, name='remover_afiliado'),
    path('gestao_comissao/', views.gestao_comissao, name='gestao_comissao'),
    path('registrar_pagamento/', views.registrar_pagamento, name='registrar_pagamento'),
    path('extrato-comissoes-pdf/<int:afiliado_id>/', views.extrato_comissoes_pdf, name='extrato_comissoes_pdf'),
    path('extrato-comissoes-xlsx/<int:afiliado_id>/', views.extrato_comissoes_xlsx, name='extrato_comissoes_xlsx'),
    path('alterar-senha/', views.alterar_senha, name='alterar_senha'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
