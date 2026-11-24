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

    
]
