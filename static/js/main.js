// Show/hide registration fields based on role selection
document.addEventListener('DOMContentLoaded', function () {

    const roleIndustry    = document.getElementById('role_industry');
    const roleParticipant = document.getElementById('role_participant');
    const industryFields  = document.getElementById('industry-fields');
    const participantFields = document.getElementById('participant-fields');

    function updateFields() {
        if (roleIndustry && roleIndustry.checked) {
            if (industryFields)    industryFields.style.display    = 'block';
            if (participantFields) participantFields.style.display = 'none';
        } else if (roleParticipant && roleParticipant.checked) {
            if (industryFields)    industryFields.style.display    = 'none';
            if (participantFields) participantFields.style.display = 'block';
        }
    }

    if (roleIndustry)    roleIndustry.addEventListener('change',    updateFields);
    if (roleParticipant) roleParticipant.addEventListener('change', updateFields);

    // Auto-select role from URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const role = urlParams.get('role');
    if (role === 'industry' && roleIndustry) {
        roleIndustry.checked = true;
        updateFields();
    } else if (role === 'participant' && roleParticipant) {
        roleParticipant.checked = true;
        updateFields();
    }

    // Auto-dismiss flash messages after 5 seconds
    setTimeout(function () {
        document.querySelectorAll('.alert').forEach(function (el) {
            el.style.opacity = '0';
            el.style.transition = 'opacity 0.5s';
            setTimeout(() => el.remove(), 500);
        });
    }, 5000);
});