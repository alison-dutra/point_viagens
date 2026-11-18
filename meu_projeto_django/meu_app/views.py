from django.shortcuts import render, redirect, get_object_or_404
from django.db.models.deletion import ProtectedError
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from .forms import ProdutoForm
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Afiliado, Venda, Cliente, Produto
import uuid
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib.auth.models import User
import random
import string
import threading
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from .models import Afiliado, Venda, Cliente, Produto, ComissaoPagamento
from decimal import Decimal, InvalidOperation
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from .models import Afiliado, Venda, Cliente, Produto, ComissaoPagamento, AfiliadoDocumento

AFFILIATE_LOGIN = {
    'login': {
        'label': 'Login',
        'template': 'meu_app/affiliate_tabs/login.html',
    },
}

AFFILIATE_TAB_ORDER_LOGIN = [
    'login',
]

AFFILIATE_TABS = {
    'login': {
        'label': 'Login',
        'template': 'meu_app/affiliate_tabs/login.html',
    },
    'nova-venda': {
        'label': 'Nova Venda',
        'template': 'meu_app/affiliate_tabs/nova_venda.html',
    },
    'minhas-vendas': {
        'label': 'Minhas Vendas',
        'template': 'meu_app/affiliate_tabs/minhas_vendas.html',
    },
    'meu-perfil': {
        'label': 'Meu Perfil',
        'template': 'meu_app/affiliate_tabs/meu_perfil.html',
    },
    'produtos': {
        'label': 'Produtos',
        'template': 'meu_app/affiliate_tabs/produtos.html',
    },
    'meus-clientes': {
        'label': 'Meus Clientes',
        'template': 'meu_app/affiliate_tabs/meus_clientes.html',
    },
    'consultar-vendas': {
        'label': 'Consultar Vendas',
        'template': 'meu_app/affiliate_tabs/consultar_vendas_admin.html',
    },
    'meus-afiliados': {
        'label': 'Meus Afiliados',
        'template': 'meu_app/affiliate_tabs/meus_afiliados.html',
    },
    'gestao-comissao': {
        'label': 'Gestao Comissao',
        'template': 'meu_app/affiliate_tabs/gestao_comissao.html',
    },
}

AFFILIATE_TAB_ORDER = [
    'nova-venda',
    'minhas-vendas',
    'meu-perfil',
]


def _get_tab_slug(tab_slug):
    return tab_slug if tab_slug in AFFILIATE_TABS else 'nova-venda'


def _is_passagem_aerea(produto):
    return produto.is_passagem_aerea


def home(request):
    return render(request, 'meu_app/index.html')


def area_do_afiliado(request, tab_slug='login'):
    # Se já está logado, manda direto pra área logada
    if request.user.is_authenticated:
        return redirect('area_do_afiliado_logado')

    if request.method == 'POST':
        from django.contrib.auth.forms import AuthenticationForm
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('area_do_afiliado_logado')
    else:
        from django.contrib.auth.forms import AuthenticationForm
        form = AuthenticationForm()

    context = {
        'active_tab': 'login',
        'affiliate_tabs': [(slug, AFFILIATE_LOGIN[slug]) for slug in AFFILIATE_TAB_ORDER_LOGIN],
        'form': form,
    }

    return render(request, 'meu_app/index_area_do_afiliado.html', context)


def logout_view(request):
    logout(request)
    return redirect('/area-do-afiliado/')


