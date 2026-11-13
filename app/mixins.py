from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class GrupoRequeridoMixin(LoginRequiredMixin, UserPassesTestMixin):
    grupos_permitidos = []

    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        return user.groups.filter(name__in=self.grupos_permitidos).exists()