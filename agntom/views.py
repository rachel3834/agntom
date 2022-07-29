from django import forms
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView
from guardian.mixins import PermissionListMixin
from agntom.forms import LCOImagingTemplateForm, LCOImagingSequenceTemplateForm
from django.urls import reverse
from django.shortcuts import redirect
from tom_observations.widgets import FilterField
from tom_observations.models import ObservationTemplate

class LCOImagingTemplateCreateView(FormView):
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

class LCOImagingTemplateUpdateView(LoginRequiredMixin, FormView):
    """
    View for updating an existing observation template.
    """
    template_name = 'tom_observations/lco_imaging_template_form.html'

    def get_object(self):
        return ObservationTemplate.objects.get(pk=self.kwargs['pk'])

    def get_form_class(self):
        self.object = self.get_object()
        return LCOImagingTemplateForm

    def get_form(self):
        form = super().get_form()
        form.helper.form_action = reverse(
            'lco-imaging-template-update', kwargs={'pk': self.object.id}
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


class LCOImagingSequenceTemplateCreateView(FormView):
    """
    Displays the form for creating a new observation template. Uses the observation template form specified in the
    respective facility class.
    """
    template_name = 'tom_observations/lco_imaging_sequence_template_form.html'

    def get_facility_name(self):
        return 'LCO'

    def get_form_class(self):
        facility_name = self.get_facility_name()

        if not facility_name:
            raise ValueError('Must provide a facility name')

        return LCOImagingSequenceTemplateForm

    def get_form(self, form_class=None):
        form = super().get_form()
        form.helper.form_action = reverse('lco-imaging-sequence-template-create')
        return form

    def get_initial(self):
        initial = super().get_initial()
        initial['facility'] = self.get_facility_name()
        initial.update(self.request.GET.dict())
        return initial

    def form_valid(self, form):
        form.save()
        return redirect(reverse('tom_observations:template-list'))


class LCOImagingSequenceTemplateUpdateView(LoginRequiredMixin, FormView):
    """
    View for updating an existing observation template.
    """
    template_name = 'tom_observations/lco_imaging_sequence_template_form.html'

    def get_object(self):
        return ObservationTemplate.objects.get(pk=self.kwargs['pk'])

    def get_form_class(self):
        self.object = self.get_object()
        return LCOImagingSequenceTemplateForm

    def get_form(self):
        form = super().get_form()
        form.helper.form_action = reverse(
            'lco-imaging-sequence-template-update', kwargs={'pk': self.object.id}
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
