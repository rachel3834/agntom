from django import forms
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView
from guardian.mixins import PermissionListMixin
from agntom.forms import LCOImagingTemplateForm
from django.urls import reverse
from django.shortcuts import redirect

class DetailedLCOImagingTemplateCreateView(FormView):
    """
    Displays the form for creating a new observation template. Uses the observation template form specified in the
    respective facility class.
    """
    template_name = 'tom_observations/lco_imaging_template_form.html'

    def get_facility_name(self):
        return 'LCO'

    def get_form_class(self):
        facility_name = self.get_facility_name()

        if not facility_name:
            raise ValueError('Must provide a facility name')

        return LCOImagingTemplateForm

    def get_form(self, form_class=None):
        form = super().get_form()
        form.helper.form_action = reverse('lco-imaging-template-create')
        return form

    def get_initial(self):
        initial = super().get_initial()
        initial['facility'] = self.get_facility_name()
        initial.update(self.request.GET.dict())
        return initial

    def form_valid(self, form):
        form.save()
        return redirect(reverse('tom_observations:template-list'))

class ObservationTemplateUpdateView(LoginRequiredMixin, FormView):
    """
    View for updating an existing observation template.
    """
    template_name = 'tom_observations/observationtemplate_form.html'

    def get_object(self):
        return ObservationTemplate.objects.get(pk=self.kwargs['pk'])

    def get_form_class(self):
        self.object = self.get_object()
        return get_service_class(self.object.facility)().get_template_form(None)

    def get_form(self):
        form = super().get_form()
        form.helper.form_action = reverse(
            'tom_observations:template-update', kwargs={'pk': self.object.id}
        )
        return form

    def get_initial(self):
        initial = super().get_initial()
        initial.update(self.object.parameters)
        initial['facility'] = self.object.facility
        return initial

    def form_valid(self, form):
        form.save(template_id=self.object.id)
        return redirect(reverse('tom_observations:template-list'))