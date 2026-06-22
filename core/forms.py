from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import CustomUser, Ticket, TicketAttachment, TicketComment, UserRole, Device, KnowledgeBaseArticle, Material, MaterialRequest


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': field.label,
            })
            if field.label:
                field.label = field.label.capitalize()

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['name', 'description', 'unit', 'stock_quantity', 'min_stock_level']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

class MaterialRequestForm(forms.ModelForm):
    class Meta:
        model = MaterialRequest
        fields = ['material', 'quantity', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Why do you need these materials?'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['material'].queryset = Material.objects.filter(stock_quantity__gt=0)
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})


class KnowledgeBaseForm(forms.ModelForm):
    class Meta:
        model = KnowledgeBaseArticle
        fields = ['title', 'category', 'content', 'is_published']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10, 'placeholder': 'Write the solution steps here...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Your email address'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            if field.label:
                field.label = field.label.capitalize()


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = [
            'title', 'description', 'priority', 'category', 'ai_suggested_category',
            'wing', 'floor', 'room_number', 'device', 'device_serial_number'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'title': forms.TextInput(attrs={'placeholder': 'Brief summary of the issue'}),
            'category': forms.TextInput(attrs={'placeholder': 'e.g. Network, Hardware, Software'}),
            'ai_suggested_category': forms.HiddenInput(),
            'wing': forms.Select(attrs={'class': 'form-select'}),
            'floor': forms.Select(attrs={'class': 'form-select'}),
            'device': forms.Select(attrs={'class': 'form-select'}),
            'room_number': forms.TextInput(attrs={'placeholder': 'Room number'}),
            'device_serial_number': forms.TextInput(attrs={'placeholder': 'Manual override (optional if device selected)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'device' in self.fields:
            self.fields['device'].queryset = Device.objects.all().order_by('serial_number')

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            if field.label:
                field.label = field.label.capitalize()


class TicketUpdateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'priority', 'category', 'wing', 'floor', 'room_number', 'device', 'device_serial_number', 'status', 'assigned_to']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'title': forms.TextInput(attrs={'placeholder': 'Brief summary of the issue'}),
            'category': forms.TextInput(attrs={'placeholder': 'e.g. Network, Hardware, Software'}),
            'wing': forms.Select(attrs={'class': 'form-select'}),
            'floor': forms.Select(attrs={'class': 'form-select'}),
            'device': forms.Select(attrs={'class': 'form-select'}),
            'room_number': forms.TextInput(attrs={'placeholder': 'Room number'}),
            'device_serial_number': forms.TextInput(attrs={'placeholder': 'Manual override (optional if device selected)'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if 'device' in self.fields:
            self.fields['device'].queryset = Device.objects.all().order_by('serial_number')

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            if field.label:
                field.label = field.label.capitalize()

        # Limit assigned_to choices to users with Technician role
        if 'assigned_to' in self.fields:
            self.fields['assigned_to'].queryset = CustomUser.objects.filter(role=UserRole.TECHNICIAN)

        # Allow admins and technicians to assign; hide field for other users
        if user and not (user.is_admin or user.is_technician):
            self.fields['assigned_to'].widget = forms.HiddenInput()
            self.fields['assigned_to'].required = False

        # Only admins and technicians should see/change status
        if user and not (user.is_admin or user.is_technician):
            self.fields.pop('status', None)


class UserRoleForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['role', 'is_active']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            if field.label:
                field.label = field.label.capitalize()


class TicketCommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Add an update or note about this ticket.'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            if field.label:
                field.label = field.label.capitalize()


class TicketAttachmentForm(forms.ModelForm):
    class Meta:
        model = TicketAttachment
        fields = ['file', 'description']
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'Optional description for the file'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'file':
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
            if field.label:
                field.label = field.label.capitalize()


class TicketReopenForm(forms.Form):
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Optional reason for reopening the ticket',
            'class': 'form-control',
        }),
        label='Reopen reason',
    )


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = [
            'device_type', 'other_device_type', 'assigned_user', 'serial_number', 'name', 'wing', 'floor', 'room_number',
            'status', 'condition', 'last_inspected', 'next_inspection', 'notes'
        ]
        widgets = {
            'serial_number': forms.TextInput(attrs={'placeholder': 'Enter unique serial number or asset tag'}),
            'other_device_type': forms.TextInput(attrs={'placeholder': 'Specify type if Other'}),
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Dell Latitude 5420'}),
            'room_number': forms.TextInput(attrs={'placeholder': 'e.g. 102'}),
            'last_inspected': forms.DateInput(attrs={'type': 'date'}),
            'next_inspection': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional notes about device history'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            if field.label:
                field.label = field.label.capitalize()
