from django.shortcuts import render
from django.views.generic import TemplateView


class AboutView(TemplateView):
    template_name = 'pages/about.html'


class RulesView(TemplateView):
    template_name = 'pages/rules.html'


def page_not_found(request, *args, **kwargs):
    return render(request, 'pages/404.html', status=404)


def csrf_failure(request, *args, **kwargs):
    return render(request, 'pages/403csrf.html', status=403)


def internal_error(request, *args, **kwargs):
    return render(request, 'pages/500.html', status=500)