@login_required(login_url='/area-do-afiliado/')
def area_do_afiliado_logado(request, tab_slug='nova-venda', produto_id=None):
    tab_slug = _get_tab_slug(tab_slug)
    tab_data = AFFILIATE_TABS[tab_slug]

    if tab_slug == 'produtos' and not request.user.is_superuser:
        return HttpResponseForbidden('Acesso permitido apenas ao administrador.')

    produto_editando = None
    if tab_slug == 'produtos' and produto_id is not None:
        produto_editando = get_object_or_404(Produto, pk=produto_id)
    produto_form = ProdutoForm(instance=produto_editando)
    if tab_slug == 'produtos' and request.method == 'POST':
        produto_form = ProdutoForm(request.POST, instance=produto_editando)
        if produto_form.is_valid():
            produto_form.save()
            messages.success(request, 'Produto atualizado com sucesso!' if produto_editando else 'Produto cadastrado com sucesso!')
            return redirect('produtos')

    if request.user.is_superuser:
        tabs_visiveis = ['nova-venda', 'minhas-vendas', 'meu-perfil', 'consultar-vendas', 'meus-afiliados', 'gestao-comissao', 'meus-clientes', 'produtos']
    elif request.user.groups.filter(name='funcionario').exists():
        tabs_visiveis = ['nova-venda', 'minhas-vendas', 'meu-perfil', 'consultar-vendas', 'meus-clientes']
    else:
        tabs_visiveis = ['nova-venda', 'minhas-vendas', 'meu-perfil']

    afiliado_logado = None
    try:
        username_limpo = request.user.username
        afiliado_logado = next(
            (a for a in Afiliado.objects.all() 
            if a.cpf.replace('.','').replace('-','') == username_limpo),
            None
        )
        afiliado_logado_cpf = afiliado_logado.cpf if afiliado_logado else ''

        if afiliado_logado:
            vendas_afiliado = Venda.objects.filter(afiliado=afiliado_logado)
            vendas_aprovadas = vendas_afiliado.filter(status_venda='aprovado')
            total_comissao = sum((v.comissao_valor for v in vendas_aprovadas.select_related('produto', 'afiliado')), Decimal('0.00'))
            pagamentos = ComissaoPagamento.objects.filter(afiliado=afiliado_logado).order_by('-data_pagamento')
            total_pago = sum(p.valor for p in pagamentos)
            total_a_receber = max(Decimal('0'), total_comissao - total_pago)

            perfil_dados = {
                'id': afiliado_logado.id,
                'nome': afiliado_logado.nome_afiliado,
                'email': afiliado_logado.email,
                'cpf': afiliado_logado.cpf,
                'total_realizadas': vendas_afiliado.count(),
                'total_aprovadas': vendas_afiliado.filter(status_venda='aprovado').count(),
                'total_reprovadas': vendas_afiliado.filter(status_venda='reprovado').count(),
                'total_pendentes': vendas_afiliado.filter(status_venda='pendente').count(),
                'total_comissao': total_a_receber,
                'total_comissoes_pagas': total_pago,
                'comissoes_pagas': pagamentos,
            }
        else:
            perfil_dados = {}
    except:
        afiliado_logado_cpf = ''
        perfil_dados = {}

    vendas = Venda.objects.select_related('cliente', 'afiliado', 'produto').all()
    if request.user.is_superuser:
        vendas_minhas = vendas.filter(criado_por=request.user)
    else:
        vendas_minhas = vendas.filter(afiliado=afiliado_logado) if afiliado_logado else vendas.none()
    
    context = {
        'active_tab': tab_slug,
        'affiliate_tabs': [(slug, AFFILIATE_TABS[slug]) for slug in tabs_visiveis],
        'vendas': vendas,
        'minhas_vendas': vendas_minhas,
        'afiliados': Afiliado.objects.prefetch_related('documentos').all(),
        'clientes': Cliente.objects.all(),
        'produtos': Produto.objects.all().order_by('-data_cadastro', '-id'),
        'produto_form': produto_form,
        'produto_editando': produto_editando,
        'afiliado_logado_cpf': afiliado_logado_cpf,
        'afiliado_comissao': afiliado_logado.comissao if afiliado_logado else None,
        'perfil_dados': perfil_dados,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, tab_data['template'], context)

    return render(request, 'meu_app/index_area_do_afiliado_logado.html', context)


def cadastro_afiliado(request):
    return render(request, 'meu_app/form_afiliado.html')


@csrf_exempt
def salvar_afiliado(request):
    if request.method == "POST":
        try:
            afiliado = Afiliado.objects.create(
                nome_afiliado=request.POST.get('nome_afiliado'),
                cpf=request.POST.get('cpf'),
                rg=request.POST.get('rg'),
                endereco=request.POST.get('endereco'),
                celular=request.POST.get('celular'),
                email=request.POST.get('email'),
            )

            # Salva cada arquivo na tabela de documentos
            arquivos = request.FILES.getlist('documento_foto')
            for arquivo in arquivos:
                AfiliadoDocumento.objects.create(
                    afiliado=afiliado,
                    arquivo=arquivo
                )

            return JsonResponse({'success': True, 'message': 'Afiliado cadastrado com sucesso!', 'id': afiliado.id})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erro: {str(e)}'}, status=400)
    return JsonResponse({'success': False}, status=405)


