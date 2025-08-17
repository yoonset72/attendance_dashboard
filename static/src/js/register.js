function triggerForgotPassword() {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/employee/register';

    const empInput = document.querySelector('input[name="employee_number"]');
    const empValue = empInput ? empInput.value : '';

    const hiddenEmp = document.createElement('input');
    hiddenEmp.type = 'hidden';
    hiddenEmp.name = 'employee_number';
    hiddenEmp.value = empValue;

    const hiddenForgot = document.createElement('input');
    hiddenForgot.type = 'hidden';
    hiddenForgot.name = 'forgot';
    hiddenForgot.value = '1';

    form.appendChild(hiddenEmp);
    form.appendChild(hiddenForgot);
    document.body.appendChild(form);
    form.submit();
}
