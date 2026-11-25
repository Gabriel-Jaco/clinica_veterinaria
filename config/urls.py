"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from app.views import *
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView   

urlpatterns = [
    path('admin/', admin.site.urls),
    path('index/', IndexView.as_view(), name="index"),
    path('', RedirectView.as_view(pattern_name='login'), name='home'),
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    
    #path('teste-permissao/', TestePermissaoView.as_view()),


    path('funcionario/', FuncionarioView.as_view(), name='funcionario'),
    path('funcionario/cadastrar/', FuncionarioCreateView.as_view(), name='cadastro_funcionario'),
    path('funcionario/editar/<int:pk>/',FuncionarioEditView.as_view(),name='editar_funcionario'),
    path('funcionario/excluir/<int:pk>/',FuncionarioDeleteView.as_view(),name='excluir_funcionario'),

    path('animal/', AnimalView.as_view(), name='animal'),
    path('animal/cadastrar/', AnimalCreateView.as_view(), name='cadastro_animal'),
    path('animal/editar/<int:pk>/', AnimalEditView.as_view(), name='editar_animal'),
    path('animal/excluir/<int:pk>/', AnimalDeleteView.as_view(), name='excluir_animal'),

    path('raca/', RacaView.as_view(), name='raca'),
    path('raca/cadastrar/', RacaCreateView.as_view(), name='cadastro_raca'),
    path('raca/excluir/<int:pk>/', RacaDeleteView.as_view(), name='excluir_raca'),
        
    path('cliente/', ClienteView.as_view(), name="cliente"),
    path('cliente/cadastrar/', ClienteCreateView.as_view(), name='cadastro_cliente'),
    path('cliente/editar/<int:pk>/', ClienteEditView.as_view(), name='editar_cliente'),
    path('cliente/excluir/<int:pk>/', ClienteDeleteView.as_view(), name='excluir_cliente'),

    
    path('fornecedor/', FornecedorView.as_view(), name='fornecedor'),
    path('fornecedor/cadastrar/', FornecedorCreateView.as_view(), name='cadastro_fornecedor'),
    path('fornecedor/editar/<int:pk>/', FornecedorEditView.as_view(), name='editar_fornecedor'),
    path('fornecedor/excluir/<int:pk>/', FornecedorDeleteView.as_view(), name='excluir_fornecedor'),

    # PRODUTOS
    path('produto/', ProdutoView.as_view(), name='produto'),
    path('produto/cadastrar/', ProdutoCreateView.as_view(), name='cadastro_produto'),
    path('produto/visualizar/<int:pk>/', ProdutoDetailView.as_view(), name='visualizar_produto'),
    path('produto/editar/<int:pk>/', ProdutoEditView.as_view(), name='editar_produto'),
    path('produto/excluir/<int:pk>/', ProdutoDeleteView.as_view(), name='excluir_produto'),

    # LOTES
    path('lote/', LoteView.as_view(), name='lote'),
    path('lote/cadastrar/', LoteCreateView.as_view(), name='cadastro_lote'),
    path('lote/visualizar/<int:pk>/', LoteDetailView.as_view(), name='visualizar_lote'),
    path('lote/editar/<int:pk>/', LoteEditView.as_view(), name='editar_lote'),
    path('lote/excluir/<int:pk>/', LoteDeleteView.as_view(), name='excluir_lote'),

    path('atendimento/', AtendimentoView.as_view(), name='atendimento'),
    path('atendimento/novo/', AtendimentoCreateView.as_view(), name='atendimento_cadastro'),
    path('atendimento/<int:pk>/', AtendimentoDetailView.as_view(), name='atendimento_detalhe'),
    path('atendimento/<int:pk>/editar/', AtendimentoEditView.as_view(), name='atendimento_editar'),
    path('atendimento/<int:pk>/cancelar/', AtendimentoCancelView.as_view(), name='atendimento_cancelar'),

    path('servico/', ServicoView.as_view(), name='servico'),
    path('servico/novo/', ServicoCreateView.as_view(), name='servico_cadastro'),
    path('servico/<int:pk>/editar/', ServicoEditView.as_view(), name='servico_editar'),
    path('servico/<int:pk>/excluir/', ServicoDeleteView.as_view(), name='servico_excluir'),


    path('fatura/', FaturaView.as_view(), name='fatura'),
    path('fatura/nova/', FaturaCreateView.as_view(), name='fatura_cadastro'),
    path('fatura/<int:pk>/', FaturaDetailView.as_view(), name='fatura_detalhe'),
    path('fatura/<int:pk>/excluir/', FaturaDeleteView.as_view(), name='fatura_excluir'),
    path('fatura/<int:pk>/pagar/', PagamentoCreateView.as_view(), name='pagamento_cadastro'),
    path('pagamento/<int:pk>/estornar/', PagamentoEstornarView.as_view(), name='pagamento_estornar'),

    
]