@csrf_exempt
def alterar_afiliado(request, afiliado_id):
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Acesso permitido apenas ao administrador.'}, status=403)
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            afiliado = Afiliado.objects.get(id=afiliado_id)
            
            status_anterior = afiliado.status
            novo_status = data.get('status', afiliado.status)

            afiliado.nome_afiliado = data.get('nome_afiliado', afiliado.nome_afiliado)
            afiliado.cpf           = data.get('cpf', afiliado.cpf)
            afiliado.rg            = data.get('rg', afiliado.rg)
            afiliado.endereco      = data.get('endereco', afiliado.endereco)
            afiliado.celular       = data.get('celular', afiliado.celular)
            afiliado.email         = data.get('email', afiliado.email)
            if 'comissao' in data:
                percentual = data.get('comissao')
                if percentual in (None, ''):
                    afiliado.comissao = None
                else:
                    afiliado.comissao = Decimal(str(percentual).replace(',', '.'))
                    if afiliado.comissao < 0 or afiliado.comissao > 100:
                        return JsonResponse({'success': False, 'message': 'A comissão deve ficar entre 0% e 100%.'}, status=400)
            afiliado.status        = novo_status
            afiliado.save()

            if status_anterior != 'aprovado' and novo_status == 'aprovado':
                username = afiliado.cpf.replace('.', '').replace('-', '')
                senha = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

                if not User.objects.filter(username=username).exists():
                    User.objects.create_user(
                        username=username,
                        password=senha,
                        email=afiliado.email,
                        first_name=afiliado.nome_afiliado
                    )

                    # Envia email em background
                    def enviar_email():
                        send_mail(
                            subject='Seu cadastro foi aprovado! 🎉',
                            message=f'''Olá, {afiliado.nome_afiliado}!

Seu cadastro como afiliado foi aprovado. Aqui estão suas credenciais de acesso:

Usuário: {username}
Senha: {senha}

Acesse: http://127.0.0.1:8000/area-do-afiliado/

Att,
Equipe Point Viagens''',
                            from_email='alison.dutra58@gmail.com',
                            recipient_list=[afiliado.email],
                            fail_silently=True,
                        )

                    threading.Thread(target=enviar_email).start()

            return JsonResponse({'success': True})

        except Afiliado.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Afiliado não encontrado.'}, status=404)
        except Exception as e:
            print("ERRO:", str(e))
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False}, status=405)

@login_required(login_url='/area-do-afiliado/')
@require_POST
def remover_afiliado(request, afiliado_id):
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Acesso permitido apenas ao administrador.'}, status=403)
    afiliado = get_object_or_404(Afiliado, pk=afiliado_id)
    try:
        afiliado.delete()
    except ProtectedError:
        return JsonResponse({'success': False, 'message': 'NÃ£o Ã© possÃ­vel excluir este afiliado porque hÃ¡ vendas ou pagamentos vinculados.'}, status=400)
    return JsonResponse({'success': True})


@csrf_exempt
@login_required(login_url='/area-do-afiliado/')
def alterar_senha(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            senha_atual = data.get('senha_atual')
            senha_nova  = data.get('senha_nova')

            if not request.user.check_password(senha_atual):
                return JsonResponse({'success': False, 'message': 'Senha atual incorreta.'})

            request.user.set_password(senha_nova)
            request.user.save()

            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False}, status=405)

