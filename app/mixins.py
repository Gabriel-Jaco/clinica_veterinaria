from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect

class PermissaoComRedirecionamentoMixin(LoginRequiredMixin, PermissionRequiredMixin):

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "Ação não permitida!")
            return redirect('index')

        return super().handle_no_permission()