@login_required(login_url='/area-do-afiliado/')
@csrf_exempt
def nova_venda(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            if data.get('verificar_cpf'):
                cpf = data.get('cliente_id')
                existe = Cliente.objects.filter(cpf=cpf).exists()
                return JsonResponse({'success': existe})

            if data.get('buscar_cliente'):
                cpf = data.get('cliente_id')
                try:
                    cliente = Cliente.objects.get(cpf=cpf)
                    return JsonResponse({
                        'success': True,
                        'nome': cliente.nome,
                        'celular': cliente.celular,
                        'email': cliente.email,
                    })
                except Cliente.DoesNotExist:
                    return JsonResponse({'success': False})

            cpf_cliente = (data.get('cliente_id') or '').strip()
            if not cpf_cliente:
                if not request.user.is_superuser:
                    return JsonResponse({'success': False, 'message': 'O CPF do cliente é obrigatório.'}, status=400)
                cliente = Cliente.objects.create(
                    nome='Cliente sem CPF',
                    cpf='',
                    nascimento='',
                    celular='',
                    email='',
                )
            else:
                cliente = Cliente.objects.get(cpf=cpf_cliente)

            # O formulário envia afiliado_cpf vazio para usuários admin; nesse
            # caso use o CPF de afiliado padrão configurado para vendas admin.
            cpf_afiliado = (data.get('afiliado_cpf') or '240.035.058-24').strip()
            afiliado = Afiliado.objects.get(cpf=cpf_afiliado)

            codigo = (data.get('codigo_venda') or '').strip().lstrip('#').upper()

            if not codigo:
                return JsonResponse({'success': False, 'message': 'Informe o código da venda.'}, status=400)

            if Venda.objects.filter(codigo_venda=codigo).exists():
                return JsonResponse({'success': False, 'message': 'Já existe uma venda com esse código.'}, status=400)

            produto = Produto.objects.get(pk=data.get('produto_id'))
            data_hora_ida = None
            data_hora_volta = None
            localizador_reserva = None
            if _is_passagem_aerea(produto):
                data_hora_ida = parse_datetime((data.get('data_hora_ida') or '').strip())
                data_hora_volta = parse_datetime((data.get('data_hora_volta') or '').strip())
                localizador_reserva = (data.get('localizador_reserva') or '').strip()
                if not data_hora_ida or not data_hora_volta or not localizador_reserva:
                    return JsonResponse({'success': False, 'message': 'Informe ida, volta e localizador da reserva para passagem aÃ©rea.'}, status=400)
                if not localizador_reserva.isascii() or not localizador_reserva.isalnum():
                    return JsonResponse({'success': False, 'message': 'O localizador deve conter apenas letras e nÃºmeros.'}, status=400)
                if timezone.is_naive(data_hora_ida):
                    data_hora_ida = timezone.make_aware(data_hora_ida, timezone.get_current_timezone())
                if timezone.is_naive(data_hora_volta):
                    data_hora_volta = timezone.make_aware(data_hora_volta, timezone.get_current_timezone())

            venda = Venda.objects.create(
                codigo_venda=codigo,
                cliente=cliente,
                afiliado=afiliado,
                produto=produto,
                descricao_venda=data.get('descricao_venda'),
                tipo_venda=data.get('tipo_venda'),
                valor=data.get('valor'),
                data_hora_ida=data_hora_ida,
                data_hora_volta=data_hora_volta,
                localizador_reserva=localizador_reserva,
                status_venda='pendente',
                criado_por=request.user
            )
            return JsonResponse({'success': True, 'id': venda.id})

        except Cliente.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Cliente não encontrado com este CPF.'}, status=404)
        except Afiliado.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Afiliado não encontrado com este CPF.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    return redirect('area_do_afiliado_logado')


@login_required(login_url='/area-do-afiliado/')
def minhas_vendas(request):
    username_limpo = request.user.username
    afiliado = next(
        (a for a in Afiliado.objects.all() if a.cpf.replace('.', '').replace('-', '') == username_limpo),
        None,
    )
    vendas = Venda.objects.select_related('cliente', 'afiliado', 'produto')
    vendas = vendas.filter(criado_por=request.user) if request.user.is_superuser else (vendas.filter(afiliado=afiliado) if afiliado else vendas.none())
    return render(request, 'meu_app/affiliate_tabs/minhas_vendas.html', {
        'vendas': vendas,
        'minhas_vendas': vendas,
        'produtos': Produto.objects.all(),
    })


@csrf_exempt
def alterar_venda(request, venda_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            venda = Venda.objects.get(id=venda_id)

            if 'status_venda' in data and not request.user.is_superuser:
                return JsonResponse({'success': False, 'message': 'Apenas o administrador pode aprovar ou reprovar vendas.'}, status=403)
            
            
            if 'codigo_venda' in data:
                codigo = (data.get('codigo_venda') or '').strip().lstrip('#').upper()
                if not codigo:
                    return JsonResponse({'success': False, 'message': 'O código da venda não pode ser vazio.'}, status=400)
                if Venda.objects.filter(codigo_venda=codigo).exclude(id=venda.id).exists():
                    return JsonResponse({'success': False, 'message': 'Já existe outra venda com esse código.'}, status=400)
                venda.codigo_venda = codigo

            venda.produto_id = data.get('produto_id', venda.produto_id)
            venda.descricao_venda = data.get('descricao_venda', venda.descricao_venda)
            venda.tipo_venda = data.get('tipo_venda', venda.tipo_venda)

            valor = data.get('valor', venda.valor)
            if isinstance(valor, str):
                valor = valor.strip()
                if ',' in valor:  # formato brasileiro: 1.234,56
                    valor = valor.replace('.', '').replace(',', '.')
            try:
                venda.valor = Decimal(str(valor))
            except InvalidOperation:
                return JsonResponse({'success': False, 'message': 'Valor da venda inválido.'}, status=400)
            if 'comissao_personalizada' in data:
                if not request.user.is_superuser:
                    return JsonResponse({'success': False, 'message': 'Apenas o administrador pode alterar a comissão da venda.'}, status=403)
                percentual = data.get('comissao_personalizada')
                if percentual in (None, ''):
                    venda.comissao_personalizada = None
                else:
                    try:
                        percentual = Decimal(str(percentual).replace(',', '.'))
                    except InvalidOperation:
                        return JsonResponse({'success': False, 'message': 'Percentual de comissão inválido.'}, status=400)
                    if percentual < 0 or percentual > 100:
                        return JsonResponse({'success': False, 'message': 'A comissão deve ficar entre 0% e 100%.'}, status=400)
                    venda.comissao_personalizada = percentual
            venda.status_venda    = data.get('status_venda', venda.status_venda)
            venda.save()
            return JsonResponse({
                'success': True,
                'comissao_personalizada': str(venda.comissao_personalizada) if venda.comissao_personalizada is not None else '',
                'comissao_percentual': str(venda.comissao_percentual),
                'comissao_valor': str(venda.comissao_valor),
            })
        except Venda.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Venda não encontrada.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False}, status=405)


@csrf_exempt
def salvar_cliente(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            cliente = Cliente.objects.create(
                nome=data.get('nome'),
                cpf=data.get('cpf'),
                nascimento=data.get('nascimento'),
                celular=data.get('celular'),
                email=data.get('email')
            )
            return JsonResponse({'success': True, 'id': cliente.id})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False}, status=405)

@csrf_exempt
def gestao_comissao(request):
    afiliados = Afiliado.objects.filter(
        venda__status_venda='aprovado'
    ).distinct()

    dados = []

    for afiliado in afiliados:
        vendas_aprovadas = Venda.objects.filter(afiliado=afiliado, status_venda='aprovado')
        total_vendas = sum(v.valor for v in vendas_aprovadas)
        total_comissao = sum((v.comissao_valor for v in vendas_aprovadas.select_related('produto', 'afiliado')), Decimal('0.00'))
        pagamentos = ComissaoPagamento.objects.filter(afiliado=afiliado)
        total_pago = sum(p.valor for p in pagamentos)
        total_receber = max(Decimal('0'), total_comissao - total_pago)

        dados.append({
            'afiliado': afiliado,
            'total_vendas': total_vendas,
            'total_comissao': total_comissao,
            'total_pago': total_pago,
            'total_receber': total_receber,
        })

    return JsonResponse({'dados': [
        {
            'id': d['afiliado'].id,
            'nome': d['afiliado'].nome_afiliado,
            'total_vendas': float(d['total_vendas']),
            'total_comissao': float(d['total_comissao']),
            'total_pago': float(d['total_pago']),
            'total_receber': float(d['total_receber']),
        } for d in dados
    ]})


@csrf_exempt
def registrar_pagamento(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            afiliado = Afiliado.objects.get(id=data.get('afiliado_id'))

            pagamento = ComissaoPagamento.objects.create(
                afiliado=afiliado,
                valor=data.get('valor'),
                data_pagamento=data.get('data_pagamento'),
                descricao=data.get('descricao', '')
            )

            # Envia email em background
            def enviar_email():
                send_mail(
                    subject='Pagamento de comissão registrado! 💰',
                    message=f'''Olá, {afiliado.nome_afiliado}!

Um pagamento de comissão foi registrado para você:

Valor: R$ {pagamento.valor}
Data: {pagamento.data_pagamento}
Descrição: {pagamento.descricao or 'Sem descrição'}

Acesse sua área para mais detalhes.

Att,
Equipe Point Viagens''',
                    from_email='alison.dutra58@gmail.com',
                    recipient_list=[afiliado.email],
                    fail_silently=True,
                )
            threading.Thread(target=enviar_email).start()

            return JsonResponse({'success': True, 'id': pagamento.id})

        except Afiliado.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Afiliado não encontrado.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    return JsonResponse({'success': False}, status=405)

def extrato_comissoes_pdf(request, afiliado_id):
    afiliado = Afiliado.objects.get(id=afiliado_id)
    pagamentos = ComissaoPagamento.objects.filter(afiliado=afiliado).order_by('-data_pagamento')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="extrato_comissoes_{afiliado.cpf}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Título
    story.append(Paragraph(f"Extrato de Comissões — {afiliado.nome_afiliado}", styles['Title']))
    story.append(Paragraph(f"CPF: {afiliado.cpf} | Email: {afiliado.email}", styles['Normal']))
    story.append(Spacer(1, 20))

    # Tabela
    data = [['Data', 'Descrição', 'Valor']]
    total = Decimal('0')
    for p in pagamentos:
        data.append([
            p.data_pagamento.strftime('%d/%m/%Y'),
            p.descricao or '—',
            f"R$ {p.valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        ])
        total += p.valor

    data.append(['', 'TOTAL', f"R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')])

    table = Table(data, colWidths=[100, 280, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0a2342')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dafbe1')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    doc.build(story)
    return response


def extrato_comissoes_xlsx(request, afiliado_id):
    afiliado = Afiliado.objects.get(id=afiliado_id)
    pagamentos = ComissaoPagamento.objects.filter(afiliado=afiliado).order_by('-data_pagamento')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Extrato de Comissões"

    # Cabeçalho info
    ws['A1'] = f"Extrato de Comissões — {afiliado.nome_afiliado}"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A2'] = f"CPF: {afiliado.cpf} | Email: {afiliado.email}"
    ws.append([])

    # Header tabela
    headers = ['Data', 'Descrição', 'Valor (R$)']
    ws.append(headers)
    header_row = ws.max_row
    for col in range(1, 4):
        cell = ws.cell(row=header_row, column=col)
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(fill_type='solid', fgColor='0a2342')
        cell.alignment = Alignment(horizontal='center')

    # Dados
    total = Decimal('0')
    for p in pagamentos:
        ws.append([
            p.data_pagamento.strftime('%d/%m/%Y'),
            p.descricao or '—',
            float(p.valor)
        ])
        total += p.valor

    # Total
    ws.append(['', 'TOTAL', float(total)])
    total_row = ws.max_row
    for col in range(1, 4):
        cell = ws.cell(row=total_row, column=col)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(fill_type='solid', fgColor='dafbe1')

    # Largura colunas
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 40
    ws.column_dimensions['C'].width = 15

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="extrato_comissoes_{afiliado.cpf}.xlsx"'
    wb.save(response)
    return response



@login_required(login_url='/area-do-afiliado/')
@require_POST
def remover_produto(request, produto_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden('Acesso permitido apenas ao administrador.')
    produto = get_object_or_404(Produto, pk=produto_id)
    try:
        produto.delete()
    except ProtectedError:
        messages.error(request, 'Não é possível remover este produto porque ele está vinculado a vendas.')
    else:
        messages.success(request, 'Produto removido com sucesso!')
    return redirect('produtos')
